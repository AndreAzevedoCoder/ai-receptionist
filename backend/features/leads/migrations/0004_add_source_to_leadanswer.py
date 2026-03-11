from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0003_add_leadanswer'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadanswer',
            name='source',
            field=models.CharField(
                choices=[('webhook', 'AI Webhook'), ('manual', 'Manual Input')],
                default='webhook',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='leadanswer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
