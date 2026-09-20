from django.core.management.base import BaseCommand
from django.utils import timezone

from monitor.models import Activity, CallRecord, Device, SMSMessage, WhatsAppMessage


class Command(BaseCommand):
    help = 'Seed the local family dashboard with sample model-backed data.'

    def handle(self, *args, **options):
        Device.objects.all().delete()
        Activity.objects.all().delete()
        WhatsAppMessage.objects.all().delete()
        SMSMessage.objects.all().delete()
        CallRecord.objects.all().delete()

        device = Device.objects.create(
            device_id='device-01',
            name="John's Galaxy S23",
            os='Android 14',
            battery=78,
            connection_status='Online',
            risk_level='Low',
            pairing_code='PAIR-001',
            consent_accepted=True,
            consent_required=True,
            visible_on_child=True,
            hidden_on_child=False,
            is_active=True,
        )

        device2 = Device.objects.create(
            device_id='device-02',
            name='Office Device',
            os='Android 13',
            battery=64,
            connection_status='Online',
            risk_level='Medium',
            pairing_code='PAIR-002',
            consent_accepted=True,
            consent_required=True,
            visible_on_child=True,
            hidden_on_child=False,
            is_active=True,
        )

        device3 = Device.objects.create(
            device_id='device-03',
            name='Test Device',
            os='Android 12',
            battery=0,
            connection_status='Offline',
            risk_level='Unknown',
            pairing_code='PAIR-003',
            consent_accepted=False,
            consent_required=True,
            visible_on_child=True,
            hidden_on_child=False,
            is_active=False,
        )

        Activity.objects.create(device=device, activity_type='whatsapp', title='WhatsApp message', summary='Family check-in')
        Activity.objects.create(device=device, activity_type='sms', title='SMS message', summary='New package')
        Activity.objects.create(device=device, activity_type='calls', title='Call recording ready', summary='Family call created')
        Activity.objects.create(device=device2, activity_type='notification', title='Device connected', summary='Office Device connected')

        WhatsAppMessage.objects.create(device=device, sender='Emily', content='Family check-in')
        WhatsAppMessage.objects.create(device=device2, sender='Group', content='Dinner plan')
        SMSMessage.objects.create(device=device, sender='MTN', content='New package')
        CallRecord.objects.create(device=device, caller='John', duration='03:44')

        self.stdout.write(self.style.SUCCESS('Seeded 3 devices and family activity records.'))
