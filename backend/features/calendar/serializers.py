from rest_framework import serializers

from .models import ScheduledMeeting


class ScheduledMeetingSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    lead_phone = serializers.CharField(source='lead.phone_number', read_only=True)

    class Meta:
        model = ScheduledMeeting
        fields = [
            'id',
            'lead',
            'lead_name',
            'lead_phone',
            'google_event_id',
            'title',
            'description',
            'scheduled_time',
            'duration_minutes',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'google_event_id', 'created_at', 'updated_at']


class CreateMeetingSerializer(serializers.Serializer):
    """Serializer for creating a new meeting with Google Calendar integration."""
    lead_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255, default='Meeting')
    description = serializers.CharField(required=False, default='')
    scheduled_time = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(default=30, min_value=15, max_value=480)
