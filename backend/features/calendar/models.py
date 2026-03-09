import uuid

from django.db import models


class ScheduledMeeting(models.Model):
    """Stores meeting information scheduled via Google Calendar."""

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE,
        related_name='meetings',
    )
    google_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=255, default='Meeting')
    description = models.TextField(blank=True, default='')
    scheduled_time = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']
        verbose_name = 'Scheduled Meeting'
        verbose_name_plural = 'Scheduled Meetings'

    def __str__(self):
        return f"{self.title} with {self.lead.name} at {self.scheduled_time}"
