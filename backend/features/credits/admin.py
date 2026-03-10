from django.contrib import admin

from .models import Credit


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'tenant',
        'amount',
        'transaction_type',
        'phone_number',
        'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['tenant__name', 'phone_number', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'tenant', 'amount', 'transaction_type', 'description')
        }),
        ('Call Details', {
            'fields': ('phone_number', 'call_duration_seconds', 'call_log'),
            'classes': ('collapse',),
        }),
        ('Payment Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_checkout_session_id'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
