from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='agent',
            name='company_name',
            field=models.CharField(blank=True, help_text='Company name for AI greeting', max_length=255),
        ),
    ]
