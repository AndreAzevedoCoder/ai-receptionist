from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """Full tenant serializer for admin use."""
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    agent_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'owner_email',
            'status',
            'agent_count',
            'stripe_customer_id',
            'stripe_subscription_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'owner_email',
            'status',
            'agent_count',
            'stripe_customer_id',
            'stripe_subscription_id',
            'created_at',
            'updated_at',
        ]


class TenantPublicSerializer(serializers.ModelSerializer):
    """
    Public tenant serializer for tenant users.
    """
    agent_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'status',
            'agent_count',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'name',
            'status',
            'agent_count',
            'created_at',
        ]


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant information."""

    class Meta:
        model = Tenant
        fields = [
            'name',
        ]
