import uuid

from django.db import models


# Predefined question types that can be toggled
QUESTION_TYPE_CHOICES = [
    ('budget', 'Budget'),
    ('credit_score', 'Credit Score'),
    ('location', 'Location'),
    ('move_in_date', 'Move-in Date'),
    ('num_people', 'Number of People'),
    ('custom', 'Custom Question'),
]


class Agent(models.Model):
    """
    Represents an AI agent belonging to a tenant.
    Each tenant can have multiple agents, but each agent belongs to only one tenant.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='agents'
    )
    name = models.CharField(max_length=255, help_text='Internal name for this agent')
    company_name = models.CharField(max_length=255, blank=True, help_text='Company name for AI greeting')

    # Telnyx Configuration
    telnyx_phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    telnyx_phone_id = models.CharField(max_length=100, blank=True)
    telnyx_assistant_id = models.CharField(max_length=100, blank=True)
    telnyx_connection_id = models.CharField(max_length=100, blank=True)

    # Agent-configurable settings
    forward_phone_number = models.CharField(max_length=20, blank=True)
    timeout_seconds = models.IntegerField(default=6)

    # AI Assistant Configuration
    assistant_name = models.CharField(max_length=100, default='AI Receptionist')
    assistant_greeting = models.TextField(
        default="Hello! Thank you for calling. How can I help you today?"
    )
    system_prompt = models.TextField(
        blank=True,
        help_text='Custom system prompt for the AI assistant'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provisioning_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_provisioned(self):
        """Check if agent is provisioned."""
        return bool(self.telnyx_phone_number and self.telnyx_assistant_id)

    @property
    def phone_number(self):
        """Get the agent's phone number."""
        return self.telnyx_phone_number

    @property
    def assistant_id(self):
        """Get the agent's assistant ID."""
        return self.telnyx_assistant_id

    def build_system_prompt(self):
        """Build system prompt from questions."""
        questions = self.questions.all().order_by('order')
        if not questions.exists():
            return self.system_prompt

        question_labels = {
            'budget': 'Budget',
            'credit_score': 'Credit Score',
            'location': 'Location',
            'move_in_date': 'Move-in Date',
            'num_people': 'Number of People',
        }

        questions_list = []
        for q in questions:
            if q.question_type == 'custom':
                questions_list.append(q.custom_text)
            else:
                questions_list.append(question_labels.get(q.question_type, q.question_type))

        if not questions_list:
            return self.system_prompt

        questions_text = '\n'.join(f'- {q}' for q in questions_list)
        notification_email = self.tenant.notification_email or self.tenant.owner.email

        return f"""You are Alven, a professional AI receptionist.

When speaking with callers, collect the following information:
{questions_text}

Be friendly, professional, and conversational. Don't ask all questions at once - have a natural conversation.

After collecting the information, let the caller know that someone will follow up with them soon.

Send collected information to: {notification_email}"""


class Question(models.Model):
    """
    Represents a question that the AI agent should ask callers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='custom'
    )
    custom_text = models.CharField(
        max_length=255,
        blank=True,
        help_text='Custom question text (only used when question_type is "custom")'
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        if self.question_type == 'custom':
            return f"Custom: {self.custom_text[:50]}"
        return dict(QUESTION_TYPE_CHOICES).get(self.question_type, self.question_type)
