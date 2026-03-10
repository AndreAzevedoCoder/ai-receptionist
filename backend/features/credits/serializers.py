from rest_framework import serializers

from .models import Credit


class CreditSerializer(serializers.ModelSerializer):
    """Serializer for credit transactions."""

    class Meta:
        model = Credit
        fields = [
            'id',
            'amount',
            'transaction_type',
            'description',
            'phone_number',
            'call_duration_seconds',
            'created_at',
        ]
        read_only_fields = fields


class CreditBalanceSerializer(serializers.Serializer):
    """Serializer for credit balance response."""

    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_purchased = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_used = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreditUsageStatsSerializer(serializers.Serializer):
    """Serializer for usage statistics."""

    total_calls = serializers.IntegerField()
    total_minutes = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_call_duration = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating a Stripe checkout session."""

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=5.00,
        help_text='Amount in dollars to purchase (minimum $5.00)'
    )
    success_url = serializers.URLField(
        help_text='URL to redirect to after successful payment'
    )
    cancel_url = serializers.URLField(
        help_text='URL to redirect to if payment is cancelled'
    )


class CheckoutSessionResponseSerializer(serializers.Serializer):
    """Response serializer for checkout session creation."""

    checkout_url = serializers.URLField()
    session_id = serializers.CharField()
