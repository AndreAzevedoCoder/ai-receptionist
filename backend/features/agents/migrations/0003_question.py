import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0002_agent_company_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question_type', models.CharField(choices=[('budget', 'Budget'), ('credit_score', 'Credit Score'), ('location', 'Location'), ('move_in_date', 'Move-in Date'), ('num_people', 'Number of People'), ('custom', 'Custom Question')], default='custom', max_length=20)),
                ('custom_text', models.CharField(blank=True, help_text='Custom question text (only used when question_type is "custom")', max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='agents.agent')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
