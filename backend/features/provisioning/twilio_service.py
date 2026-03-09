import logging
from typing import Optional

from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioProvisioningService:
    """Service for provisioning Twilio phone numbers."""

    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.base_webhook_url = settings.BASE_WEBHOOK_URL

    def buy_phone_number(self, country: str = 'US', area_code: str = None) -> Optional[dict]:
        """
        Purchase a new phone number from Twilio.

        Args:
            country: Country code (US, GB, etc.)
            area_code: Optional area code preference

        Returns:
            Dict with phone_number and sid, or None if failed
        """
        try:
            # Search for available numbers
            search_params = {
                'voice_enabled': True,
                'sms_enabled': True,
            }
            if area_code:
                search_params['area_code'] = area_code

            available_numbers = self.client.available_phone_numbers(country).local.list(
                **search_params,
                limit=1
            )

            if not available_numbers:
                logger.error(f"No available phone numbers found for {country}")
                return None

            # Purchase the first available number
            number = available_numbers[0]
            purchased = self.client.incoming_phone_numbers.create(
                phone_number=number.phone_number
            )

            logger.info(f"Purchased phone number: {purchased.phone_number}")

            return {
                'phone_number': purchased.phone_number,
                'sid': purchased.sid,
            }

        except Exception as e:
            logger.error(f"Error buying phone number: {e}")
            return None

    def configure_webhook(self, phone_sid: str, tenant_id: str) -> bool:
        """
        Configure the webhook URL for a phone number.

        Args:
            phone_sid: Twilio phone number SID
            tenant_id: Tenant ID (not currently used in URL, but could be)

        Returns:
            True if successful, False otherwise
        """
        try:
            webhook_url = f"{self.base_webhook_url}/api/twilio/incoming/"

            self.client.incoming_phone_numbers(phone_sid).update(
                voice_url=webhook_url,
                voice_method='POST',
                status_callback=f"{self.base_webhook_url}/api/twilio/status/",
                status_callback_method='POST',
            )

            logger.info(f"Configured webhook for {phone_sid}: {webhook_url}")
            return True

        except Exception as e:
            logger.error(f"Error configuring webhook: {e}")
            return False

    def release_phone_number(self, phone_sid: str) -> bool:
        """
        Release a phone number back to Twilio.

        Args:
            phone_sid: Twilio phone number SID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.incoming_phone_numbers(phone_sid).delete()
            logger.info(f"Released phone number: {phone_sid}")
            return True

        except Exception as e:
            logger.error(f"Error releasing phone number: {e}")
            return False
