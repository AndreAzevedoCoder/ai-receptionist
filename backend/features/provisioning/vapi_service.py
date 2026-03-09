import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class VapiProvisioningService:
    """Service for provisioning Vapi assistants and phone numbers."""

    BASE_URL = 'https://api.vapi.ai'

    def __init__(self):
        self.api_key = settings.VAPI_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        self.base_webhook_url = settings.BASE_WEBHOOK_URL

    def create_assistant(
        self,
        name: str,
        company_name: str,
        greeting: str,
    ) -> Optional[str]:
        """
        Create a new Vapi assistant.

        Args:
            name: Assistant name
            company_name: Company name for the prompt
            greeting: Initial greeting message

        Returns:
            Assistant ID or None if failed
        """
        system_prompt = f"""You are a friendly AI receptionist for {company_name}. Your role is to:

1. Greet callers warmly
2. Ask for their name
3. Ask how you can help them today
4. If they want to speak with someone, let them know the person is unavailable and offer to take a message or schedule a callback
5. Collect their contact information (email is optional)
6. If they want to schedule a meeting, ask for their preferred date and time
7. Summarize what you've collected and confirm it's correct
8. Thank them and end the call professionally

Keep responses concise and conversational. Don't sound robotic."""

        payload = {
            'name': name,
            'model': {
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'systemPrompt': system_prompt,
            },
            'voice': {
                'provider': '11labs',
                'voiceId': 'paula',
            },
            'firstMessage': greeting,
            'serverUrl': f"{self.base_webhook_url}/api/vapi/end-of-call/",
            'analysisPlan': {
                'structuredDataPlan': {
                    'enabled': True,
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': "The caller's full name"},
                            'email': {'type': 'string', 'description': "The caller's email address if provided"},
                            'reason': {'type': 'string', 'description': "Why the caller is calling"},
                            'wants_meeting': {'type': 'boolean', 'description': "Whether the caller wants to schedule a meeting"},
                            'preferred_meeting_time': {'type': 'string', 'description': "Preferred meeting time in ISO 8601 format"},
                            'meeting_notes': {'type': 'string', 'description': "Additional notes about the meeting request"},
                        },
                        'required': ['name'],
                    },
                },
                'summaryPlan': {
                    'enabled': True,
                },
            },
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/assistant",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            assistant_id = data.get('id')
            logger.info(f"Created Vapi assistant: {assistant_id}")
            return assistant_id

        except Exception as e:
            logger.error(f"Error creating Vapi assistant: {e}")
            return None

    def buy_phone_number(self, area_code: str = None) -> Optional[dict]:
        """
        Buy a phone number from Vapi.

        Args:
            area_code: Optional area code preference

        Returns:
            Dict with phone_number and id, or None if failed
        """
        payload = {
            'provider': 'vapi',
        }
        if area_code:
            payload['areaCode'] = area_code

        try:
            response = requests.post(
                f"{self.BASE_URL}/phone-number",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Purchased Vapi phone number: {data.get('number')}")
            return {
                'phone_number': data.get('number'),
                'id': data.get('id'),
            }

        except Exception as e:
            logger.error(f"Error buying Vapi phone number: {e}")
            return None

    def assign_assistant_to_phone(self, phone_id: str, assistant_id: str) -> bool:
        """
        Assign an assistant to a phone number.

        Args:
            phone_id: Vapi phone number ID
            assistant_id: Vapi assistant ID

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.patch(
                f"{self.BASE_URL}/phone-number/{phone_id}",
                headers=self.headers,
                json={'assistantId': assistant_id},
            )
            response.raise_for_status()

            logger.info(f"Assigned assistant {assistant_id} to phone {phone_id}")
            return True

        except Exception as e:
            logger.error(f"Error assigning assistant to phone: {e}")
            return False

    def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete a Vapi assistant.

        Args:
            assistant_id: Vapi assistant ID

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.BASE_URL}/assistant/{assistant_id}",
                headers=self.headers,
            )
            response.raise_for_status()

            logger.info(f"Deleted Vapi assistant: {assistant_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting Vapi assistant: {e}")
            return False

    def release_phone_number(self, phone_id: str) -> bool:
        """
        Release a Vapi phone number.

        Args:
            phone_id: Vapi phone number ID

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.BASE_URL}/phone-number/{phone_id}",
                headers=self.headers,
            )
            response.raise_for_status()

            logger.info(f"Released Vapi phone number: {phone_id}")
            return True

        except Exception as e:
            logger.error(f"Error releasing Vapi phone number: {e}")
            return False
