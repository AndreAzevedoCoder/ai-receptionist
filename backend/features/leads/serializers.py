from rest_framework import serializers

from .models import Lead, LeadAnswer


class LeadAnswerSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)

    class Meta:
        model = LeadAnswer
        fields = [
            'id',
            'lead',
            'question_type',
            'question_label',
            'display_label',
            'answer',
            'source',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'lead': {'required': False},
        }


class LeadSerializer(serializers.ModelSerializer):
    answers = LeadAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id',
            'name',
            'phone_number',
            'email',
            'notes',
            'source',
            'answers',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeadListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views without all answers."""
    answer_count = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id',
            'name',
            'phone_number',
            'email',
            'source',
            'answer_count',
            'created_at',
        ]

    def get_answer_count(self, obj):
        return obj.answers.count()
