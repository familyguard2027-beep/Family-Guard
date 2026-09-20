from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0004_device_monitoring_permissions_and_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='companion_id',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='device',
            name='companion_permissions',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]