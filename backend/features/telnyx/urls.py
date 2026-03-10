from django.urls import path

from .views import TelnyxWebhookView

urlpatterns = [
    path('webhook/', TelnyxWebhookView.as_view(), name='telnyx_webhook'),
]
