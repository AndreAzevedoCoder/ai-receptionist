from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """Full tenant serializer for admin use."""
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'owner_email',
            'twilio_phone_number',
            'vapi_assistant_id',
            'vapi_phone_number',
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'company_name',
            'status',
            'provisioning_error',
            'stripe_customer_id',
            'stripe_subscription_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'owner_email',
            'twilio_phone_number',
            'vapi_assistant_id',
            'vapi_phone_number',
            'status',
            'provisioning_error',
            'stripe_customer_id',
            'stripe_subscription_id',
            'created_at',
            'updated_at',
        ]


class TenantPublicSerializer(serializers.ModelSerializer):
    """
    Public tenant serializer for tenant users.
    Only shows configurable fields.
    """
    phone_number = serializers.CharField(source='twilio_phone_number', read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'phone_number',
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'company_name',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'name',
            'phone_number',
            'status',
            'created_at',
        ]


class TenantConfigSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant configuration."""

    class Meta:
        model = Tenant
        fields = [
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'company_name',
        ]

    def validate_timeout_seconds(self, value):
        if value < 3 or value > 30:
            raise serializers.ValidationError("Timeout must be between 3 and 30 seconds.")
        return value
