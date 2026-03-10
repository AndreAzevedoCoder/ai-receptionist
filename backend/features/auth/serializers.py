import logging

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from backend.features.tenants.models import Tenant
from backend.features.agents.models import Agent, Question

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    # Optional agent setup fields
    phone_number = serializers.CharField(required=False, allow_blank=True)
    questions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    notification_email = serializers.EmailField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Extract agent-related fields
        phone_number = validated_data.pop('phone_number', '')
        questions = validated_data.pop('questions', [])
        notification_email = validated_data.pop('notification_email', '') or validated_data['email']

        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

        # Create tenant with email username as name
        tenant = Tenant.objects.create(
            owner=user,
            name=validated_data['email'].split('@')[0],
            status='active',
            notification_email=notification_email,
        )

        # Always create a default agent
        agent = Agent.objects.create(
            tenant=tenant,
            name="Main Receptionist",
            forward_phone_number=phone_number,
            assistant_name="Alven",
            assistant_greeting="Hello! Thank you for calling. This is Alven, how can I help you today?",
            status='pending',
        )

        # Create questions for the agent
        # Map question labels to question_type values
        question_type_map = {
            'budget': 'budget',
            'credit_score': 'credit_score',
            'credit score': 'credit_score',
            'location': 'location',
            'move_in_date': 'move_in_date',
            'move-in date': 'move_in_date',
            'num_people': 'num_people',
            'number of people': 'num_people',
        }

        for i, q in enumerate(questions):
            q_lower = q.lower().strip()
            question_type = question_type_map.get(q_lower, 'custom')

            Question.objects.create(
                agent=agent,
                question_type=question_type,
                custom_text=q if question_type == 'custom' else '',
                order=i,
                is_active=True
            )

        # Build and save the system prompt
        agent.system_prompt = agent.build_system_prompt()
        agent.save()

        # Create Telnyx AI Assistant
        try:
            from backend.features.agents.views import create_telnyx_assistant
            create_telnyx_assistant(agent)
        except Exception as e:
            logger.error(f"Failed to create Telnyx assistant during registration: {e}")
            # Don't fail registration if Telnyx fails, agent can be provisioned later

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
