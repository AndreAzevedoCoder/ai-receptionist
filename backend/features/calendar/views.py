from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.features.leads.models import Lead
from .models import ScheduledMeeting
from .serializers import CreateMeetingSerializer, ScheduledMeetingSerializer
from .services import GoogleCalendarService


class ScheduledMeetingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing scheduled meetings.
    """
    queryset = ScheduledMeeting.objects.all()
    serializer_class = ScheduledMeetingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = ScheduledMeeting.objects.select_related('lead').all()

        # Filter by lead
        lead_id = self.request.query_params.get('lead_id')
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)

        # Filter by status
        meeting_status = self.request.query_params.get('status')
        if meeting_status:
            queryset = queryset.filter(status=meeting_status)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new meeting with Google Calendar integration."""
        serializer = CreateMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            lead = Lead.objects.get(id=serializer.validated_data['lead_id'])
        except Lead.DoesNotExist:
            return Response(
                {'error': 'Lead not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        calendar_service = GoogleCalendarService()
        meeting = calendar_service.create_meeting(
            lead=lead,
            scheduled_time=serializer.validated_data['scheduled_time'],
            duration_minutes=serializer.validated_data.get('duration_minutes', 30),
            title=serializer.validated_data.get('title', 'Meeting'),
            description=serializer.validated_data.get('description', ''),
        )

        if not meeting:
            return Response(
                {'error': 'Failed to create calendar event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        output_serializer = ScheduledMeetingSerializer(meeting)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled meeting."""
        meeting = self.get_object()

        if meeting.status == 'cancelled':
            return Response(
                {'error': 'Meeting is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = GoogleCalendarService()
        success = calendar_service.cancel_meeting(meeting)

        if not success:
            return Response(
                {'error': 'Failed to cancel calendar event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ScheduledMeetingSerializer(meeting)
        return Response(serializer.data)


class AvailableSlotsView(APIView):
    """Get available time slots for scheduling."""
    permission_classes = [AllowAny]

    def get(self, request):
        date_str = request.query_params.get('date')
        duration = int(request.query_params.get('duration', 30))

        if not date_str:
            return Response(
                {'error': 'date parameter is required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = GoogleCalendarService()
        slots = calendar_service.get_available_slots(date, duration_minutes=duration)

        return Response({'date': date_str, 'duration_minutes': duration, 'slots': slots})
