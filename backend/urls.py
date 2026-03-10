"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes
    path('api/auth/', include('backend.features.auth.urls')),
    path('api/tenants/', include('backend.features.tenants.urls')),
    path('api/agents/', include('backend.features.agents.urls')),
    path('api/billing/', include('backend.features.billing.urls')),
    path('api/credits/', include('backend.features.credits.urls')),
    path('api/telnyx/', include('backend.features.telnyx.urls')),
    path('api/leads/', include('backend.features.leads.urls')),
    path('api/calls/', include('backend.features.calls.urls')),
    path('api/calendar/', include('backend.features.calendar.urls')),
]
