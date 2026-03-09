import logging

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.features.calls.models import CallLog
from backend.features.tenants.models import Tenant
from .authentication import TwilioWebhookAuthentication
from .services import TwilioService

logger = logging.getLogger(__name__)

# Statuses that should forward to Vapi (DND fix)
FORWARD_TO_VAPI_STATUSES = ['no-answer', 'busy', 'failed', 'canceled']


class TwilioWebhookMixin:
    """Mixin for Twilio webhook views."""
    authentication_classes = [TwilioWebhookAuthentication]
    permission_classes = [AllowAny]

    def twiml_response(self, twiml: str) -> HttpResponse:
        """Return a TwiML response."""
        return HttpResponse(twiml, content_type='application/xml')

    def get_tenant_by_phone(self, phone_number: str) -> Tenant:
        """Look up tenant by Twilio phone number."""
        return Tenant.objects.get(twilio_phone_number=phone_number, status='active')


class IncomingCallView(TwilioWebhookMixin, APIView):
    """
    Handle incoming calls from Twilio.

    POST /api/twilio/incoming/

    Looks up the tenant by the called number, then attempts to forward
    the call to their configured forward number with their configured timeout.
    If not answered, forwards to their Vapi AI assistant.
    """

    @csrf_exempt
    def post(self, request):
        call_sid = request.POST.get('CallSid', '')
        from_number = request.POST.get('From', '')
        to_number = request.POST.get('To', '')

        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")

        # Look up tenant by the called number
        try:
            tenant = self.get_tenant_by_phone(to_number)
        except Tenant.DoesNotExist:
            logger.error(f"No active tenant found for phone number: {to_number}")
            # Return a message and hang up
            service = TwilioService()
            twiml = service.generate_error_twiml("Sorry, this number is not configured.")
            return self.twiml_response(twiml)

        # Log the incoming call with tenant
        CallLog.objects.create(
            tenant=tenant,
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            status='incoming',
        )

        # Build action URL
        action_url = request.build_absolute_uri(reverse('twilio_dial_result'))

        # Fix protocol if behind reverse proxy
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        if forwarded_proto == 'https' and action_url.startswith('http://'):
            action_url = 'https://' + action_url[7:]

        # Generate TwiML using tenant's configuration
        service = TwilioService()
        twiml = service.generate_incoming_call_twiml(
            forward_number=tenant.forward_phone_number,
            timeout=tenant.timeout_seconds,
            action_url=action_url,
            caller_id=tenant.twilio_phone_number,
        )

        logger.info(f"Forwarding to {tenant.forward_phone_number} with {tenant.timeout_seconds}s timeout")
        return self.twiml_response(twiml)


class DialResultView(TwilioWebhookMixin, APIView):
    """
    Handle the result of dialing the primary number.

    POST /api/twilio/dial-result/

    If the call was not completed (no answer, busy, failed, canceled),
    forward to Vapi.ai for AI handling.

    DND Fix: Now forwards on ANY non-completed status, including:
    - no-answer: Phone rang but wasn't answered
    - busy: Phone was busy or DND
    - failed: Call failed for any reason
    - canceled: Call was canceled
    """

    @csrf_exempt
    def post(self, request):
        call_sid = request.POST.get('CallSid', '')
        dial_call_status = request.POST.get('DialCallStatus', '')
        to_number = request.POST.get('To', '')

        logger.info(f"Dial result for {call_sid}: {dial_call_status}")

        # Look up tenant and call log
        try:
            tenant = self.get_tenant_by_phone(to_number)
        except Tenant.DoesNotExist:
            logger.error(f"No tenant found for {to_number}")
            return self.twiml_response('<Response><Hangup/></Response>')

        service = TwilioService()

        try:
            call_log = CallLog.objects.get(call_sid=call_sid)

            if dial_call_status == 'completed':
                # Call was answered and completed
                call_log.status = 'completed'
                call_log.save()
                twiml = service.generate_hangup_twiml()
            elif dial_call_status in FORWARD_TO_VAPI_STATUSES:
                # Forward to Vapi for ANY non-completed status (DND fix)
                call_log.status = 'vapi'
                call_log.save()

                logger.info(
                    f"Forwarding call {call_sid} to Vapi ({dial_call_status}): "
                    f"{tenant.vapi_phone_number}"
                )
                twiml = service.generate_vapi_forward_twiml(
                    vapi_phone_number=tenant.vapi_phone_number,
                    caller_id=tenant.twilio_phone_number,
                )
            else:
                # Unknown status, forward to Vapi anyway
                logger.warning(f"Unknown dial status {dial_call_status}, forwarding to Vapi")
                call_log.status = 'vapi'
                call_log.save()
                twiml = service.generate_vapi_forward_twiml(
                    vapi_phone_number=tenant.vapi_phone_number,
                    caller_id=tenant.twilio_phone_number,
                )

        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found for {call_sid}, forwarding to Vapi")
            twiml = service.generate_vapi_forward_twiml(
                vapi_phone_number=tenant.vapi_phone_number,
                caller_id=tenant.twilio_phone_number,
            )

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
                # Only update if not already forwarded to vapi
                if call_log.status != 'vapi':
                    call_log.status = status_mapping[call_status]

            call_log.save()
            logger.info(f"Updated call log {call_sid}: status={call_log.status}, duration={call_log.duration}")

        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found for status update: {call_sid}")

        return self.twiml_response('<Response></Response>')
