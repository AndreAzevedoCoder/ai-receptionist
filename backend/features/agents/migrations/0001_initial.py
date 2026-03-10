import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Internal name for this agent', max_length=255)),
                ('telnyx_phone_number', models.CharField(blank=True, db_index=True, max_length=20)),
                ('telnyx_phone_id', models.CharField(blank=True, max_length=100)),
                ('telnyx_assistant_id', models.CharField(blank=True, max_length=100)),
                ('telnyx_connection_id', models.CharField(blank=True, max_length=100)),
                ('forward_phone_number', models.CharField(blank=True, max_length=20)),
                ('timeout_seconds', models.IntegerField(default=6)),
                ('assistant_name', models.CharField(default='AI Receptionist', max_length=100)),
                ('assistant_greeting', models.TextField(default='Hello! Thank you for calling. How can I help you today?')),
                ('system_prompt', models.TextField(blank=True, help_text='Custom system prompt for the AI assistant')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('provisioning', 'Provisioning'),
                        ('active', 'Active'),
                        ('suspended', 'Suspended'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('provisioning_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='agents',
                    to='tenants.tenant',
                )),
            ],
            options={
                'verbose_name': 'Agent',
                'verbose_name_plural': 'Agents',
                'ordering': ['-created_at'],
            },
        ),
    ]
