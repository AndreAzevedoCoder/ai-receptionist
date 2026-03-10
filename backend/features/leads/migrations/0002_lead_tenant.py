import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        # tenant_id already exists in database, marking as no-op
        # This migration is needed for dependency tracking
    ]
