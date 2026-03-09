from django.urls import path

from .views import CallStatusView, DialResultView, IncomingCallView

urlpatterns = [
    path('incoming/', IncomingCallView.as_view(), name='twilio_incoming'),
    path('dial-result/', DialResultView.as_view(), name='twilio_dial_result'),
    path('status/', CallStatusView.as_view(), name='twilio_status'),
]
