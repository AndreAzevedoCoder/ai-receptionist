import uuid

from django.contrib.auth.models import User
from django.db import models


class Tenant(models.Model):
    """
    Represents a tenant in the multi-tenant system.
    Each tenant has their own phone configuration and billing.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant')

    # Phone Configuration (managed by system, hidden from tenant)
    twilio_phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    twilio_phone_sid = models.CharField(max_length=64, blank=True)
    vapi_assistant_id = models.CharField(max_length=100, blank=True)
    vapi_phone_number = models.CharField(max_length=20, blank=True)
    vapi_phone_id = models.CharField(max_length=100, blank=True)

    # Tenant-configurable settings
    forward_phone_number = models.CharField(max_length=20)
    timeout_seconds = models.IntegerField(default=6)

    # AI Assistant Configuration
    assistant_name = models.CharField(max_length=100, default='AI Receptionist')
    assistant_greeting = models.TextField(
        default="Hello! Thank you for calling. How can I help you today?"
    )
    company_name = models.CharField(max_length=255, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provisioning_error = models.TextField(blank=True)

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
    def is_provisioned(self):
        return bool(self.twilio_phone_number and self.vapi_assistant_id)
