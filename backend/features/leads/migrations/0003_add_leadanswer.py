import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_lead_tenant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='source',
            field=models.CharField(
                choices=[
                    ('telnyx_ai', 'Telnyx AI'),
                    ('vapi_ai', 'Vapi AI'),
                    ('manual', 'Manual Entry'),
                    ('web', 'Website'),
                ],
                default='telnyx_ai',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='LeadAnswer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question_type', models.CharField(
                    choices=[
                        ('budget', 'Budget'),
                        ('credit_score', 'Credit Score'),
                        ('location', 'Location'),
                        ('move_in_date', 'Move-in Date'),
                        ('num_people', 'Number of People'),
                        ('name', 'Name'),
                        ('email', 'Email'),
                        ('phone', 'Phone'),
                        ('custom', 'Custom'),
                    ],
                    default='custom',
                    max_length=50,
                )),
                ('question_label', models.CharField(blank=True, default='', max_length=255)),
                ('answer', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='leads.lead')),
            ],
            options={
                'verbose_name': 'Lead Answer',
                'verbose_name_plural': 'Lead Answers',
                'ordering': ['created_at'],
            },
        ),
    ]
