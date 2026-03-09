import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.features.calls.models import CallLog
from backend.features.calendar.services import GoogleCalendarService
from backend.features.leads.models import Lead
from .authentication import VapiWebhookAuthentication
from .services import VapiService

logger = logging.getLogger(__name__)


class EndOfCallWebhookView(APIView):
    """
    Handle end-of-call webhooks from Vapi.ai.

    POST /api/vapi/end-of-call/

    This webhook is called when a Vapi conversation ends.
    It extracts lead information, creates a Lead record,
    links it to the call log, and optionally schedules a meeting.
    """
    authentication_classes = [VapiWebhookAuthentication]
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        payload = request.data
        logger.info(f"Received Vapi end-of-call webhook: {payload.get('type', 'unknown')}")

        # Only process end-of-call events
        event_type = payload.get('type', '')
        if event_type != 'end-of-call-report':
            logger.info(f"Ignoring Vapi event type: {event_type}")
            return Response({'status': 'ignored'})

        vapi_service = VapiService()

        # Extract lead data
        lead_data = vapi_service.extract_lead_data(payload)
        phone_number = vapi_service.get_caller_phone_number(payload)

        if not lead_data and not phone_number:
            logger.warning("No lead data or phone number found in webhook")
            return Response(
                {'status': 'error', 'message': 'No lead data found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create or update lead
        if phone_number:
            lead, created = Lead.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'name': lead_data.get('name', 'Unknown') if lead_data else 'Unknown',
                    'email': lead_data.get('email', '') if lead_data else '',
                    'notes': lead_data.get('notes', '') if lead_data else '',
                    'source': 'vapi_ai',
                },
            )

            if not created and lead_data:
                # Update existing lead with new information
                if lead_data.get('name') and lead_data['name'] != 'Unknown':
                    lead.name = lead_data['name']
                if lead_data.get('email'):
                    lead.email = lead_data['email']
                if lead_data.get('notes'):
                    lead.notes = f"{lead.notes}\n\n{lead_data['notes']}".strip()
                lead.save()

            logger.info(f"{'Created' if created else 'Updated'} lead {lead.id} for {phone_number}")

            # Link to call log if exists
            try:
                call_log = CallLog.objects.filter(
                    from_number=phone_number,
                    status='vapi',
                ).order_by('-created_at').first()

                if call_log:
                    call_log.lead = lead
                    call_log.status = 'completed'
                    call_log.save()
                    logger.info(f"Linked call log {call_log.call_sid} to lead {lead.id}")
            except Exception as e:
                logger.error(f"Error linking call log: {e}")

            # Check if meeting was requested
            meeting_request = vapi_service.extract_meeting_request(payload)
            if meeting_request and meeting_request.get('requested'):
                logger.info(f"Meeting requested for lead {lead.id}")
                # If a preferred time was provided, try to schedule
                preferred_time = meeting_request.get('preferred_time')
                if preferred_time:
                    try:
                        from datetime import datetime
                        scheduled_time = datetime.fromisoformat(preferred_time)
                        calendar_service = GoogleCalendarService()
                        meeting = calendar_service.create_meeting(
                            lead=lead,
                            scheduled_time=scheduled_time,
                            title='Follow-up Call',
                            description=meeting_request.get('notes', ''),
                        )
                        if meeting:
                            logger.info(f"Created meeting {meeting.id} for lead {lead.id}")
                    except Exception as e:
                        logger.error(f"Error creating meeting: {e}")

            return Response({
                'status': 'success',
                'lead_id': str(lead.id),
                'created': created,
            })

        return Response({'status': 'success', 'message': 'Processed but no lead created'})
