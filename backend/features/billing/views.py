import logging

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import StripeService

logger = logging.getLogger(__name__)


class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.

    POST /api/billing/webhook/
    """
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError as e:
            logger.error(f"Invalid Stripe payload: {e}")
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe signature: {e}")
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle the event
        stripe_service = StripeService()
        success = stripe_service.handle_webhook_event(event)

        if success:
            return Response({'status': 'success'})
        else:
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
