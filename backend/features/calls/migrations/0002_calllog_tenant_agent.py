from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0001_initial'),
        ('tenants', '0001_initial'),
        ('agents', '0001_initial'),
    ]

    operations = [
        # Both tenant_id and agent_id already exist in database
        # This migration is needed for dependency tracking only
    ]
