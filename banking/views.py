import random
import string
from django.db import transaction as db_transaction
from django.contrib.auth.hashers import check_password
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from .models import BankAccount, Transaction
from .serializers import TransactionSerializer, BalanceSerializer, TransferSerializer, WithdrawSerializer, DepositSerializer
from .utils import send_transaction_email


def generate_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def get_or_create_account(user):
    account, _ = BankAccount.objects.get_or_create(user=user)
    return account


class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = get_or_create_account(request.user)
        return Response({'balance': str(account.balance)})


class ValidateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_number):
        try:
            user = User.objects.get(account_number=account_number, is_verified=True)
            if user == request.user:
                return Response({'message': 'Cannot transfer to your own account.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'full_name': user.full_name, 'account_number': user.account_number})
        except User.DoesNotExist:
            return Response({'message': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        if not check_password(data['pin'], user.pin):
            return Response({'message': 'Incorrect PIN.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            recipient = User.objects.get(account_number=data['to_account'], is_verified=True)
        except User.DoesNotExist:
            return Response({'message': 'Recipient account not found.'}, status=status.HTTP_404_NOT_FOUND)

        if recipient == user:
            return Response({'message': 'Cannot transfer to your own account.'}, status=status.HTTP_400_BAD_REQUEST)

        sender_account = get_or_create_account(user)
        recipient_account = get_or_create_account(recipient)
        amount = data['amount']

        if sender_account.balance < amount:
            return Response({'message': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        ref = generate_reference()
        desc = data.get('description', '') or f'Transfer to {recipient.full_name}'

        with db_transaction.atomic():
            sender_account.balance -= amount
            sender_account.save()
            recipient_account.balance += amount
            recipient_account.save()

            Transaction.objects.create(
                account=sender_account, transaction_type='transfer',
                amount=amount, description=desc,
                reference_id=ref, related_account=recipient_account, status='success',
            )
            Transaction.objects.create(
                account=recipient_account, transaction_type='credit',
                amount=amount, description=f'Transfer from {user.full_name}',
                reference_id=ref, related_account=sender_account, status='success',
            )

        # Send emails to both parties
        send_transaction_email(
            user=user, transaction_type='transfer_debit',
            amount=amount, balance_after=sender_account.balance,
            reference_id=ref, recipient_name=recipient.full_name,
        )
        send_transaction_email(
            user=recipient, transaction_type='transfer_credit',
            amount=amount, balance_after=recipient_account.balance,
            reference_id=ref, sender_name=user.full_name,
        )

        return Response({
            'message': f'Rs.{amount} transferred successfully to {recipient.full_name}.',
            'reference_id': ref,
            'new_balance': str(sender_account.balance),
        }, status=status.HTTP_200_OK)


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        if not check_password(data['pin'], user.pin):
            return Response({'message': 'Incorrect PIN.'}, status=status.HTTP_401_UNAUTHORIZED)

        account = get_or_create_account(user)
        amount = data['amount']

        if account.balance < amount:
            return Response({'message': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        ref = generate_reference()

        with db_transaction.atomic():
            account.balance -= amount
            account.save()
            Transaction.objects.create(
                account=account, transaction_type='withdrawal',
                amount=amount, description='Cash Withdrawal',
                reference_id=ref, status='success',
            )

        # Send email notification
        send_transaction_email(
            user=user, transaction_type='withdrawal',
            amount=amount, balance_after=account.balance,
            reference_id=ref,
        )

        return Response({
            'message': f'Rs.{amount} withdrawn successfully.',
            'reference_id': ref,
            'new_balance': str(account.balance),
        }, status=status.HTTP_200_OK)


class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        # Verify PIN
        if not check_password(data['pin'], user.pin):
            return Response({'message': 'Incorrect PIN.'}, status=status.HTTP_401_UNAUTHORIZED)

        account = get_or_create_account(user)
        amount = data['amount']
        source = data.get('source', 'Cash Deposit')
        ref = generate_reference()

        with db_transaction.atomic():
            account.balance += amount
            account.save()
            Transaction.objects.create(
                account=account,
                transaction_type='credit',
                amount=amount,
                description=f'Deposit - {source}',
                reference_id=ref,
                status='success',
            )

        # Send email notification
        send_transaction_email(
            user=user,
            transaction_type='deposit',
            amount=amount,
            balance_after=account.balance,
            reference_id=ref,
            source=source,
        )

        return Response({
            'message': f'Rs.{amount} deposited successfully.',
            'reference_id': ref,
            'new_balance': str(account.balance),
        }, status=status.HTTP_200_OK)


class TransactionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        account = get_or_create_account(self.request.user)
        qs = Transaction.objects.filter(account=account)
        tx_type = self.request.query_params.get('type')
        if tx_type and tx_type != 'all':
            qs = qs.filter(transaction_type=tx_type)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(description__icontains=search)
        return qs
