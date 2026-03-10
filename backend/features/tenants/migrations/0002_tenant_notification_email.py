from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='notification_email',
            field=models.EmailField(blank=True, help_text='Email for lead notifications', max_length=254),
        ),
    ]
