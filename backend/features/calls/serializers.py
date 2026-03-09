from rest_framework import serializers

from .models import CallLog


class CallLogSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.name', read_only=True, default=None)

    class Meta:
        model = CallLog
        fields = [
            'id',
            'call_sid',
            'from_number',
            'to_number',
            'status',
            'duration',
            'lead',
            'lead_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
