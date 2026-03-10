import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.db.models import Sum, Count, Avg

from .models import Credit

logger = logging.getLogger(__name__)

# Cost per minute in dollars
COST_PER_MINUTE = Decimal('0.24')


class CreditService:
    """Service for managing credits."""

    @staticmethod
    def get_balance(tenant):
        """Get the current credit balance for a tenant."""
        return Credit.get_balance(tenant)

    @staticmethod
    def get_balance_summary(tenant):
        """Get a summary of credit balance, purchases, and usage."""
        return {
            'balance': Credit.get_balance(tenant),
            'total_purchased': Credit.get_total_purchased(tenant),
            'total_used': Credit.get_total_usage(tenant),
        }

    @staticmethod
    def get_usage_stats(tenant):
        """Get usage statistics for a tenant."""
        usage_records = Credit.objects.filter(
            tenant=tenant,
            transaction_type='call_usage'
        )

        stats = usage_records.aggregate(
            total_calls=Count('id'),
            total_seconds=Sum('call_duration_seconds'),
            total_cost=Sum('amount'),
        )

        total_seconds = stats['total_seconds'] or 0
        total_calls = stats['total_calls'] or 0

        return {
            'total_calls': total_calls,
            'total_minutes': total_seconds // 60,
            'total_cost': abs(stats['total_cost'] or Decimal('0.00')),
            'average_call_duration': Decimal(str(
                round(total_seconds / total_calls, 2) if total_calls > 0 else 0
            )),
        }

    @staticmethod
    def add_purchased_credits(tenant, amount, stripe_payment_intent_id=None,
                               stripe_checkout_session_id=None):
        """Add purchased credits to a tenant's balance."""
        return Credit.add_credits(
            tenant=tenant,
            amount=amount,
            transaction_type='purchase',
            description=f'Purchased ${amount:.2f} in credits',
            stripe_payment_intent_id=stripe_payment_intent_id or '',
            stripe_checkout_session_id=stripe_checkout_session_id or '',
        )

    @staticmethod
    def deduct_call_credits(tenant, duration_seconds, phone_number, call_log=None):
        """
        Deduct credits for a call based on duration.

        Args:
            tenant: The tenant to deduct credits from
            duration_seconds: Call duration in seconds
            phone_number: Phone number of the caller
            call_log: Optional CallLog instance

        Returns:
            Credit instance if deduction successful, None if insufficient balance
        """
        # Calculate cost (round up to nearest minute)
        minutes = (duration_seconds + 59) // 60  # Round up
        cost = Decimal(str(minutes)) * COST_PER_MINUTE

        # Check balance
        current_balance = Credit.get_balance(tenant)
        if current_balance < cost:
            logger.warning(
                f"Insufficient credits for tenant {tenant.id}. "
                f"Balance: {current_balance}, Required: {cost}"
            )
            # Still deduct but balance will go negative
            # This allows the call to complete but alerts for low balance

        return Credit.deduct_credits(
            tenant=tenant,
            amount=cost,
            transaction_type='call_usage',
            description=f'Call with {phone_number} ({minutes} min)',
            phone_number=phone_number,
            call_duration_seconds=duration_seconds,
            call_log=call_log,
        )

    @staticmethod
    def add_bonus_credits(tenant, amount, description):
        """Add bonus credits to a tenant."""
        return Credit.add_credits(
            tenant=tenant,
            amount=amount,
            transaction_type='bonus',
            description=description,
        )

    @staticmethod
    def add_refund(tenant, amount, description, original_payment_intent_id=None):
        """Add a refund to a tenant's credits."""
        return Credit.add_credits(
            tenant=tenant,
            amount=amount,
            transaction_type='refund',
            description=description,
            stripe_payment_intent_id=original_payment_intent_id or '',
        )

    @staticmethod
    def make_adjustment(tenant, amount, description):
        """Make a manual adjustment to credits (can be positive or negative)."""
        if amount >= 0:
            return Credit.add_credits(
                tenant=tenant,
                amount=amount,
                transaction_type='adjustment',
                description=description,
            )
        else:
            return Credit.deduct_credits(
                tenant=tenant,
                amount=abs(amount),
                transaction_type='adjustment',
                description=description,
            )

    @staticmethod
    def has_sufficient_balance(tenant, required_amount=None):
        """Check if tenant has sufficient balance for a call."""
        balance = Credit.get_balance(tenant)
        if required_amount:
            return balance >= Decimal(str(required_amount))
        # Default: check if they have at least 1 minute worth
        return balance >= COST_PER_MINUTE


class StripeCreditsService:
    """Service for Stripe credit purchases."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_checkout_session(self, tenant, amount, success_url, cancel_url):
        """
        Create a Stripe Checkout session for purchasing credits.

        Args:
            tenant: The tenant purchasing credits
            amount: Amount in dollars

        Returns:
            dict with checkout_url and session_id
        """
        # Ensure tenant has a Stripe customer ID
        if not tenant.stripe_customer_id:
            customer = stripe.Customer.create(
                email=tenant.owner.email,
                name=tenant.name,
                metadata={
                    'tenant_id': str(tenant.id),
                }
            )
            tenant.stripe_customer_id = customer.id
            tenant.save(update_fields=['stripe_customer_id'])

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'AI Receptionist Credits',
                        'description': f'${amount:.2f} in call credits',
                    },
                    'unit_amount': int(Decimal(str(amount)) * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'tenant_id': str(tenant.id),
                'credit_amount': str(amount),
                'type': 'credit_purchase',
            },
        )

        return {
            'checkout_url': session.url,
            'session_id': session.id,
        }

    def handle_checkout_completed(self, session):
        """
        Handle successful checkout session completion.

        Called from webhook handler.
        """
        from backend.features.tenants.models import Tenant

        metadata = session.get('metadata', {})

        if metadata.get('type') != 'credit_purchase':
            return False

        tenant_id = metadata.get('tenant_id')
        credit_amount = metadata.get('credit_amount')

        if not tenant_id or not credit_amount:
            logger.error(f"Missing metadata in checkout session: {session['id']}")
            return False

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            logger.error(f"Tenant not found: {tenant_id}")
            return False

        # Check if we already processed this session
        existing = Credit.objects.filter(
            stripe_checkout_session_id=session['id']
        ).exists()

        if existing:
            logger.info(f"Checkout session already processed: {session['id']}")
            return True

        # Add credits
        CreditService.add_purchased_credits(
            tenant=tenant,
            amount=Decimal(credit_amount),
            stripe_payment_intent_id=session.get('payment_intent', ''),
            stripe_checkout_session_id=session['id'],
        )

        logger.info(
            f"Added {credit_amount} credits for tenant {tenant.name} "
            f"from checkout session {session['id']}"
        )

        return True
