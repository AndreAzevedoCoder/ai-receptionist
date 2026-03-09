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

    def generate_incoming_call_twiml(
        self,
        forward_number: str,
        timeout: int,
        action_url: str,
        caller_id: str = None,
    ) -> str:
        """
        Generate TwiML for handling incoming calls.

        Attempts to dial the forward number with a timeout.
        If no answer, the action URL will handle forwarding to Vapi.

        Args:
            forward_number: Number to forward the call to
            timeout: Seconds to wait before timing out
            action_url: URL to handle the dial result
            caller_id: Caller ID to use for the outbound call

        Returns:
            TwiML string
        """
        response = VoiceResponse()

        dial = Dial(
            timeout=timeout,
            action=action_url,
            method='POST',
            caller_id=caller_id,
        )
        dial.number(forward_number)

        response.append(dial)

        return str(response)

    def generate_vapi_forward_twiml(
        self,
        vapi_phone_number: str,
        caller_id: str = None,
    ) -> str:
        """
        Generate TwiML to forward the call to a Vapi phone number.

        Args:
            vapi_phone_number: Vapi phone number to forward to
            caller_id: Caller ID to use for the outbound call

        Returns:
            TwiML string
        """
        response = VoiceResponse()

        dial = Dial(caller_id=caller_id)
        dial.number(vapi_phone_number)

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

    def generate_error_twiml(self, message: str) -> str:
        """
        Generate TwiML to say an error message and hang up.

        Args:
            message: Error message to say

        Returns:
            TwiML string
        """
        response = VoiceResponse()
        response.say(message, voice='alice')
        response.hangup()
        return str(response)
