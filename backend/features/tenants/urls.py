from django.urls import path

from .views import TenantMeView, TenantStatusView

urlpatterns = [
    path('me/', TenantMeView.as_view(), name='tenant_me'),
    path('me/status/', TenantStatusView.as_view(), name='tenant_status'),
]
