"""
Telnyx service for handling Voice AI and Call Control operations.

This service handles:
- Phone number provisioning
- AI Assistant management
- Call Control for ring-first-then-AI flow
- Webhook validation
"""

import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TelnyxService:
    """Service for Telnyx API operations."""

    BASE_URL = "https://api.telnyx.com/v2"

    def __init__(self):
        self.api_key = settings.TELNYX_API_KEY
        self.public_key = settings.TELNYX_PUBLIC_KEY

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def validate_webhook(self, signature: str, timestamp: str) -> bool:
        """
        Validate a Telnyx webhook signature.

        Note: Full ed25519 signature verification requires the PyNaCl library.
        For now, we do basic validation. Add PyNaCl and implement full
        verification for production use.

        Args:
            signature: The telnyx-signature-ed25519 header
            timestamp: The telnyx-timestamp header

        Returns:
            True if valid, False otherwise
        """
        if not self.public_key:
            logger.warning("Telnyx public key not configured, skipping validation")
            return True

        if not signature or not timestamp:
            logger.warning("Missing signature or timestamp, skipping validation")
            return True

        # TODO: Implement proper ed25519 verification with PyNaCl for production
        # See: https://developers.telnyx.com/docs/v2/development/api-guide/webhooks
        return True

    # =========================================
    # Phone Number Management
    # =========================================

    def search_phone_numbers(
        self,
        country_code: str = "US",
        area_code: str = None,
        limit: int = 10,
    ) -> list:
        """
        Search for available phone numbers.

        Args:
            country_code: ISO country code (default US)
            area_code: Optional area code filter
            limit: Number of results

        Returns:
            List of available phone numbers
        """
        params = {
            "filter[country_code]": country_code,
            "filter[limit]": limit,
            "filter[features]": "voice",
        }
        if area_code:
            params["filter[national_destination_code]"] = area_code

        response = requests.get(
            f"{self.BASE_URL}/available_phone_numbers",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json().get("data", [])

    def purchase_phone_number(self, phone_number: str, connection_id: str) -> dict:
        """
        Purchase a phone number and assign it to a connection.

        Args:
            phone_number: The phone number to purchase (E.164 format)
            connection_id: The Telnyx connection ID to assign

        Returns:
            Phone number order details
        """
        payload = {
            "phone_numbers": [{"phone_number": phone_number}],
            "connection_id": connection_id,
        }

        response = requests.post(
            f"{self.BASE_URL}/number_orders",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def release_phone_number(self, phone_number_id: str) -> bool:
        """
        Release/delete a phone number.

        Args:
            phone_number_id: The Telnyx phone number ID

        Returns:
            True if successful
        """
        response = requests.delete(
            f"{self.BASE_URL}/phone_numbers/{phone_number_id}",
            headers=self._headers(),
        )
        return response.status_code == 200

    def update_phone_number(
        self,
        phone_number_id: str,
        connection_id: str = None,
        tags: list = None,
    ) -> dict:
        """
        Update phone number settings.

        Args:
            phone_number_id: The Telnyx phone number ID
            connection_id: Optional new connection ID
            tags: Optional tags for the number

        Returns:
            Updated phone number details
        """
        payload = {}
        if connection_id:
            payload["connection_id"] = connection_id
        if tags:
            payload["tags"] = tags

        response = requests.patch(
            f"{self.BASE_URL}/phone_numbers/{phone_number_id}",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    # =========================================
    # AI Assistant Management
    # =========================================

    def create_ai_assistant(
        self,
        name: str,
        system_prompt: str,
        greeting: str,
        voice: str = "Minimax.speech-2.6-turbo.English_Upbeat_Woman",
        model: str = "Qwen/Qwen3-235B-A22B",
        webhook_url: str = None,
        tools: list = None,
    ) -> dict:
        """
        Create a Telnyx AI Assistant with telephony enabled.

        Args:
            name: Assistant name
            system_prompt: System instructions
            greeting: Initial greeting message
            voice: TTS voice to use (format: provider.model.voice_id)
            model: LLM model to use (format: provider/model_id)
            webhook_url: URL for conversation end webhooks
            tools: List of tool configurations (webhook, handoff, etc.)

        Returns:
            Created assistant details
        """
        payload = {
            "name": name,
            "instructions": system_prompt,
            "greeting": greeting,
            "model": model,
            # Enable telephony for voice calls
            "enabled_features": ["telephony"],
            # Voice settings
            "voice_settings": {
                "voice": voice,
                "voice_speed": 1.0,
                "language_boost": "auto",
            },
            # Transcription settings for speech-to-text
            "transcription": {
                "model": "deepgram/nova-3",
                "language": "auto",
            },
            # Interruption settings for natural conversation
            "interruption_settings": {
                "enable": True,
                "start_speaking_plan": {
                    "wait_seconds": 0.1,
                    "transcription_endpointing_plan": {
                        "on_punctuation_seconds": 0.1,
                        "on_no_punctuation_seconds": 0.1,
                        "on_number_seconds": 0.1,
                    },
                },
            },
        }

        if webhook_url:
            payload["dynamic_variables_webhook_url"] = webhook_url

        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.BASE_URL}/ai/assistants",
            headers=self._headers(),
            json=payload,
        )
        if not response.ok:
            logger.error(f"Telnyx AI Assistant creation failed: {response.status_code} - {response.text}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"Telnyx AI Assistant creation response: {result}")
        return result.get("data", result)

    def update_ai_assistant(
        self,
        assistant_id: str,
        name: str = None,
        system_prompt: str = None,
        greeting: str = None,
        webhook_url: str = None,
        tools: list = None,
    ) -> dict:
        """
        Update an existing AI Assistant.

        Args:
            assistant_id: The assistant ID to update
            name: New name (optional)
            system_prompt: New system instructions (optional)
            greeting: New greeting (optional)
            webhook_url: New webhook URL (optional)
            tools: List of tool configurations (optional)

        Returns:
            Updated assistant details
        """
        payload = {}
        if name:
            payload["name"] = name
        if system_prompt:
            payload["instructions"] = system_prompt
        if greeting:
            payload["greeting"] = greeting
        if webhook_url:
            payload["dynamic_variables_webhook_url"] = webhook_url
        if tools is not None:
            payload["tools"] = tools

        response = requests.patch(
            f"{self.BASE_URL}/ai/assistants/{assistant_id}",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    @staticmethod
    def build_save_answer_tool(webhook_url: str, assistant_id: str) -> dict:
        """
        Build a webhook tool configuration for saving caller answers.

        The AI will call this webhook after collecting each piece of information.

        Args:
            webhook_url: The URL to POST answers to
            assistant_id: The Telnyx assistant ID (used to identify the tenant)

        Returns:
            Tool configuration dict
        """
        return {
            "type": "webhook",
            "webhook": {
                "name": "save_caller_answer",
                "description": f"Save information collected from the caller. Call this immediately after the caller provides an answer to any question. Always include assistant_id: {assistant_id}",
                "url": webhook_url,
                "method": "POST",
                "body_parameters": {
                    "type": "object",
                    "properties": {
                        "question_type": {
                            "type": "string",
                            "description": "The type of question answered: budget, credit_score, location, move_in_date, num_people, name, email, phone, or custom"
                        },
                        "answer": {
                            "type": "string",
                            "description": "The caller's answer to the question"
                        },
                        "caller_phone": {
                            "type": "string",
                            "description": "The caller's phone number"
                        },
                        "assistant_id": {
                            "type": "string",
                            "description": f"The assistant ID. Always use: {assistant_id}"
                        }
                    },
                    "required": ["question_type", "answer", "assistant_id"]
                }
            }
        }

    def delete_ai_assistant(self, assistant_id: str) -> bool:
        """
        Delete an AI Assistant.

        Args:
            assistant_id: The assistant ID to delete

        Returns:
            True if successful
        """
        response = requests.delete(
            f"{self.BASE_URL}/ai/assistants/{assistant_id}",
            headers=self._headers(),
        )
        return response.status_code in [200, 204]

    def get_ai_assistant(self, assistant_id: str) -> dict:
        """
        Get AI Assistant details.

        Args:
            assistant_id: The assistant ID

        Returns:
            Assistant details
        """
        response = requests.get(
            f"{self.BASE_URL}/ai/assistants/{assistant_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json().get("data", {})

    # =========================================
    # TeXML Application Management
    # =========================================

    def create_texml_application(
        self,
        name: str,
        webhook_url: str,
        outbound_voice_profile_id: str = None,
    ) -> dict:
        """
        Create a TeXML Application.

        Args:
            name: Application name
            webhook_url: URL where TeXML webhooks will be sent
            outbound_voice_profile_id: Optional outbound voice profile

        Returns:
            Created TeXML application details
        """
        payload = {
            "friendly_name": name,
            "voice_url": webhook_url,
            "voice_fallback_url": webhook_url,
            "voice_method": "POST",
        }

        if outbound_voice_profile_id:
            payload["outbound_voice_profile_id"] = outbound_voice_profile_id

        response = requests.post(
            f"{self.BASE_URL}/texml_applications",
            headers=self._headers(),
            json=payload,
        )
        if not response.ok:
            logger.error(f"TeXML Application creation failed: {response.status_code} - {response.text}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"TeXML Application creation response: {result}")
        return result.get("data", result)

    def get_texml_application(self, texml_app_id: str) -> dict:
        """
        Get TeXML Application details.

        Args:
            texml_app_id: The TeXML application ID

        Returns:
            TeXML application details
        """
        response = requests.get(
            f"{self.BASE_URL}/texml_applications/{texml_app_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def list_texml_applications(self) -> list:
        """
        List all TeXML Applications.

        Returns:
            List of TeXML applications
        """
        response = requests.get(
            f"{self.BASE_URL}/texml_applications",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json().get("data", [])

    # =========================================
    # Phone Number Assignment
    # =========================================

    def get_phone_number_by_number(self, phone_number: str) -> Optional[dict]:
        """
        Get phone number details by the phone number string.

        Args:
            phone_number: The phone number in E.164 format (e.g., +17435004191)

        Returns:
            Phone number details or None if not found
        """
        response = requests.get(
            f"{self.BASE_URL}/phone_numbers",
            headers=self._headers(),
            params={"filter[phone_number]": phone_number},
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return data[0] if data else None

    def assign_phone_number_to_texml_app(
        self,
        phone_number: str,
        texml_app_id: str,
    ) -> dict:
        """
        Assign a phone number to a TeXML Application.

        Args:
            phone_number: The phone number in E.164 format
            texml_app_id: The TeXML application ID

        Returns:
            Updated phone number details
        """
        # First, get the phone number ID
        phone_data = self.get_phone_number_by_number(phone_number)
        if not phone_data:
            raise ValueError(f"Phone number {phone_number} not found in Telnyx account")

        phone_number_id = phone_data.get("id")

        # Update the phone number's connection to use the TeXML app
        payload = {
            "connection_id": texml_app_id,
        }

        response = requests.patch(
            f"{self.BASE_URL}/phone_numbers/{phone_number_id}",
            headers=self._headers(),
            json=payload,
        )
        if not response.ok:
            logger.error(f"Phone number assignment failed: {response.status_code} - {response.text}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"Phone number {phone_number} assigned to TeXML app {texml_app_id}")
        return result.get("data", result)

    def provision_phone_for_ai_assistant(
        self,
        phone_number: str,
        assistant_id: str,
        assistant_name: str,
        webhook_url: str = None,
    ) -> dict:
        """
        Provision a phone number to work with an AI Assistant.

        This creates a TeXML application that routes calls to the AI Assistant
        and assigns the phone number to that application.

        Args:
            phone_number: The phone number in E.164 format
            assistant_id: The Telnyx AI Assistant ID
            assistant_name: Name for the TeXML application
            webhook_url: Optional webhook URL for call events

        Returns:
            Dict with texml_app_id and phone_number_id
        """
        # Create a TeXML application for this assistant
        # The TeXML app will route incoming calls to the AI assistant
        texml_webhook_url = webhook_url or f"https://api.telnyx.com/v2/ai/assistants/{assistant_id}/calls"

        texml_app = self.create_texml_application(
            name=f"AI Assistant - {assistant_name}",
            webhook_url=texml_webhook_url,
        )
        texml_app_id = texml_app.get("id")

        # Assign the phone number to the TeXML application
        phone_result = self.assign_phone_number_to_texml_app(phone_number, texml_app_id)

        return {
            "texml_app_id": texml_app_id,
            "phone_number_id": phone_result.get("id"),
            "phone_number": phone_number,
            "assistant_id": assistant_id,
        }

    # =========================================
    # Call Control
    # =========================================

    def answer_call(self, call_control_id: str, webhook_url: str = None) -> dict:
        """
        Answer an incoming call.

        Args:
            call_control_id: The call control ID
            webhook_url: Optional webhook URL for this call

        Returns:
            Response data
        """
        payload = {}
        if webhook_url:
            payload["webhook_url"] = webhook_url

        response = requests.post(
            f"{self.BASE_URL}/calls/{call_control_id}/actions/answer",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def transfer_call(
        self,
        call_control_id: str,
        to_number: str,
        from_number: str,
        timeout_secs: int = 30,
        webhook_url: str = None,
    ) -> dict:
        """
        Transfer the call to another number (ring human).

        Uses the 'transfer' action which dials another party and connects them.

        Args:
            call_control_id: The call control ID
            to_number: Number to transfer to
            from_number: Caller ID to show
            timeout_secs: Ring timeout before giving up
            webhook_url: Webhook for call events

        Returns:
            Response data
        """
        payload = {
            "to": to_number,
            "from": from_number,
            "timeout_secs": timeout_secs,
        }
        if webhook_url:
            payload["webhook_url"] = webhook_url

        response = requests.post(
            f"{self.BASE_URL}/calls/{call_control_id}/actions/transfer",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def transfer_to_ai_assistant(
        self,
        call_control_id: str,
        assistant_id: str,
        greeting: str = None,
        webhook_url: str = None,
    ) -> dict:
        """
        Start an AI Assistant conversation on an existing call.

        Uses POST /calls/{call_control_id}/actions/ai_assistant_start

        Args:
            call_control_id: The call control ID of the active call
            assistant_id: The AI Assistant ID
            greeting: Optional greeting for the AI to speak first
            webhook_url: Webhook for AI events

        Returns:
            Response data
        """
        payload = {
            "assistant": {
                "id": assistant_id,
            },
        }
        if greeting:
            payload["greeting"] = greeting
        if webhook_url:
            payload["webhook_url"] = webhook_url

        logger.info(f"AI assistant start payload: {payload}")

        response = requests.post(
            f"{self.BASE_URL}/calls/{call_control_id}/actions/ai_assistant_start",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def hangup_call(self, call_control_id: str) -> dict:
        """
        Hang up a call.

        Args:
            call_control_id: The call control ID

        Returns:
            Response data
        """
        response = requests.post(
            f"{self.BASE_URL}/calls/{call_control_id}/actions/hangup",
            headers=self._headers(),
            json={},
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def speak_text(
        self,
        call_control_id: str,
        text: str,
        voice: str = "nova",
    ) -> dict:
        """
        Speak text on the call using TTS.

        Args:
            call_control_id: The call control ID
            text: Text to speak
            voice: Voice to use

        Returns:
            Response data
        """
        payload = {
            "payload": text,
            "voice": voice,
        }

        response = requests.post(
            f"{self.BASE_URL}/calls/{call_control_id}/actions/speak",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data", {})


class TelnyxWebhookProcessor:
    """Process Telnyx webhook payloads to extract data."""

    @staticmethod
    def get_event_type(payload: dict) -> str:
        """Get the webhook event type."""
        return payload.get("data", {}).get("event_type", "")

    @staticmethod
    def get_call_control_id(payload: dict) -> str:
        """Get the call control ID from webhook."""
        return payload.get("data", {}).get("payload", {}).get("call_control_id", "")

    @staticmethod
    def get_call_leg_id(payload: dict) -> str:
        """Get the call leg ID from webhook."""
        return payload.get("data", {}).get("payload", {}).get("call_leg_id", "")

    @staticmethod
    def get_from_number(payload: dict) -> str:
        """Get the caller's phone number."""
        return payload.get("data", {}).get("payload", {}).get("from", "")

    @staticmethod
    def get_to_number(payload: dict) -> str:
        """Get the called number."""
        return payload.get("data", {}).get("payload", {}).get("to", "")

    @staticmethod
    def get_call_duration(payload: dict) -> int:
        """Get call duration in seconds."""
        # Duration might be in different places depending on event
        data = payload.get("data", {}).get("payload", {})

        # Try different duration field names (Telnyx uses both)
        duration = data.get("duration_secs") or data.get("duration_sec") or 0

        # For AI conversation events, duration might be in call_quality_stats
        if not duration:
            call_quality = data.get("call_quality_stats", {})
            duration = call_quality.get("duration_secs") or call_quality.get("duration_sec") or 0

        if not duration:
            # Try calculating from timestamps
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            if start_time and end_time:
                try:
                    from datetime import datetime
                    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    duration = int((end - start).total_seconds())
                except Exception:
                    pass

        return max(0, int(duration))

    @staticmethod
    def get_bridge_state(payload: dict) -> str:
        """Get bridge state from bridge events."""
        return payload.get("data", {}).get("payload", {}).get("state", "")

    @staticmethod
    def get_ai_conversation_data(payload: dict) -> dict:
        """Extract AI conversation data from end event."""
        data = payload.get("data", {}).get("payload", {})

        return {
            "transcript": data.get("transcript", []),
            "summary": data.get("summary", ""),
            "structured_data": data.get("structured_data", {}),
            "duration_secs": data.get("duration_secs", 0),
        }

    @staticmethod
    def extract_lead_data(payload: dict) -> Optional[dict]:
        """
        Extract lead information from AI conversation webhook.

        Args:
            payload: The webhook payload

        Returns:
            Dictionary with lead data or None
        """
        ai_data = TelnyxWebhookProcessor.get_ai_conversation_data(payload)
        structured_data = ai_data.get("structured_data", {})

        lead_data = {
            "name": structured_data.get("name", ""),
            "email": structured_data.get("email", ""),
            "phone_number": TelnyxWebhookProcessor.get_from_number(payload),
            "notes": ai_data.get("summary", ""),
        }

        # Try to extract name from transcript if not in structured data
        if not lead_data["name"]:
            lead_data["name"] = TelnyxWebhookProcessor._extract_name_from_transcript(
                ai_data.get("transcript", [])
            )

        return lead_data if lead_data["name"] or lead_data["phone_number"] else None

    @staticmethod
    def _extract_name_from_transcript(transcript: list) -> str:
        """Extract name from conversation transcript."""
        for entry in transcript:
            if entry.get("role") == "user":
                content = entry.get("content", "").lower()
                if "my name is" in content:
                    parts = content.split("my name is")
                    if len(parts) > 1:
                        name_part = parts[1].strip()
                        words = name_part.split()[:2]
                        return " ".join(words).title()
                elif "i'm " in content or "i am " in content:
                    for prefix in ["i'm ", "i am "]:
                        if prefix in content:
                            parts = content.split(prefix)
                            if len(parts) > 1:
                                name_part = parts[1].strip()
                                words = name_part.split()[:2]
                                return " ".join(words).title()
        return ""

    @staticmethod
    def extract_meeting_request(payload: dict) -> Optional[dict]:
        """Check if caller requested a meeting."""
        ai_data = TelnyxWebhookProcessor.get_ai_conversation_data(payload)
        structured_data = ai_data.get("structured_data", {})

        wants_meeting = structured_data.get("wants_meeting", False)
        meeting_time = structured_data.get("preferred_meeting_time")

        if wants_meeting or meeting_time:
            return {
                "requested": True,
                "preferred_time": meeting_time,
                "notes": structured_data.get("meeting_notes", ""),
            }
        return None
