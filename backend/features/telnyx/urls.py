from django.urls import path

from .views import TelnyxWebhookView, TelnyxSaveAnswerView

urlpatterns = [
    path('webhook/', TelnyxWebhookView.as_view(), name='telnyx_webhook'),
    path('save-answer/', TelnyxSaveAnswerView.as_view(), name='telnyx_save_answer'),
]
