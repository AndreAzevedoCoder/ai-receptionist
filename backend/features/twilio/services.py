import logging

from django.conf import settings
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Dial

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for handling Twilio-related operations."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.forward_number = settings.FORWARD_PHONE_NUMBER
        self.vapi_phone_number = settings.VAPI_ASSISTANT_PHONE_NUMBER

    def validate_request(self, url: str, params: dict, signature: str) -> bool:
        """
        Validate that a request came from Twilio.

        Args:
            url: The full URL of the request
            params: The POST parameters
            signature: The X-Twilio-Signature header

        Returns:
            True if the request is valid, False otherwise
        """
        if not self.auth_token:
            logger.warning("Twilio auth token not configured, skipping validation")
            return True

        validator = RequestValidator(self.auth_token)
        return validator.validate(url, params, signature)

    def generate_incoming_call_twiml(self, action_url: str, timeout: int = 6) -> str:
        """
        Generate TwiML for handling incoming calls.

        Attempts to dial the primary number with a timeout.
        If no answer, the action URL will handle forwarding to Vapi.

        Args:
            action_url: URL to handle the dial result
            timeout: Seconds to wait before timing out

        Returns:
            TwiML string
        """
        response = VoiceResponse()

        dial = Dial(
            timeout=timeout,
            action=action_url,
            method='POST',
        )
        dial.number(self.forward_number)

        response.append(dial)

        return str(response)

    def generate_vapi_forward_twiml(self, caller_id: str = None) -> str:
        """
        Generate TwiML to forward the call to Vapi.ai phone number.

        Args:
            caller_id: The caller ID to use for the outbound call

        Returns:
            TwiML string
        """
        response = VoiceResponse()

        # Use the Twilio phone number as caller ID for the outbound leg
        dial = Dial(caller_id=caller_id or self.phone_number)
        # Forward to Vapi.ai phone number
        dial.number(self.vapi_phone_number)

        response.append(dial)

        return str(response)

    def generate_hangup_twiml(self) -> str:
        """
        Generate TwiML to end the call.

        Returns:
            TwiML string
        """
        response = VoiceResponse()
        response.hangup()
        return str(response)
