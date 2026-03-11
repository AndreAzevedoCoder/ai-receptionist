import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0001_initial'),
        ('tenants', '0001_initial'),
        ('agents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='calllog',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='call_logs',
                to='tenants.tenant',
            ),
        ),
        migrations.AddField(
            model_name='calllog',
            name='agent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='call_logs',
                to='agents.agent',
            ),
        ),
    ]
