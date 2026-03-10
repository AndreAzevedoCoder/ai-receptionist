from django.contrib import admin

from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'tenant',
        'telnyx_phone_number',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'tenant__name', 'telnyx_phone_number']
    readonly_fields = [
        'id',
        'telnyx_phone_number',
        'telnyx_phone_id',
        'telnyx_assistant_id',
        'telnyx_connection_id',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'tenant', 'status', 'provisioning_error')
        }),
        ('Telnyx Configuration', {
            'fields': (
                'telnyx_phone_number',
                'telnyx_phone_id',
                'telnyx_assistant_id',
                'telnyx_connection_id',
            )
        }),
        ('Call Settings', {
            'fields': ('forward_phone_number', 'timeout_seconds')
        }),
        ('AI Assistant', {
            'fields': (
                'assistant_name',
                'assistant_greeting',
                'system_prompt',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
