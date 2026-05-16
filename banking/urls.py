from django.urls import path
from . import views

urlpatterns = [
    path('balance/', views.BalanceView.as_view(), name='balance'),
    path('transfer/', views.TransferView.as_view(), name='transfer'),
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('transactions/', views.TransactionListView.as_view(), name='transactions'),
    path('validate-account/<str:account_number>/', views.ValidateAccountView.as_view(), name='validate-account'),
]
