import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Sum


class Credit(models.Model):
    """
    Tracks all credit transactions for a tenant.

    Positive amounts = credits added (purchases, bonuses, refunds)
    Negative amounts = credits used (call usage, deductions)

    Balance is calculated by summing all credit records for a tenant.
    """

    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('call_usage', 'Call Usage'),
        ('refund', 'Refund'),
        ('adjustment', 'Manual Adjustment'),
        ('bonus', 'Bonus'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='credits',
    )

    # Amount in dollars (positive = added, negative = used)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True,
    )
    description = models.TextField()

    # Call-specific fields (for call_usage transactions)
    phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    call_duration_seconds = models.IntegerField(null=True, blank=True)
    call_log = models.ForeignKey(
        'calls.CallLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions',
    )

    # Payment-specific fields (for purchase transactions)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Credit'
        verbose_name_plural = 'Credits'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'transaction_type']),
        ]

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.tenant.name}: {sign}${self.amount} ({self.transaction_type})"

    @classmethod
    def get_balance(cls, tenant):
        """Calculate the current balance for a tenant."""
        result = cls.objects.filter(tenant=tenant).aggregate(
            balance=Sum('amount')
        )
        return result['balance'] or Decimal('0.00')

    @classmethod
    def get_total_usage(cls, tenant):
        """Calculate total credits used (negative transactions) for a tenant."""
        result = cls.objects.filter(
            tenant=tenant,
            amount__lt=0
        ).aggregate(total=Sum('amount'))
        # Return as positive number
        return abs(result['total'] or Decimal('0.00'))

    @classmethod
    def get_total_purchased(cls, tenant):
        """Calculate total credits purchased for a tenant."""
        result = cls.objects.filter(
            tenant=tenant,
            transaction_type='purchase'
        ).aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')

    @classmethod
    def add_credits(cls, tenant, amount, transaction_type, description, **kwargs):
        """Add a credit transaction (positive amount)."""
        return cls.objects.create(
            tenant=tenant,
            amount=abs(Decimal(str(amount))),
            transaction_type=transaction_type,
            description=description,
            **kwargs
        )

    @classmethod
    def deduct_credits(cls, tenant, amount, transaction_type, description, **kwargs):
        """Deduct credits (creates a negative amount transaction)."""
        return cls.objects.create(
            tenant=tenant,
            amount=-abs(Decimal(str(amount))),
            transaction_type=transaction_type,
            description=description,
            **kwargs
        )
