import uuid

from django.contrib.auth.models import User
from django.db import models


class Tenant(models.Model):
    """
    Represents a tenant in the multi-tenant system.
    Each tenant can have multiple AI agents with their own phone numbers.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Notifications
    notification_email = models.EmailField(blank=True, help_text='Email for lead notifications')

    # Billing
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def agent_count(self):
        return self.agents.count()
