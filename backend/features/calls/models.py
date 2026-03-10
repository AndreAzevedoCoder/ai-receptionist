import uuid

from django.db import models


class CallLog(models.Model):
    """Logs all incoming calls and their routing status."""

    STATUS_CHOICES = [
        ('incoming', 'Incoming'),
        ('forwarded', 'Forwarded to Primary'),
        ('vapi', 'Forwarded to Vapi AI'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='call_logs',
        null=True,
        blank=True,
    )
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='call_logs',
        null=True,
        blank=True,
    )
    call_sid = models.CharField(max_length=64, unique=True, db_index=True)
    from_number = models.CharField(max_length=20, db_index=True)
    to_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incoming')
    duration = models.IntegerField(default=0, help_text='Call duration in seconds')
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calls',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Call Log'
        verbose_name_plural = 'Call Logs'

    def __str__(self):
        return f"{self.from_number} -> {self.to_number} ({self.status})"
