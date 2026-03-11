from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LeadViewSet, LeadAnswerViewSet

router = DefaultRouter()
router.register('answers', LeadAnswerViewSet, basename='lead-answers')
router.register('', LeadViewSet, basename='leads')

urlpatterns = router.urls
