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
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('stripe_subscription_id', models.CharField(max_length=100, unique=True)),
                ('stripe_price_id', models.CharField(max_length=100)),
                ('plan', models.CharField(
                    choices=[('basic', 'Basic'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
                    default='basic',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('past_due', 'Past Due'),
                        ('canceled', 'Canceled'),
                        ('trialing', 'Trialing'),
                    ],
                    default='active',
                    max_length=20,
                )),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subscription',
                    to='tenants.tenant',
                )),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('call_count', models.IntegerField(default=0)),
                ('call_minutes', models.IntegerField(default=0)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('reported_to_stripe', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='usage_records',
                    to='tenants.tenant',
                )),
            ],
            options={
                'verbose_name': 'Usage Record',
                'verbose_name_plural': 'Usage Records',
                'ordering': ['-period_start'],
                'unique_together': {('tenant', 'period_start', 'period_end')},
            },
        ),
    ]
