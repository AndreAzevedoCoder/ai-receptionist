import uuid

from django.db import models


class Lead(models.Model):
    """Stores lead information collected by AI agent."""

    SOURCE_CHOICES = [
        ('telnyx_ai', 'Telnyx AI'),
        ('vapi_ai', 'Vapi AI'),
        ('manual', 'Manual Entry'),
        ('web', 'Website'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='leads',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='telnyx_ai')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class LeadAnswer(models.Model):
    """Stores individual answers collected from leads during AI calls."""

    QUESTION_TYPE_CHOICES = [
        ('budget', 'Budget'),
        ('credit_score', 'Credit Score'),
        ('location', 'Location'),
        ('move_in_date', 'Move-in Date'),
        ('num_people', 'Number of People'),
        ('name', 'Name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('custom', 'Custom'),
    ]

    SOURCE_CHOICES = [
        ('webhook', 'AI Webhook'),
        ('manual', 'Manual Input'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='custom')
    question_label = models.CharField(max_length=255, blank=True, default='')
    answer = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='webhook')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Lead Answer'
        verbose_name_plural = 'Lead Answers'

    def __str__(self):
        return f"{self.lead.name} - {self.question_type}: {self.answer[:50]}"

    @property
    def display_label(self):
        """Get display label for the question type."""
        labels = {
            'budget': 'Budget',
            'credit_score': 'Credit Score',
            'location': 'Location',
            'move_in_date': 'Move-in Date',
            'num_people': 'Number of People',
            'name': 'Name',
            'email': 'Email',
            'phone': 'Phone',
        }
        return self.question_label or labels.get(self.question_type, self.question_type.title())
