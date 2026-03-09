import logging
from datetime import datetime
from typing import Optional

import stripe
from django.conf import settings

from backend.features.tenants.models import Tenant
from .models import Subscription

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for managing Stripe billing."""

    def create_customer(self, tenant: Tenant) -> Optional[str]:
        """
        Create a Stripe customer for a tenant.

        Args:
            tenant: The tenant to create a customer for

        Returns:
            Stripe customer ID or None if failed
        """
        try:
            customer = stripe.Customer.create(
                email=tenant.owner.email,
                name=tenant.name,
                metadata={
                    'tenant_id': str(tenant.id),
                },
            )

            tenant.stripe_customer_id = customer.id
            tenant.save()

            logger.info(f"Created Stripe customer {customer.id} for tenant {tenant.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None

    def create_subscription(
        self,
        tenant: Tenant,
        price_id: str,
        trial_days: int = 14,
    ) -> Optional[str]:
        """
        Create a subscription for a tenant.

        Args:
            tenant: The tenant to create a subscription for
            price_id: Stripe price ID
            trial_days: Number of trial days

        Returns:
            Stripe subscription ID or None if failed
        """
        try:
            # Ensure customer exists
            if not tenant.stripe_customer_id:
                customer_id = self.create_customer(tenant)
                if not customer_id:
                    return None
            else:
                customer_id = tenant.stripe_customer_id

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=trial_days,
                metadata={
                    'tenant_id': str(tenant.id),
                },
            )

            # Determine plan from price ID
            plan = 'basic'
            if price_id == settings.STRIPE_PRICE_ID_PRO:
                plan = 'pro'
            elif price_id == settings.STRIPE_PRICE_ID_ENTERPRISE:
                plan = 'enterprise'

            # Create local subscription record
            Subscription.objects.create(
                tenant=tenant,
                stripe_subscription_id=subscription.id,
                stripe_price_id=price_id,
                plan=plan,
                status='trialing' if trial_days > 0 else 'active',
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
            )

            tenant.stripe_subscription_id = subscription.id
            tenant.save()

            logger.info(f"Created subscription {subscription.id} for tenant {tenant.id}")
            return subscription.id

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {e}")
            return None

    def cancel_subscription(self, tenant: Tenant, at_period_end: bool = True) -> bool:
        """
        Cancel a tenant's subscription.

        Args:
            tenant: The tenant to cancel
            at_period_end: If True, cancel at end of billing period

        Returns:
            True if successful, False otherwise
        """
        try:
            if not tenant.stripe_subscription_id:
                logger.warning(f"No subscription to cancel for tenant {tenant.id}")
                return True

            if at_period_end:
                stripe.Subscription.modify(
                    tenant.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe.Subscription.delete(tenant.stripe_subscription_id)

            # Update local record
            try:
                subscription = tenant.subscription
                if at_period_end:
                    subscription.cancel_at_period_end = True
                else:
                    subscription.status = 'canceled'
                subscription.save()
            except Subscription.DoesNotExist:
                pass

            logger.info(f"Canceled subscription for tenant {tenant.id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error canceling subscription: {e}")
            return False

    def record_usage(self, tenant: Tenant, minutes: int) -> bool:
        """
        Report usage to Stripe for metered billing.

        Args:
            tenant: The tenant to report usage for
            minutes: Number of minutes to report

        Returns:
            True if successful, False otherwise
        """
        try:
            if not tenant.stripe_subscription_id:
                logger.warning(f"No subscription for usage reporting: tenant {tenant.id}")
                return False

            # Get the subscription item ID for metered usage
            subscription = stripe.Subscription.retrieve(tenant.stripe_subscription_id)

            # Find the metered item (if using metered billing)
            metered_item = None
            for item in subscription['items']['data']:
                if item['price']['recurring']['usage_type'] == 'metered':
                    metered_item = item
                    break

            if metered_item:
                stripe.SubscriptionItem.create_usage_record(
                    metered_item['id'],
                    quantity=minutes,
                    timestamp=int(datetime.now().timestamp()),
                )
                logger.info(f"Recorded {minutes} minutes usage for tenant {tenant.id}")

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error recording usage: {e}")
            return False

    def handle_webhook_event(self, event: dict) -> bool:
        """
        Handle a Stripe webhook event.

        Args:
            event: Stripe event object

        Returns:
            True if handled successfully, False otherwise
        """
        event_type = event.get('type', '')
        data = event.get('data', {}).get('object', {})

        logger.info(f"Handling Stripe webhook: {event_type}")

        try:
            if event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data)
            elif event_type == 'invoice.paid':
                return self._handle_invoice_paid(data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return True

        except Exception as e:
            logger.error(f"Error handling webhook {event_type}: {e}")
            return False

    def _handle_subscription_updated(self, data: dict) -> bool:
        """Handle subscription update event."""
        subscription_id = data.get('id')
        status = data.get('status')

        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = status
            subscription.current_period_start = datetime.fromtimestamp(data.get('current_period_start'))
            subscription.current_period_end = datetime.fromtimestamp(data.get('current_period_end'))
            subscription.cancel_at_period_end = data.get('cancel_at_period_end', False)
            subscription.save()

            logger.info(f"Updated subscription {subscription_id} to status {status}")
            return True

        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found: {subscription_id}")
            return False

    def _handle_subscription_deleted(self, data: dict) -> bool:
        """Handle subscription deletion event."""
        subscription_id = data.get('id')

        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = 'canceled'
            subscription.save()

            # Suspend the tenant
            tenant = subscription.tenant
            tenant.status = 'suspended'
            tenant.save()

            logger.info(f"Subscription {subscription_id} deleted, tenant suspended")
            return True

        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found: {subscription_id}")
            return False

    def _handle_payment_failed(self, data: dict) -> bool:
        """Handle failed payment event."""
        subscription_id = data.get('subscription')

        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = 'past_due'
            subscription.save()

            logger.info(f"Payment failed for subscription {subscription_id}")
            return True

        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found: {subscription_id}")
            return False

    def _handle_invoice_paid(self, data: dict) -> bool:
        """Handle successful payment event."""
        subscription_id = data.get('subscription')

        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            if subscription.status == 'past_due':
                subscription.status = 'active'
                subscription.save()

            logger.info(f"Invoice paid for subscription {subscription_id}")
            return True

        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found: {subscription_id}")
            return False
