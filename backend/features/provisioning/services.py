import logging

from backend.features.tenants.models import Tenant
from .twilio_service import TwilioProvisioningService
from .vapi_service import VapiProvisioningService

logger = logging.getLogger(__name__)


class ProvisioningService:
    """
    Orchestrates the provisioning of all resources for a tenant.
    """

    def __init__(self):
        self.twilio = TwilioProvisioningService()
        self.vapi = VapiProvisioningService()

    def provision_tenant(self, tenant: Tenant) -> bool:
        """
        Provision all required resources for a tenant.

        1. Buy Twilio phone number
        2. Configure Twilio webhook
        3. Create Vapi assistant
        4. Buy Vapi phone number
        5. Assign assistant to phone

        Args:
            tenant: The tenant to provision

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting provisioning for tenant {tenant.id}")
        tenant.status = 'provisioning'
        tenant.save()

        try:
            # Step 1: Buy Twilio phone number
            logger.info(f"Buying Twilio phone number for tenant {tenant.id}")
            twilio_result = self.twilio.buy_phone_number()
            if not twilio_result:
                raise Exception("Failed to buy Twilio phone number")

            tenant.twilio_phone_number = twilio_result['phone_number']
            tenant.twilio_phone_sid = twilio_result['sid']
            tenant.save()

            # Step 2: Configure Twilio webhook
            logger.info(f"Configuring Twilio webhook for tenant {tenant.id}")
            if not self.twilio.configure_webhook(twilio_result['sid'], str(tenant.id)):
                raise Exception("Failed to configure Twilio webhook")

            # Step 3: Create Vapi assistant
            logger.info(f"Creating Vapi assistant for tenant {tenant.id}")
            assistant_id = self.vapi.create_assistant(
                name=f"{tenant.company_name or tenant.name} Assistant",
                company_name=tenant.company_name or tenant.name,
                greeting=tenant.assistant_greeting,
            )
            if not assistant_id:
                raise Exception("Failed to create Vapi assistant")

            tenant.vapi_assistant_id = assistant_id
            tenant.save()

            # Step 4: Buy Vapi phone number
            logger.info(f"Buying Vapi phone number for tenant {tenant.id}")
            vapi_phone = self.vapi.buy_phone_number()
            if not vapi_phone:
                raise Exception("Failed to buy Vapi phone number")

            tenant.vapi_phone_number = vapi_phone['phone_number']
            tenant.vapi_phone_id = vapi_phone['id']
            tenant.save()

            # Step 5: Assign assistant to phone
            logger.info(f"Assigning assistant to phone for tenant {tenant.id}")
            if not self.vapi.assign_assistant_to_phone(vapi_phone['id'], assistant_id):
                raise Exception("Failed to assign assistant to phone")

            # Success!
            tenant.status = 'active'
            tenant.provisioning_error = ''
            tenant.save()

            logger.info(f"Successfully provisioned tenant {tenant.id}")
            return True

        except Exception as e:
            logger.error(f"Provisioning failed for tenant {tenant.id}: {e}")
            tenant.status = 'failed'
            tenant.provisioning_error = str(e)
            tenant.save()
            return False

    def deprovision_tenant(self, tenant: Tenant) -> bool:
        """
        Release all resources for a tenant.

        Args:
            tenant: The tenant to deprovision

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting deprovisioning for tenant {tenant.id}")
        errors = []

        # Release Twilio phone number
        if tenant.twilio_phone_sid:
            if not self.twilio.release_phone_number(tenant.twilio_phone_sid):
                errors.append("Failed to release Twilio phone number")

        # Delete Vapi assistant
        if tenant.vapi_assistant_id:
            if not self.vapi.delete_assistant(tenant.vapi_assistant_id):
                errors.append("Failed to delete Vapi assistant")

        # Release Vapi phone number
        if tenant.vapi_phone_id:
            if not self.vapi.release_phone_number(tenant.vapi_phone_id):
                errors.append("Failed to release Vapi phone number")

        # Clear tenant fields
        tenant.twilio_phone_number = ''
        tenant.twilio_phone_sid = ''
        tenant.vapi_assistant_id = ''
        tenant.vapi_phone_number = ''
        tenant.vapi_phone_id = ''
        tenant.status = 'suspended'
        tenant.save()

        if errors:
            logger.warning(f"Deprovisioning completed with errors for tenant {tenant.id}: {errors}")
            return False

        logger.info(f"Successfully deprovisioned tenant {tenant.id}")
        return True
