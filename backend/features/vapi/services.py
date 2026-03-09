import hashlib
import hmac
import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class VapiService:
    """Service for handling Vapi.ai webhook processing."""

    def __init__(self):
        self.webhook_secret = settings.VAPI_WEBHOOK_SECRET

    def validate_webhook(self, payload: bytes, signature: str) -> bool:
        """
        Validate a Vapi webhook signature.

        Args:
            payload: Raw request body
            signature: The X-Vapi-Signature header

        Returns:
            True if valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Vapi webhook secret not configured, skipping validation")
            return True

        if not signature:
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def extract_lead_data(self, payload: dict) -> Optional[dict]:
        """
        Extract lead information from Vapi end-of-call webhook payload.

        Args:
            payload: The webhook payload

        Returns:
            Dictionary with lead data or None
        """
        # Try to get data from the analysis field
        analysis = payload.get('analysis', {})

        # The structure depends on how you configure your Vapi assistant
        # This is a common pattern for extracting structured data
        structured_data = analysis.get('structuredData', {})

        lead_data = {
            'name': structured_data.get('name', ''),
            'phone_number': payload.get('customer', {}).get('number', ''),
            'email': structured_data.get('email', ''),
            'notes': '',
        }

        # Try to get summary from analysis
        summary = analysis.get('summary', '')
        if summary:
            lead_data['notes'] = summary

        # If no structured data, try to extract from the conversation
        if not lead_data['name']:
            lead_data['name'] = self._extract_name_from_transcript(payload)

        return lead_data if lead_data['name'] or lead_data['phone_number'] else None

    def extract_meeting_request(self, payload: dict) -> Optional[dict]:
        """
        Check if the caller requested to schedule a meeting.

        Args:
            payload: The webhook payload

        Returns:
            Dictionary with meeting details or None
        """
        analysis = payload.get('analysis', {})
        structured_data = analysis.get('structuredData', {})

        # Check if a meeting was requested
        wants_meeting = structured_data.get('wants_meeting', False)
        meeting_time = structured_data.get('preferred_meeting_time')

        if wants_meeting or meeting_time:
            return {
                'requested': True,
                'preferred_time': meeting_time,
                'notes': structured_data.get('meeting_notes', ''),
            }

        return None

    def _extract_name_from_transcript(self, payload: dict) -> str:
        """
        Try to extract a name from the conversation transcript.

        Args:
            payload: The webhook payload

        Returns:
            Extracted name or empty string
        """
        messages = payload.get('messages', [])

        # Look for patterns like "my name is X" or "I'm X"
        for message in messages:
            if message.get('role') == 'user':
                content = message.get('content', '').lower()
                if 'my name is' in content:
                    # Extract what comes after "my name is"
                    parts = content.split('my name is')
                    if len(parts) > 1:
                        name_part = parts[1].strip()
                        # Take the first word or two
                        words = name_part.split()[:2]
                        return ' '.join(words).title()
                elif "i'm " in content or "i am " in content:
                    # Extract what comes after "i'm" or "i am"
                    for prefix in ["i'm ", "i am "]:
                        if prefix in content:
                            parts = content.split(prefix)
                            if len(parts) > 1:
                                name_part = parts[1].strip()
                                words = name_part.split()[:2]
                                return ' '.join(words).title()

        return ''

    def get_caller_phone_number(self, payload: dict) -> str:
        """
        Extract the caller's phone number from the payload.

        Args:
            payload: The webhook payload

        Returns:
            Phone number or empty string
        """
        customer = payload.get('customer', {})
        return customer.get('number', '')
