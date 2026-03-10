import logging

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Credit
from .serializers import (
    CreditSerializer,
    CreditBalanceSerializer,
    CreditUsageStatsSerializer,
    CreateCheckoutSessionSerializer,
    CheckoutSessionResponseSerializer,
)
from .services import CreditService, StripeCreditsService

logger = logging.getLogger(__name__)


class CreditBalanceView(APIView):
    """
    Get current credit balance and summary.

    GET /api/credits/balance/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        summary = CreditService.get_balance_summary(tenant)
        serializer = CreditBalanceSerializer(summary)
        return Response(serializer.data)


class CreditHistoryView(APIView):
    """
    Get credit transaction history.

    GET /api/credits/history/
    Query params:
        - transaction_type: Filter by type (purchase, call_usage, refund, adjustment, bonus)
        - limit: Number of records to return (default 50, max 100)
        - offset: Pagination offset
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant

        # Get query params
        transaction_type = request.query_params.get('transaction_type')
        limit = min(int(request.query_params.get('limit', 50)), 100)
        offset = int(request.query_params.get('offset', 0))

        # Build queryset
        queryset = Credit.objects.filter(tenant=tenant)

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination
        credits = queryset[offset:offset + limit]

        serializer = CreditSerializer(credits, many=True)

        return Response({
            'results': serializer.data,
            'total': total_count,
            'limit': limit,
            'offset': offset,
        })


class CreditUsageStatsView(APIView):
    """
    Get usage statistics.

    GET /api/credits/usage-stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        stats = CreditService.get_usage_stats(tenant)
        serializer = CreditUsageStatsSerializer(stats)
        return Response(serializer.data)


class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe checkout session for purchasing credits.

    POST /api/credits/checkout/
    Body:
        - amount: Amount in dollars (minimum $5.00)
        - success_url: URL to redirect after successful payment
        - cancel_url: URL to redirect if cancelled
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = request.user.tenant
        stripe_service = StripeCreditsService()

        try:
            result = stripe_service.create_checkout_session(
                tenant=tenant,
                amount=serializer.validated_data['amount'],
                success_url=serializer.validated_data['success_url'],
                cancel_url=serializer.validated_data['cancel_url'],
            )

            response_serializer = CheckoutSessionResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            return Response(
                {'error': 'Failed to create checkout session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditsWebhookView(APIView):
    """
    Handle Stripe webhook events for credit purchases.

    POST /api/credits/webhook/
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

        # Handle checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            stripe_service = StripeCreditsService()
            success = stripe_service.handle_checkout_completed(session)

            if success:
                return Response({'status': 'success'})
            else:
                return Response(
                    {'status': 'error'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Acknowledge other events
        return Response({'status': 'received'})
