from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'owner',
        'twilio_phone_number',
        'forward_phone_number',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'owner__email', 'twilio_phone_number', 'forward_phone_number']
    readonly_fields = [
        'id',
        'twilio_phone_number',
        'twilio_phone_sid',
        'vapi_assistant_id',
        'vapi_phone_number',
        'vapi_phone_id',
        'stripe_customer_id',
        'stripe_subscription_id',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'owner', 'status', 'provisioning_error')
        }),
        ('Phone Configuration', {
            'fields': (
                'forward_phone_number',
                'timeout_seconds',
                'twilio_phone_number',
                'twilio_phone_sid',
            )
        }),
        ('Vapi Configuration', {
            'fields': (
                'vapi_assistant_id',
                'vapi_phone_number',
                'vapi_phone_id',
            )
        }),
        ('AI Assistant', {
            'fields': (
                'assistant_name',
                'assistant_greeting',
                'company_name',
            )
        }),
        ('Billing', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
