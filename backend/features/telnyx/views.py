"""
Telnyx webhook views for handling Call Control and AI events.

Call Flow:
1. Incoming call → call.initiated webhook
2. Answer call → Bridge to human's phone with timeout
3. If bridge fails (no answer/busy) → Transfer to AI Assistant
4. AI conversation ends → Extract lead data, deduct credits
"""

import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.features.agents.models import Agent
from backend.features.calls.models import CallLog
from backend.features.credits.services import CreditService
from backend.features.leads.models import Lead
from .services import TelnyxService, TelnyxWebhookProcessor

logger = logging.getLogger(__name__)


class TelnyxWebhookView(APIView):
    """
    Main webhook handler for all Telnyx events.

    POST /api/telnyx/webhook/

    Handles:
    - call.initiated: New incoming call
    - call.answered: Call was answered
    - call.bridged: Bridge attempt result
    - call.hangup: Call ended
    - ai.conversation.ended: AI conversation finished
    """
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        payload = request.data
        event_type = TelnyxWebhookProcessor.get_event_type(payload)

        logger.info(f"Received Telnyx webhook: {event_type}")

        # Route to appropriate handler
        handlers = {
            "call.initiated": self.handle_call_initiated,
            "call.answered": self.handle_call_answered,
            "call.bridged": self.handle_call_bridged,
            "call.hangup": self.handle_call_hangup,
            "ai.conversation.ended": self.handle_ai_conversation_ended,
            # Bridge-specific events
            "call.bridge.failed": self.handle_bridge_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(payload)

        # Log unhandled events but return success
        logger.debug(f"Unhandled Telnyx event: {event_type}")
        return Response({"status": "ignored", "event": event_type})

    def handle_call_initiated(self, payload: dict) -> Response:
        """
        Handle new incoming call.

        1. Look up agent by the called number
        2. Answer the call
        3. Bridge to human's phone with timeout
        """
        processor = TelnyxWebhookProcessor
        service = TelnyxService()

        call_control_id = processor.get_call_control_id(payload)
        from_number = processor.get_from_number(payload)
        to_number = processor.get_to_number(payload)
        call_leg_id = processor.get_call_leg_id(payload)

        logger.info(f"Incoming call: {from_number} -> {to_number}")

        # Look up agent by the Telnyx phone number
        try:
            agent = Agent.objects.get(
                telnyx_phone_number=to_number,
                status="active"
            )
        except Agent.DoesNotExist:
            logger.error(f"No active agent found for number: {to_number}")
            # Hang up if no agent configured
            try:
                service.hangup_call(call_control_id)
            except Exception as e:
                logger.error(f"Failed to hangup call: {e}")
            return Response({"status": "error", "message": "No agent configured"})

        # Create call log
        call_log = CallLog.objects.create(
            tenant=agent.tenant,
            agent=agent,
            call_sid=call_leg_id,  # Use call_leg_id as our reference
            from_number=from_number,
            to_number=to_number,
            status="incoming",
        )

        # Answer the call
        try:
            service.answer_call(call_control_id)
            logger.info(f"Answered call {call_leg_id}")
        except Exception as e:
            logger.error(f"Failed to answer call: {e}")
            return Response({"status": "error", "message": str(e)})

        # Bridge to human's phone if configured
        if agent.forward_phone_number:
            try:
                service.bridge_call(
                    call_control_id=call_control_id,
                    to_number=agent.forward_phone_number,
                    from_number=to_number,  # Show the AI number as caller ID
                    timeout_secs=agent.timeout_seconds,
                )
                call_log.status = "forwarded"
                call_log.save()
                logger.info(
                    f"Bridging call to {agent.forward_phone_number} "
                    f"with {agent.timeout_seconds}s timeout"
                )
            except Exception as e:
                logger.error(f"Failed to bridge call: {e}")
                # If bridge fails immediately, go to AI
                self._transfer_to_ai(call_control_id, agent, call_log)
        else:
            # No forward number, go directly to AI
            self._transfer_to_ai(call_control_id, agent, call_log)

        return Response({"status": "processing"})

    def handle_call_answered(self, payload: dict) -> Response:
        """Handle call answered event."""
        call_leg_id = TelnyxWebhookProcessor.get_call_leg_id(payload)
        logger.info(f"Call answered: {call_leg_id}")
        return Response({"status": "ok"})

    def handle_call_bridged(self, payload: dict) -> Response:
        """
        Handle bridge result.

        If bridge state is not 'bridged', transfer to AI.
        """
        processor = TelnyxWebhookProcessor
        service = TelnyxService()

        call_control_id = processor.get_call_control_id(payload)
        call_leg_id = processor.get_call_leg_id(payload)
        bridge_state = processor.get_bridge_state(payload)

        logger.info(f"Bridge result for {call_leg_id}: {bridge_state}")

        # If successfully bridged, human answered - we're done
        if bridge_state == "bridged":
            try:
                call_log = CallLog.objects.get(call_sid=call_leg_id)
                call_log.status = "completed"
                call_log.save()
            except CallLog.DoesNotExist:
                pass
            return Response({"status": "bridged"})

        # Bridge failed (no answer, busy, etc.) - transfer to AI
        try:
            call_log = CallLog.objects.get(call_sid=call_leg_id)
            agent = call_log.agent
            if agent:
                self._transfer_to_ai(call_control_id, agent, call_log)
        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found: {call_leg_id}")

        return Response({"status": "transferring_to_ai"})

    def handle_bridge_failed(self, payload: dict) -> Response:
        """Handle explicit bridge failure event."""
        processor = TelnyxWebhookProcessor
        service = TelnyxService()

        call_control_id = processor.get_call_control_id(payload)
        call_leg_id = processor.get_call_leg_id(payload)

        logger.info(f"Bridge failed for {call_leg_id}, transferring to AI")

        try:
            call_log = CallLog.objects.get(call_sid=call_leg_id)
            agent = call_log.agent
            if agent:
                self._transfer_to_ai(call_control_id, agent, call_log)
        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found: {call_leg_id}")

        return Response({"status": "transferring_to_ai"})

    def handle_call_hangup(self, payload: dict) -> Response:
        """Handle call hangup event."""
        processor = TelnyxWebhookProcessor

        call_leg_id = processor.get_call_leg_id(payload)
        duration = processor.get_call_duration(payload)

        logger.info(f"Call hangup: {call_leg_id}, duration: {duration}s")

        try:
            call_log = CallLog.objects.get(call_sid=call_leg_id)
            call_log.duration = duration
            if call_log.status not in ["completed", "vapi"]:
                call_log.status = "completed"
            call_log.save()
        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found: {call_leg_id}")

        return Response({"status": "ok"})

    def handle_ai_conversation_ended(self, payload: dict) -> Response:
        """
        Handle AI conversation end event.

        1. Extract lead data from conversation
        2. Create/update lead
        3. Deduct credits
        """
        processor = TelnyxWebhookProcessor

        call_leg_id = processor.get_call_leg_id(payload)
        from_number = processor.get_from_number(payload)
        to_number = processor.get_to_number(payload)
        duration = processor.get_call_duration(payload)

        logger.info(f"AI conversation ended: {call_leg_id}, duration: {duration}s")

        # Find the call log and agent
        call_log = None
        agent = None
        tenant = None

        try:
            call_log = CallLog.objects.get(call_sid=call_leg_id)
            agent = call_log.agent
            tenant = call_log.tenant
        except CallLog.DoesNotExist:
            # Try to find agent by phone number
            try:
                agent = Agent.objects.get(
                    telnyx_phone_number=to_number,
                    status="active"
                )
                tenant = agent.tenant
            except Agent.DoesNotExist:
                logger.warning(f"No agent found for AI conversation: {to_number}")

        # Extract lead data
        lead_data = processor.extract_lead_data(payload)

        if lead_data and from_number:
            # Create or update lead
            lead_defaults = {
                "name": lead_data.get("name", "Unknown"),
                "email": lead_data.get("email", ""),
                "notes": lead_data.get("notes", ""),
                "source": "telnyx_ai",
            }
            if tenant:
                lead_defaults["tenant"] = tenant

            lead_filter = {"phone_number": from_number}
            if tenant:
                lead_filter["tenant"] = tenant

            lead, created = Lead.objects.get_or_create(
                **lead_filter,
                defaults=lead_defaults,
            )

            if not created and lead_data:
                # Update existing lead
                if lead_data.get("name") and lead_data["name"] != "Unknown":
                    lead.name = lead_data["name"]
                if lead_data.get("email"):
                    lead.email = lead_data["email"]
                if lead_data.get("notes"):
                    lead.notes = f"{lead.notes}\n\n{lead_data['notes']}".strip()
                lead.save()

            logger.info(f"{'Created' if created else 'Updated'} lead {lead.id}")

            # Link to call log
            if call_log:
                call_log.lead = lead
                call_log.status = "completed"
                call_log.duration = duration
                call_log.save()

        # Deduct credits
        if tenant and duration > 0:
            try:
                credit_transaction = CreditService.deduct_call_credits(
                    tenant=tenant,
                    duration_seconds=duration,
                    phone_number=from_number,
                    call_log=call_log,
                )
                logger.info(
                    f"Deducted {abs(credit_transaction.amount)} credits "
                    f"for {duration}s AI call"
                )
            except Exception as e:
                logger.error(f"Failed to deduct credits: {e}")

        # Check for meeting request
        meeting_request = processor.extract_meeting_request(payload)
        if meeting_request and meeting_request.get("requested"):
            logger.info(f"Meeting requested by {from_number}")
            # TODO: Implement meeting scheduling

        return Response({
            "status": "success",
            "lead_created": lead_data is not None,
        })

    def _transfer_to_ai(
        self,
        call_control_id: str,
        agent: Agent,
        call_log: CallLog,
    ) -> None:
        """Transfer call to AI Assistant."""
        service = TelnyxService()

        if not agent.telnyx_assistant_id:
            logger.error(f"No AI assistant configured for agent {agent.id}")
            return

        try:
            service.transfer_to_ai_assistant(
                call_control_id=call_control_id,
                assistant_id=agent.telnyx_assistant_id,
            )
            call_log.status = "vapi"  # Reusing status for AI handling
            call_log.save()
            logger.info(f"Transferred call to AI assistant {agent.telnyx_assistant_id}")
        except Exception as e:
            logger.error(f"Failed to transfer to AI: {e}")
