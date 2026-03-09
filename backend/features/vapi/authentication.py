import hashlib
import hmac
import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class VapiWebhookUser:
    """Represents a Vapi webhook as an authenticated user."""
    is_authenticated = True

    def __str__(self):
        return 'VapiWebhook'


class VapiWebhookAuthentication(BaseAuthentication):
    """
    Custom authentication for Vapi webhooks.

    Validates the webhook signature to ensure requests
    are genuinely from Vapi.ai.
    """

    def authenticate(self, request):
        # Skip validation in debug mode if no secret is configured
        if settings.DEBUG and not settings.VAPI_WEBHOOK_SECRET:
            logger.warning("Skipping Vapi authentication in debug mode")
            return (VapiWebhookUser(), None)

        signature = request.META.get('HTTP_X_VAPI_SIGNATURE', '')

        if not signature and settings.VAPI_WEBHOOK_SECRET:
            raise AuthenticationFailed('Missing X-Vapi-Signature header')

        if settings.VAPI_WEBHOOK_SECRET:
            # Get the raw body
            body = request.body

            # Compute expected signature
            expected_signature = hmac.new(
                settings.VAPI_WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid Vapi webhook signature")
                raise AuthenticationFailed('Invalid webhook signature')

        return (VapiWebhookUser(), None)

    def authenticate_header(self, request):
        return 'Vapi'
