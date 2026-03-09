from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from backend.features.tenants.models import Tenant


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    company_name = serializers.CharField(max_length=255)
    forward_phone_number = serializers.CharField(max_length=20)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

        # Create tenant
        tenant = Tenant.objects.create(
            owner=user,
            name=validated_data['company_name'],
            company_name=validated_data['company_name'],
            forward_phone_number=validated_data['forward_phone_number'],
            status='pending',
        )

        return user, tenant


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information."""
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_status = serializers.CharField(source='tenant.status', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'tenant_id',
            'tenant_name',
            'tenant_status',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'date_joined']
