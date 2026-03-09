import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from twilio.request_validator import RequestValidator

logger = logging.getLogger(__name__)


class TwilioWebhookUser:
    """Represents a Twilio webhook as an authenticated user."""
    is_authenticated = True

    def __str__(self):
        return 'TwilioWebhook'


class TwilioWebhookAuthentication(BaseAuthentication):
    """
    Custom authentication for Twilio webhooks.

    Validates the X-Twilio-Signature header to ensure requests
    are genuinely from Twilio.
    """

    def authenticate(self, request):
        # Skip validation in debug mode if no auth token is configured
        if settings.DEBUG and not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Skipping Twilio authentication in debug mode")
            return (TwilioWebhookUser(), None)

        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')

        if not signature:
            raise AuthenticationFailed('Missing X-Twilio-Signature header')

        # Build the full URL, respecting X-Forwarded-Proto from reverse proxy
        url = request.build_absolute_uri()

        # Fix protocol if behind a reverse proxy (Cloudflare, nginx, etc.)
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        if forwarded_proto == 'https' and url.startswith('http://'):
            url = 'https://' + url[7:]

        # Get POST parameters
        params = request.POST.dict()

        # Validate
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        is_valid = validator.validate(url, params, signature)

        if not is_valid:
            logger.warning(f"Invalid Twilio signature for URL: {url}")
            raise AuthenticationFailed('Invalid Twilio signature')

        return (TwilioWebhookUser(), None)

    def authenticate_header(self, request):
        return 'Twilio'
