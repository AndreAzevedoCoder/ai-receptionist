from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'email', 'source', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['name', 'phone_number', 'email', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'phone_number', 'email')
        }),
        ('Details', {
            'fields': ('notes', 'source')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
