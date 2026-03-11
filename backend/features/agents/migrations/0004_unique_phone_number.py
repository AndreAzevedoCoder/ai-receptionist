from django.db import migrations, models


def convert_empty_to_null(apps, schema_editor):
    """Convert empty phone numbers to NULL."""
    Agent = apps.get_model('agents', 'Agent')
    Agent.objects.filter(telnyx_phone_number='').update(telnyx_phone_number=None)


def convert_null_to_empty(apps, schema_editor):
    """Reverse: convert NULL back to empty string."""
    Agent = apps.get_model('agents', 'Agent')
    Agent.objects.filter(telnyx_phone_number__isnull=True).update(telnyx_phone_number='')


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0003_question'),
    ]

    operations = [
        # Step 1: Make field nullable (without unique yet)
        migrations.AlterField(
            model_name='agent',
            name='telnyx_phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        # Step 2: Convert empty strings to NULL
        migrations.RunPython(convert_empty_to_null, convert_null_to_empty),
        # Step 3: Add unique constraint
        migrations.AlterField(
            model_name='agent',
            name='telnyx_phone_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
