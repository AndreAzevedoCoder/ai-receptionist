import logging

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.features.calls.models import CallLog
from .authentication import TwilioWebhookAuthentication
from .services import TwilioService

logger = logging.getLogger(__name__)


class TwilioWebhookMixin:
    """Mixin for Twilio webhook views."""
    authentication_classes = [TwilioWebhookAuthentication]
    permission_classes = [AllowAny]

    def twiml_response(self, twiml: str) -> HttpResponse:
        """Return a TwiML response."""
        return HttpResponse(twiml, content_type='application/xml')


class IncomingCallView(TwilioWebhookMixin, APIView):
    """
    Handle incoming calls from Twilio.

    POST /api/twilio/incoming/

    Attempts to forward the call to the primary number with a 6-second timeout.
    If the call is not answered, it will be forwarded to Vapi.ai.
    """

    @csrf_exempt
    def post(self, request):
        call_sid = request.POST.get('CallSid', '')
        from_number = request.POST.get('From', '')
        to_number = request.POST.get('To', '')

        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")

        # Log the incoming call
        CallLog.objects.create(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            status='incoming',
        )

        # Generate TwiML to dial the primary number
        service = TwilioService()
        action_url = request.build_absolute_uri(reverse('twilio_dial_result'))

        # Fix protocol if behind reverse proxy
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        if forwarded_proto == 'https' and action_url.startswith('http://'):
            action_url = 'https://' + action_url[7:]

        logger.info(f"Action URL for dial result: {action_url}")
        twiml = service.generate_incoming_call_twiml(action_url=action_url, timeout=6)
        logger.info(f"TwiML response: {twiml}")

        return self.twiml_response(twiml)


class DialResultView(TwilioWebhookMixin, APIView):
    """
    Handle the result of dialing the primary number.

    POST /api/twilio/dial-result/

    If the call was not completed (no answer, busy, failed),
    forward to Vapi.ai for AI handling.
    """

    @csrf_exempt
    def post(self, request):
        call_sid = request.POST.get('CallSid', '')
        dial_call_status = request.POST.get('DialCallStatus', '')
        from_number = request.POST.get('From', '')

        logger.info(f"Dial result for {call_sid}: {dial_call_status}")
        logger.info(f"All POST params: {dict(request.POST)}")

        service = TwilioService()

        # Update call log
        try:
            call_log = CallLog.objects.get(call_sid=call_sid)

            if dial_call_status == 'completed':
                # Call was answered and completed
                call_log.status = 'completed'
                call_log.save()
                twiml = service.generate_hangup_twiml()
            else:
                # Call was not answered - forward to Vapi
                call_log.status = 'vapi'
                call_log.save()
                logger.info(f"Forwarding call {call_sid} to Vapi.ai phone: {service.vapi_phone_number}")
                # Use Twilio number as caller ID (required by Twilio for outbound)
                twiml = service.generate_vapi_forward_twiml()
                logger.info(f"Vapi forward TwiML: {twiml}")

        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found for {call_sid}")
            # Forward to Vapi anyway
            twiml = service.generate_vapi_forward_twiml()

        return self.twiml_response(twiml)


class CallStatusView(TwilioWebhookMixin, APIView):
    """
    Handle call status callbacks from Twilio.

    POST /api/twilio/status/

    Updates the call log with final status and duration.
    """

    @csrf_exempt
    def post(self, request):
        call_sid = request.POST.get('CallSid', '')
        call_status = request.POST.get('CallStatus', '')
        call_duration = request.POST.get('CallDuration', '0')

        logger.info(f"Call status update for {call_sid}: {call_status}, duration: {call_duration}s")

        try:
            call_log = CallLog.objects.get(call_sid=call_sid)
            call_log.duration = int(call_duration)

            # Map Twilio status to our status
            status_mapping = {
                'completed': 'completed',
                'busy': 'busy',
                'no-answer': 'no_answer',
                'failed': 'failed',
                'canceled': 'failed',
            }
            if call_status in status_mapping:
                call_log.status = status_mapping[call_status]

            call_log.save()
            logger.info(f"Updated call log {call_sid}: status={call_log.status}, duration={call_log.duration}")

        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found for status update: {call_sid}")

        # Return empty TwiML
        return self.twiml_response('<Response></Response>')
