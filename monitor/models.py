from django.db import models
import uuid


class Device(models.Model):
    device_id = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    os = models.CharField(max_length=60, default='Android')
    battery = models.IntegerField(default=0, null=True, blank=True)
    connection_status = models.CharField(max_length=20, default='Online')
    risk_level = models.CharField(max_length=20, default='Low')
    pairing_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    pairing_token = models.UUIDField(default=uuid.uuid4, unique=True)
    consent_accepted = models.BooleanField(default=False)
    consent_required = models.BooleanField(default=True)
    visible_on_child = models.BooleanField(default=True)
    hidden_on_child = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    monitoring_permissions = models.JSONField(default=dict, blank=True)
    child_notifications_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']


class Activity(models.Model):
    ACTIVITY_TYPES = (
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('calls', 'Calls'),
        ('screen', 'Screen'),
        ('notification', 'Notification'),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=24, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)


class WhatsAppMessage(models.Model):
    sender = models.CharField(max_length=120)
    content = models.TextField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='whatsapp_messages')
    received_at = models.DateTimeField(auto_now_add=True)


class SMSMessage(models.Model):
    sender = models.CharField(max_length=120)
    content = models.TextField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sms_messages')
    received_at = models.DateTimeField(auto_now_add=True)


class CallRecord(models.Model):
    caller = models.CharField(max_length=120)
    duration = models.CharField(max_length=16, default='00:00')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='calls')
    created_at = models.DateTimeField(auto_now_add=True)
