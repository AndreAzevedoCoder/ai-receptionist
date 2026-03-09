from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AvailableSlotsView, ScheduledMeetingViewSet

router = DefaultRouter()
router.register('meetings', ScheduledMeetingViewSet, basename='meetings')

urlpatterns = [
    path('slots/', AvailableSlotsView.as_view(), name='available_slots'),
] + router.urls
