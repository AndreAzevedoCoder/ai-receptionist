from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'owner',
        'status',
        'agent_count',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'owner__email']
    readonly_fields = [
        'id',
        'agent_count',
        'stripe_customer_id',
        'stripe_subscription_id',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'owner', 'status')
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
