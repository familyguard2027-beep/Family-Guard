from django.test import TestCase
from django.urls import reverse

from .models import Activity, CallRecord, Device, SMSMessage, WhatsAppMessage


class FamilyGuardApiTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            device_id='device-001',
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
        Activity.objects.create(device=self.device, activity_type='whatsapp', title='WhatsApp message', summary='Family check-in')
        Activity.objects.create(device=self.device, activity_type='sms', title='SMS message', summary='New package')
        Activity.objects.create(device=self.device, activity_type='calls', title='Call recording ready', summary='Call record created')
        WhatsAppMessage.objects.create(device=self.device, sender='Emily', content='Family check-in')
        SMSMessage.objects.create(device=self.device, sender='MTN', content='New package')
        CallRecord.objects.create(device=self.device, caller='John', duration='03:44')

    def test_dashboard_api_returns_model_stats_and_devices(self):
        response = self.client.get(reverse('dashboard_api'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['stats']['monitored_devices'], 1)
        self.assertEqual(payload['stats']['whatsapp_messages'], 1)
        self.assertEqual(payload['stats']['sms_messages'], 1)
        self.assertEqual(payload['stats']['call_recordings'], 1)
        self.assertEqual(len(payload['devices']), 1)
        self.assertEqual(payload['devices'][0]['name'], "John's Galaxy S23")

    def test_bind_device_creates_device_from_post_payload(self):
        response = self.client.post(
            reverse('bind-device'),
            {
                'device_id': 'device-002',
                'name': 'Parental Device',
                'os': 'Android 14',
                'battery': 91,
                'connection_status': 'Online',
                'risk_level': 'Medium',
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['device']['device_id'], 'device-002')
        self.assertEqual(Device.objects.get(device_id='device-002').name, 'Parental Device')

    def test_bind_device_requires_all_device_details_and_reports_missing_fields(self):
        response = self.client.post(
            reverse('bind-device'),
            {
                'device_id': 'device-002',
                'name': '',
                'os': '',
                'battery': '',
                'risk_level': '',
                'connection_status': 'Online',
                'pairing_code': '',
            },
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertIn('missing_fields', payload)
        self.assertIn('name', payload['missing_fields'])
        self.assertIn('os', payload['missing_fields'])
        self.assertIn('battery', payload['missing_fields'])
        self.assertIn('risk_level', payload['missing_fields'])
        self.assertIn('name', payload['detail'])

    def test_bind_device_generates_unique_pairing_code_when_blank_and_rejects_reuse(self):
        first = self.client.post(reverse('bind-device'), {
            'device_id': 'device-002',
            'name': 'Parental Device A',
            'os': 'Android 14',
            'battery': 91,
            'connection_status': 'Online',
            'risk_level': 'Medium',
            'pairing_code': '',
        })
        self.assertEqual(first.status_code, 201)
        payload = first.json()
        self.assertTrue(payload['device']['pairing_code'].startswith('PAIR-'))
        generated_code = payload['device']['pairing_code']

        second = self.client.post(reverse('bind-device'), {
            'device_id': 'device-003',
            'name': 'Parental Device B',
            'os': 'Android 14',
            'battery': 50,
            'connection_status': 'Online',
            'risk_level': 'Medium',
            'pairing_code': generated_code,
        })
        self.assertIn(second.status_code, [400, 409])
        self.assertEqual(Device.objects.filter(pairing_code=generated_code).count(), 1)
