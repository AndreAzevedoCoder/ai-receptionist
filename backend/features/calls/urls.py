from rest_framework.routers import DefaultRouter

from .views import CallLogViewSet

router = DefaultRouter()
router.register('', CallLogViewSet, basename='calls')

urlpatterns = router.urls
