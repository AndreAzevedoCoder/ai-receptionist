from rest_framework import serializers

from .models import Agent, Question


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions."""

    class Meta:
        model = Question
        fields = ['id', 'question_type', 'custom_text', 'order', 'is_active']
        read_only_fields = ['id']


class AgentSerializer(serializers.ModelSerializer):
    """Full agent serializer."""
    phone_number = serializers.CharField(source='telnyx_phone_number', read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id',
            'name',
            'company_name',
            'phone_number',
            'telnyx_phone_number',
            'telnyx_phone_id',
            'telnyx_assistant_id',
            'telnyx_connection_id',
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'system_prompt',
            'questions',
            'status',
            'provisioning_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'phone_number',
            'telnyx_phone_number',
            'telnyx_phone_id',
            'telnyx_assistant_id',
            'telnyx_connection_id',
            'status',
            'provisioning_error',
            'created_at',
            'updated_at',
        ]


class AgentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new agent."""

    class Meta:
        model = Agent
        fields = [
            'name',
            'company_name',
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'system_prompt',
        ]

    def validate_timeout_seconds(self, value):
        if value < 3 or value > 30:
            raise serializers.ValidationError("Timeout must be between 3 and 30 seconds.")
        return value


class AgentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an agent."""

    class Meta:
        model = Agent
        fields = [
            'name',
            'company_name',
            'forward_phone_number',
            'timeout_seconds',
            'assistant_name',
            'assistant_greeting',
            'system_prompt',
        ]

    def validate_timeout_seconds(self, value):
        if value < 3 or value > 30:
            raise serializers.ValidationError("Timeout must be between 3 and 30 seconds.")
        return value


class AgentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing agents."""
    phone_number = serializers.CharField(source='telnyx_phone_number', read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id',
            'name',
            'company_name',
            'phone_number',
            'assistant_name',
            'status',
            'created_at',
        ]
