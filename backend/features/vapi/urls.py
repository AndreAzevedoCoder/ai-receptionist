from django.urls import path

from .views import EndOfCallWebhookView

urlpatterns = [
    path('end-of-call/', EndOfCallWebhookView.as_view(), name='vapi_end_of_call'),
]
