"""
Telnyx webhook views for handling Call Control and AI events.

Call Flow:
1. Incoming call → TeXML webhook receives call
2. Return TeXML to dial human's phone with timeout
3. If no answer → Transfer to AI Assistant
4. AI conversation ends → Extract lead data, deduct credits
"""

import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser

from backend.features.agents.models import Agent
from backend.features.calls.models import CallLog
from backend.features.credits.services import CreditService
from backend.features.leads.models import Lead
from .services import TelnyxService, TelnyxWebhookProcessor

logger = logging.getLogger(__name__)


class TelnyxWebhookView(APIView):
    """
    Main webhook handler for Telnyx TeXML events.

    POST /api/telnyx/webhook/

    TeXML sends form-urlencoded data with parameters like:
    - CallSid: Unique call identifier
    - From: Caller's phone number
    - To: Called phone number (our Telnyx number)
    - CallStatus: Current call status

    Returns TeXML XML to control the call flow.
    """
    permission_classes = [AllowAny]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    @csrf_exempt
    def post(self, request):
        # Handle both form-urlencoded (TeXML) and JSON (Call Control) payloads
        # TeXML sends QueryDict with CallSid, Call Control sends dict with 'data' key

        # Check if it's TeXML format (has CallSid but no 'data' key)
        if 'CallSid' in request.data and 'data' not in request.data:
            # TeXML webhook (form-urlencoded)
            return self.handle_texml_webhook(request)
        else:
            # Call Control webhook (JSON)
            return self.handle_call_control_webhook(request)

    def handle_texml_webhook(self, request):
        """Handle TeXML webhook - return XML instructions."""
        # TeXML sends form data
        call_sid = request.data.get('CallSid', '')
        from_number = request.data.get('From', '')
        to_number = request.data.get('To', '')
        call_status = request.data.get('CallStatus', '')
        dial_call_status = request.data.get('DialCallStatus', '')  # Status after <Dial> completes

        logger.info(f"TeXML webhook: CallSid={call_sid}, From={from_number}, To={to_number}, Status={call_status}, DialStatus={dial_call_status}")
        logger.info(f"Full payload: {dict(request.data)}")

        # Look up agent by the called number
        try:
            agent = Agent.objects.get(
                telnyx_phone_number=to_number,
                status="active"
            )
        except Agent.DoesNotExist:
            logger.error(f"No active agent found for number: {to_number}")
            # Return hangup XML
            return HttpResponse(
                '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Sorry, this number is not configured.</Say><Hangup/></Response>',
                content_type='application/xml'
            )

        # Create or update call log
        call_log, created = CallLog.objects.get_or_create(
            call_sid=call_sid,
            defaults={
                'tenant': agent.tenant,
                'agent': agent,
                'from_number': from_number,
                'to_number': to_number,
                'status': 'incoming',
            }
        )

        # Check if this is a callback after <Dial> completed
        if dial_call_status:
            logger.info(f"Dial completed with status: {dial_call_status}")
            if dial_call_status in ['no-answer', 'busy', 'failed', 'canceled']:
                # Human didn't answer, transfer to AI
                call_log.status = 'vapi'
                call_log.save()
                return self._transfer_to_ai_xml(agent)
            elif dial_call_status == 'completed':
                # Human answered and call completed
                call_log.status = 'completed'
                call_log.save()
                return HttpResponse(
                    '<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
                    content_type='application/xml'
                )

        # Initial call - try to bridge to human first
        if agent.forward_phone_number:
            call_log.status = 'forwarded'
            call_log.save()
            return self._dial_human_xml(agent, to_number)
        else:
            # No forward number, go directly to AI
            call_log.status = 'vapi'
            call_log.save()
            return self._transfer_to_ai_xml(agent)

    def _dial_human_xml(self, agent, caller_id):
        """Return TeXML to dial the human with timeout."""
        base_webhook_url = getattr(settings, 'BASE_WEBHOOK_URL', '')
        action_url = f"{base_webhook_url}/api/telnyx/webhook/"

        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial action="{action_url}" timeout="{agent.timeout_seconds}" callerId="{caller_id}">
        <Number>{agent.forward_phone_number}</Number>
    </Dial>
