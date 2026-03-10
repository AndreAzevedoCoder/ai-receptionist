from django.urls import path

from .views import (
    CreditBalanceView,
    CreditHistoryView,
    CreditUsageStatsView,
    CreateCheckoutSessionView,
    CreditsWebhookView,
)

urlpatterns = [
    path('balance/', CreditBalanceView.as_view(), name='credit_balance'),
    path('history/', CreditHistoryView.as_view(), name='credit_history'),
    path('usage-stats/', CreditUsageStatsView.as_view(), name='credit_usage_stats'),
    path('checkout/', CreateCheckoutSessionView.as_view(), name='credit_checkout'),
    path('webhook/', CreditsWebhookView.as_view(), name='credits_webhook'),
]
