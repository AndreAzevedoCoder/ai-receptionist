from django.contrib import admin

from .models import ScheduledMeeting


@admin.register(ScheduledMeeting)
class ScheduledMeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'lead', 'scheduled_time', 'duration_minutes', 'status', 'created_at']
    list_filter = ['status', 'scheduled_time', 'created_at']
    search_fields = ['title', 'description', 'lead__name', 'lead__phone_number']
    readonly_fields = ['id', 'google_event_id', 'created_at', 'updated_at']
    ordering = ['-scheduled_time']
    raw_id_fields = ['lead']

    fieldsets = (
        (None, {
            'fields': ('id', 'lead', 'google_event_id')
        }),
        ('Meeting Details', {
            'fields': ('title', 'description', 'scheduled_time', 'duration_minutes', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
