from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer, ChangePinSerializer
from .utils import send_otp_email, verify_otp_code


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_otp_email(user)
            except Exception as e:
                # Don't fail registration if email fails; log it
                print(f"[OTP EMAIL ERROR] {e}")
            return Response(
                {'message': 'Account created! Check your email for the OTP.'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')

        if not email or not otp_code:
            return Response({'message': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'message': 'Account already verified.'}, status=status.HTTP_200_OK)

        valid, message = verify_otp_code(user, otp_code)
        if not valid:
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.save()
        return Response({'message': 'Email verified successfully! You can now log in.'}, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'message': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'message': 'Account already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_otp_email(user)
            return Response({'message': 'OTP resent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'Failed to send OTP. Try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        pin = request.data.get('pin', '')

        if not email or not password or not pin:
            return Response({'message': 'Email, password and PIN are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'message': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({'message': 'Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)

        if not check_password(pin, user.pin):
            return Response({'message': 'Invalid PIN.'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens(user)
        return Response({
            **tokens,
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        if not check_password(data['old_pin'], user.pin):
            return Response({'message': 'Current PIN is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.pin = make_password(data['new_pin'])
        user.save()
        return Response({'message': 'PIN changed successfully.'}, status=status.HTTP_200_OK)
