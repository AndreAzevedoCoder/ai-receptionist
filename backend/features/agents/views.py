import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agent, Question
from .serializers import (
    AgentSerializer,
    AgentCreateSerializer,
    AgentUpdateSerializer,
    AgentListSerializer,
    QuestionSerializer,
)
from backend.features.telnyx.services import TelnyxService

logger = logging.getLogger(__name__)


def create_telnyx_assistant(agent):
    """Create a Telnyx AI Assistant for the agent."""
    try:
        telnyx = TelnyxService()
        base_webhook_url = getattr(settings, 'BASE_WEBHOOK_URL', None)

        webhook_url = None
        if base_webhook_url:
            webhook_url = f"{base_webhook_url}/api/telnyx/webhook/"

        # Create assistant first (without tools, since we need the assistant_id for the tool)
        result = telnyx.create_ai_assistant(
            name=f"{agent.assistant_name} - {agent.tenant.name}",
            system_prompt=agent.system_prompt,
            greeting=agent.assistant_greeting,
            webhook_url=webhook_url,
            tools=None,
        )

        # Save the assistant ID
        agent.telnyx_assistant_id = result.get('id', '')
        agent.status = 'active' if agent.telnyx_assistant_id else 'pending'
        agent.save()

        # Now add tools with the assistant_id
        if base_webhook_url and agent.telnyx_assistant_id:
            save_answer_url = f"{base_webhook_url}/api/telnyx/save-answer/"
            tools = [TelnyxService.build_save_answer_tool(save_answer_url, agent.telnyx_assistant_id)]
            telnyx.update_ai_assistant(
                assistant_id=agent.telnyx_assistant_id,
                tools=tools,
            )

        logger.info(f"Created Telnyx assistant {agent.telnyx_assistant_id} for agent {agent.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to create Telnyx assistant for agent {agent.id}: {e}")
        agent.provisioning_error = str(e)
        agent.status = 'failed'
        agent.save()
        return False


def update_telnyx_assistant(agent):
    """Update the Telnyx AI Assistant's prompt and tools."""
    if not agent.telnyx_assistant_id:
        # No assistant yet, create one
        return create_telnyx_assistant(agent)

    try:
        telnyx = TelnyxService()
        base_webhook_url = getattr(settings, 'BASE_WEBHOOK_URL', None)

        tools = None
        if base_webhook_url:
            save_answer_url = f"{base_webhook_url}/api/telnyx/save-answer/"
            tools = [TelnyxService.build_save_answer_tool(save_answer_url, agent.telnyx_assistant_id)]

        telnyx.update_ai_assistant(
            assistant_id=agent.telnyx_assistant_id,
            system_prompt=agent.system_prompt,
            tools=tools,
        )
        logger.info(f"Updated Telnyx assistant {agent.telnyx_assistant_id} for agent {agent.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to update Telnyx assistant for agent {agent.id}: {e}")
        return False


def assign_phone_number_to_agent(agent, phone_number: str):
    """
    Assign a phone number to an agent and configure it on Telnyx.

    This will:
    1. Create a TeXML application if needed
    2. Assign the phone number to the TeXML app
    3. Update the agent with the phone number and TeXML app ID

    Args:
        agent: The Agent instance
        phone_number: Phone number in E.164 format (e.g., +17435004191)

    Returns:
        True if successful, False otherwise
    """
    if not agent.telnyx_assistant_id:
        logger.error(f"Cannot assign phone to agent {agent.id}: No Telnyx assistant")
        return False

    try:
        telnyx = TelnyxService()
        webhook_url = getattr(settings, 'BASE_WEBHOOK_URL', None)
        if webhook_url:
            webhook_url = f"{webhook_url}/api/telnyx/webhook/"

        result = telnyx.provision_phone_for_ai_assistant(
            phone_number=phone_number,
            assistant_id=agent.telnyx_assistant_id,
            assistant_name=f"{agent.assistant_name} - {agent.tenant.name}",
            webhook_url=webhook_url,
        )

        # Update agent with provisioning details
        agent.telnyx_phone_number = phone_number
        agent.telnyx_connection_id = result.get('texml_app_id', '')
        agent.telnyx_phone_id = result.get('phone_number_id', '')
        agent.save()

        logger.info(f"Assigned phone {phone_number} to agent {agent.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to assign phone to agent {agent.id}: {e}")
        agent.provisioning_error = str(e)
        agent.save()
        return False


