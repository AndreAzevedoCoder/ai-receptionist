from django.contrib import admin

from .models import CallLog


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ['call_sid', 'from_number', 'to_number', 'status', 'duration', 'lead', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['call_sid', 'from_number', 'to_number']
    readonly_fields = ['id', 'call_sid', 'created_at', 'updated_at']
    ordering = ['-created_at']
    raw_id_fields = ['lead']

    fieldsets = (
        (None, {
            'fields': ('id', 'call_sid')
        }),
        ('Call Details', {
            'fields': ('from_number', 'to_number', 'status', 'duration')
        }),
        ('Lead', {
            'fields': ('lead',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
