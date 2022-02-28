from django.urls import path

from . import views
from token_exchange.views import getLinkToken,getAccessToken,getAccounts,getTransactions,getItems

urlpatterns = [
    # all POST API calls
    path('link_token/', getLinkToken.as_view(), name='Get-Plaid-Link_Token'),
    path('get_access_token/', getAccessToken.as_view(), name='Plaid-Link-Public_token'),
    
    # all GET API calls
    path('home/', views.home, name='Get-Public_token'),
    path('get_items/', getItems.as_view(), name='Get-Items'),
    path('get_accounts/', getAccounts.as_view(), name='Get-Accounts'),
    path('get_transactions/', getTransactions.as_view(), name='Get-Transactions'),
    path('transaction_webhook/', views.transactionWebhook, name='Transaction-Webhook'),
]
