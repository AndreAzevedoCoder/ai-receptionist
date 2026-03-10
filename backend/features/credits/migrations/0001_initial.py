import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('calls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_type', models.CharField(
                    choices=[
                        ('purchase', 'Purchase'),
                        ('call_usage', 'Call Usage'),
                        ('refund', 'Refund'),
                        ('adjustment', 'Manual Adjustment'),
                        ('bonus', 'Bonus'),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ('description', models.TextField()),
                ('phone_number', models.CharField(blank=True, db_index=True, max_length=20)),
                ('call_duration_seconds', models.IntegerField(blank=True, null=True)),
                ('stripe_payment_intent_id', models.CharField(blank=True, db_index=True, max_length=100)),
                ('stripe_checkout_session_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='credits',
                    to='tenants.tenant',
                )),
                ('call_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='credit_transactions',
                    to='calls.calllog',
                )),
            ],
            options={
                'verbose_name': 'Credit',
                'verbose_name_plural': 'Credits',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='credit',
            index=models.Index(fields=['tenant', 'created_at'], name='credits_cre_tenant__8b3c7c_idx'),
        ),
        migrations.AddIndex(
            model_name='credit',
            index=models.Index(fields=['tenant', 'transaction_type'], name='credits_cre_tenant__f6b4e2_idx'),
        ),
    ]
