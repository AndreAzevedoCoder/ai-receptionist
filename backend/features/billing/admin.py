from django.contrib import admin

from .models import Subscription, UsageRecord


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'current_period_end', 'created_at']
    list_filter = ['plan', 'status', 'created_at']
    search_fields = ['tenant__name', 'stripe_subscription_id']
    readonly_fields = ['id', 'stripe_subscription_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'call_count', 'call_minutes', 'period_start', 'period_end', 'reported_to_stripe']
    list_filter = ['reported_to_stripe', 'period_start']
    search_fields = ['tenant__name']
    readonly_fields = ['id', 'created_at']
    ordering = ['-period_start']
