import uuid

from django.db import models


class Lead(models.Model):
    """Stores lead information collected by Vapi AI agent."""

    SOURCE_CHOICES = [
        ('vapi_ai', 'Vapi AI'),
        ('manual', 'Manual Entry'),
        ('web', 'Website'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='leads',
        null=True,  # Allow null for migration, will be required later
        blank=True,
    )
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='vapi_ai')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
