from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0003_device_last_seen'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='child_notifications_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='device',
            name='monitoring_permissions',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]