def get_or_create_agent(tenant):
    """Get existing agent or create a default one with Telnyx assistant."""
    agent = Agent.objects.filter(tenant=tenant).first()
    if agent:
        # Check if existing agent needs Telnyx assistant provisioning
        if not agent.telnyx_assistant_id and agent.status in ('pending', 'failed'):
            create_telnyx_assistant(agent)
        return agent

    # Create default agent
    agent = Agent.objects.create(
        tenant=tenant,
        name="Main Receptionist",
        assistant_name="Alven",
        assistant_greeting="Hello! Thank you for calling. This is Alven, how can I help you today?",
        status='pending',
    )
    # Create default questions
    default_questions = ['budget', 'credit_score', 'location', 'move_in_date']
    for i, q_type in enumerate(default_questions):
        Question.objects.create(
            agent=agent,
            question_type=q_type,
            order=i,
            is_active=True
        )
    # Build system prompt
    agent.system_prompt = agent.build_system_prompt()
    agent.save()

    # Create Telnyx AI Assistant
    create_telnyx_assistant(agent)

    return agent


class AgentMeView(APIView):
    """
    Get or update the current tenant's single agent.
    Creates an agent automatically if none exists.

    GET /api/agents/me/
    PATCH /api/agents/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Exception:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent = get_or_create_agent(tenant)
        serializer = AgentSerializer(agent)
        return Response(serializer.data)

    def patch(self, request):
        try:
            tenant = request.user.tenant
        except Exception:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent = get_or_create_agent(tenant)

        serializer = AgentUpdateSerializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AgentSerializer(agent).data)


class AgentListCreateView(APIView):
    """
    List all agents for the current tenant or create a new agent.
    Note: Each tenant can only have one agent.

    GET /api/agents/
    POST /api/agents/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Exception:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        agents = Agent.objects.filter(tenant=tenant)
        serializer = AgentListSerializer(agents, many=True)
        return Response({
            'results': serializer.data,
            'count': agents.count(),
        })

    def post(self, request):
        try:
            tenant = request.user.tenant
        except Exception:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Enforce one agent per tenant
        if Agent.objects.filter(tenant=tenant).exists():
            return Response(
                {'error': 'You already have an agent configured. Each account can only have one agent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AgentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agent = Agent.objects.create(
            tenant=tenant,
            status='pending',
            **serializer.validated_data
        )

        # TODO: Trigger provisioning for the new agent
        # provision_agent.delay(agent.id)

        return Response(
            AgentSerializer(agent).data,
            status=status.HTTP_201_CREATED
        )


class AgentDetailView(APIView):
    """
    Retrieve, update, or delete an agent.

    GET /api/agents/<id>/
    PATCH /api/agents/<id>/
    DELETE /api/agents/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get_agent(self, request, agent_id):
        try:
            tenant = request.user.tenant
        except Exception:
            return None, Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            agent = Agent.objects.get(id=agent_id, tenant=tenant)
            return agent, None
        except Agent.DoesNotExist:
            return None, Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, agent_id):
        agent, error = self.get_agent(request, agent_id)
        if error:
            return error

        serializer = AgentSerializer(agent)
        return Response(serializer.data)

    def patch(self, request, agent_id):
        agent, error = self.get_agent(request, agent_id)
        if error:
            return error

        serializer = AgentUpdateSerializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AgentSerializer(agent).data)

    def delete(self, request, agent_id):
        agent, error = self.get_agent(request, agent_id)
        if error:
            return error

        # TODO: Cleanup Twilio/Vapi resources before deletion
        # cleanup_agent.delay(agent.id)

        agent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentQuestionsView(APIView):
    """
    Manage questions for the current tenant's agent.

    GET /api/agents/me/questions/
    PUT /api/agents/me/questions/  (replace all questions)
    """
    permission_classes = [IsAuthenticated]

    def get_agent(self, request):
        try:
            tenant = request.user.tenant
        except Exception:
            return None, Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent = get_or_create_agent(tenant)
        return agent, None

    def get(self, request):
        agent, error = self.get_agent(request)
        if error:
            return error

        questions = agent.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def put(self, request):
        """Replace all questions for the agent and update Telnyx assistant."""
        agent, error = self.get_agent(request)
        if error:
            return error

        # Delete existing questions
        agent.questions.all().delete()

        # Create new questions
        questions_data = request.data.get('questions', [])
        created_questions = []

        for i, q_data in enumerate(questions_data):
            question = Question.objects.create(
                agent=agent,
                question_type=q_data.get('question_type', 'custom'),
                custom_text=q_data.get('custom_text', ''),
                order=i,
                is_active=True
            )
            created_questions.append(question)

        # Update the system_prompt based on new questions
        agent.system_prompt = agent.build_system_prompt()
        agent.save()

        # Update Telnyx AI Assistant with new prompt
        update_telnyx_assistant(agent)

        serializer = QuestionSerializer(created_questions, many=True)
        return Response(serializer.data)
