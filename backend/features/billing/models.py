import uuid

from django.db import models


class Subscription(models.Model):
    """Tracks tenant subscriptions."""

    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    stripe_price_id = models.CharField(max_length=100)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.tenant.name} - {self.plan} ({self.status})"


class UsageRecord(models.Model):
    """Tracks usage for billing purposes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='usage_records',
    )
    call_count = models.IntegerField(default=0)
    call_minutes = models.IntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    reported_to_stripe = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start']
        unique_together = ['tenant', 'period_start', 'period_end']
        verbose_name = 'Usage Record'
        verbose_name_plural = 'Usage Records'

    def __str__(self):
        return f"{self.tenant.name} - {self.period_start} to {self.period_end}"