</Response>'''
        logger.info(f"Returning Dial XML to {agent.forward_phone_number} with {agent.timeout_seconds}s timeout")
        return HttpResponse(xml, content_type='application/xml')

    def _transfer_to_ai_xml(self, agent):
        """Return TeXML to transfer to AI Assistant."""
        if not agent.telnyx_assistant_id:
            logger.error(f"No AI assistant configured for agent {agent.id}")
            return HttpResponse(
                '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Sorry, no assistant is available.</Say><Hangup/></Response>',
                content_type='application/xml'
            )

        # Use AI verb to transfer to the assistant
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <AI assistant_id="{agent.telnyx_assistant_id}" />
</Response>'''
        logger.info(f"Transferring to AI assistant {agent.telnyx_assistant_id}")
        return HttpResponse(xml, content_type='application/xml')

    def handle_call_control_webhook(self, request):
        """Handle Call Control JSON webhook."""
        payload = request.data
        event_type = TelnyxWebhookProcessor.get_event_type(payload)

        logger.info(f"Received Call Control webhook: {event_type}")
        logger.info(f"Payload: {payload}")

        # Route to appropriate handler
        handlers = {
            "call.initiated": self.handle_call_initiated,
            "call.answered": self.handle_call_answered,
            "call.bridged": self.handle_call_bridged,
            "call.hangup": self.handle_call_hangup,
            "ai.conversation.ended": self.handle_ai_conversation_ended,
            "call.conversation.ended": self.handle_ai_conversation_ended,
            "call.bridge.failed": self.handle_bridge_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(payload)

        logger.debug(f"Unhandled Call Control event: {event_type}")
        return Response({"status": "ignored", "event": event_type})

    def handle_call_initiated(self, payload: dict) -> Response:
        """
        Handle new incoming call.

        1. Look up agent by the called number
        2. Answer the call
        3. Wait for call.answered event to start AI
        """
        processor = TelnyxWebhookProcessor
        service = TelnyxService()

        call_control_id = processor.get_call_control_id(payload)
        from_number = processor.get_from_number(payload)
        to_number = processor.get_to_number(payload)
        call_leg_id = processor.get_call_leg_id(payload)

        logger.info(f"Incoming call: {from_number} -> {to_number}")

        # Look up agent by the Telnyx phone number
        agent = Agent.objects.filter(
            telnyx_phone_number=to_number,
            status="active"
        ).first()

        if not agent:
            logger.error(f"No active agent found for number: {to_number}")
            # Hang up if no agent configured
            try:
                service.hangup_call(call_control_id)
            except Exception as e:
                logger.error(f"Failed to hangup call: {e}")
            return Response({"status": "error", "message": "No agent configured"})

        # Create call log with status indicating we need to start AI
        call_log = CallLog.objects.create(
            tenant=agent.tenant,
            agent=agent,
            call_sid=call_leg_id,  # Use call_leg_id as our reference
            from_number=from_number,
            to_number=to_number,
            status="incoming",  # Will be updated to "vapi" when AI starts
        )

        # Answer the call - AI will start in handle_call_answered
        try:
            service.answer_call(call_control_id)
            logger.info(f"Answered call {call_leg_id}, waiting for call.answered to start AI")
        except Exception as e:
            logger.error(f"Failed to answer call: {e}")
            if "422" in str(e):
                logger.info("Call was likely hung up before we could answer")
                call_log.status = "failed"
                call_log.save()
            return Response({"status": "error", "message": str(e)})

        return Response({"status": "processing"})

    def handle_call_answered(self, payload: dict) -> Response:
        """
        Handle call answered event.

        Now that the call is fully established, start the AI assistant.
        """
        processor = TelnyxWebhookProcessor

        call_leg_id = processor.get_call_leg_id(payload)
        call_control_id = processor.get_call_control_id(payload)
        to_number = processor.get_to_number(payload)

        logger.info(f"Call answered: {call_leg_id}")

        # Find the call log and agent
        try:
            call_log = CallLog.objects.get(call_sid=call_leg_id)
            agent = call_log.agent

            if agent and call_log.status == "incoming":
                # Start AI now that call is established
                self._transfer_to_ai(call_control_id, agent, call_log)
            else:
                logger.info(f"Call {call_leg_id} already handled or no agent")

        except CallLog.DoesNotExist:
            logger.warning(f"Call log not found for answered call: {call_leg_id}")
            # Try to find agent and start AI anyway
            agent = Agent.objects.filter(
                telnyx_phone_number=to_number,
                status="active"
            ).first()
            if agent:
                # Create call log and start AI
                call_log = CallLog.objects.create(
                    tenant=agent.tenant,
                    agent=agent,
                    call_sid=call_leg_id,
                    from_number=processor.get_from_number(payload),
                    to_number=to_number,
                    status="incoming",
                )
                self._transfer_to_ai(call_control_id, agent, call_log)

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
        """Start AI Assistant on the call."""
        service = TelnyxService()

        if not agent.telnyx_assistant_id:
            logger.error(f"No AI assistant configured for agent {agent.id}")
            return

        logger.info(f"Starting AI assistant {agent.telnyx_assistant_id} on call {call_control_id}")

        try:
            result = service.transfer_to_ai_assistant(
                call_control_id=call_control_id,
                assistant_id=agent.telnyx_assistant_id,
                greeting=agent.assistant_greeting,
            )
            call_log.status = "vapi"  # Reusing status for AI handling
            call_log.save()
            logger.info(f"AI assistant started successfully: {result}")
        except Exception as e:
            logger.error(f"Failed to start AI assistant: {e}")
            # Try to get more details from the response
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")


class TelnyxSaveAnswerView(APIView):
    """
    Webhook endpoint for AI Assistant to save caller answers in real-time.

    POST /api/telnyx/save-answer/

    This is called by the Telnyx AI Assistant's webhook tool after each
    question is answered by the caller.
    """
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        from backend.features.leads.models import LeadAnswer

        data = request.data
        question_type = data.get('question_type', '')
        question_label = data.get('question_label', '')
        answer = data.get('answer', '')
        caller_phone = data.get('caller_phone', '')
        assistant_id = data.get('assistant_id', '')  # Telnyx may pass this

        logger.info(f"Saving answer: {question_type} = {answer} from {caller_phone}")

        if not question_type or not answer:
            return Response(
                {"status": "error", "message": "Missing question_type or answer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try to find tenant from assistant_id
        tenant = None
        if assistant_id:
            try:
                agent = Agent.objects.get(telnyx_assistant_id=assistant_id)
                tenant = agent.tenant
            except Agent.DoesNotExist:
                pass

        # Find or create lead by phone number
        lead = None
        if caller_phone:
            # Find lead by phone (and tenant if available)
            if tenant:
                lead = Lead.objects.filter(phone_number=caller_phone, tenant=tenant).first()
            else:
                lead = Lead.objects.filter(phone_number=caller_phone).first()

            if not lead:
                # Create a new lead
                lead = Lead.objects.create(
                    phone_number=caller_phone,
                    name="Unknown",
                    source="telnyx_ai",
                    tenant=tenant,
                )
                logger.info(f"Created new lead {lead.id} for {caller_phone}")

        if lead:
            # Create LeadAnswer record
            lead_answer = LeadAnswer.objects.create(
                lead=lead,
                question_type=question_type,
                question_label=question_label,
                answer=answer,
            )
            logger.info(f"Created answer {lead_answer.id} for lead {lead.id}: {question_type}")

            # Update lead name if this is a name answer
            if question_type == 'name' and answer:
                lead.name = answer
                lead.save()

            # Update lead email if this is an email answer
            if question_type == 'email' and answer:
                lead.email = answer
                lead.save()

            return Response({
                "status": "success",
                "message": f"Answer saved for {question_type}",
                "lead_id": str(lead.id),
                "answer_id": str(lead_answer.id),
            })

        # No phone number - just acknowledge
        return Response({
            "status": "success",
            "message": f"Answer received: {question_type}",
        })
