import os
from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Activity, CallRecord, Device, SMSMessage, WhatsAppMessage


class AdminCredentialCommandTests(TestCase):
    def test_command_disables_previous_admin_and_updates_configured_admin(self):
        User = get_user_model()
        old_admin = User.objects.create_superuser('Admin2027', 'old@example.com', 'old-password')

        with patch.dict(os.environ, {
            'ADMIN_USERNAME': 'admin2027',
            'ADMIN_EMAIL': 'new@example.com',
            'ADMIN_PASSWORD': 'new-password',
        }, clear=False):
            call_command('create_admin_from_env')

        old_admin.refresh_from_db()
        new_admin = User.objects.get(username='admin2027')
        self.assertFalse(old_admin.is_active)
        self.assertFalse(old_admin.is_superuser)
        self.assertTrue(new_admin.is_active)
        self.assertTrue(new_admin.is_superuser)
        self.assertIsNotNone(authenticate(username='admin2027', password='new-password'))
        self.assertIsNone(authenticate(username='Admin2027', password='old-password'))


class LoginTests(TestCase):
    def test_login_accepts_username_case_from_mobile_keyboard(self):
        User = get_user_model()
        User.objects.create_user('admin2027', 'admin@example.com', 'new-password')

        response = self.client.post(reverse('login'), {
            'username': ' Admin2027 ',
            'password': 'new-password',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')


class ConsentFlowTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.force_login(self.admin)

    def test_bound_device_waits_for_child_consent(self):
        response = self.client.post(reverse('bind-device'), {
            'device_id': 'child-001',
            'name': 'Child Device',
            'os': 'Android 14',
            'battery': '80',
            'connection_status': 'Online',
            'risk_level': 'Low',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['consent_url'].startswith('/child/consent/'))
        self.assertRegex(response.json()['device']['pairing_code'], r'^PAIR-[0-9A-F]+$')
        device = Device.objects.get(device_id='child-001')
        self.assertFalse(device.consent_accepted)
        self.assertFalse(device.is_active)

        consent_response = self.client.post(
            reverse('child_consent', args=[device.pairing_token]),
            {'pairing_code': device.pairing_code, 'consent_accepted': 'on', 'permissions': ['presence', 'battery'], 'child_notifications': 'on'},
        )
        self.assertRedirects(consent_response, f'/child/dashboard/{device.pairing_token}/', fetch_redirect_response=False)
        device.refresh_from_db()
        self.assertTrue(device.consent_accepted)
        self.assertTrue(device.is_active)
        self.assertTrue(device.monitoring_permissions['presence'])
        self.assertTrue(device.monitoring_permissions['battery'])
        self.assertTrue(device.child_notifications_enabled)

    def test_child_heartbeat_and_disconnect_are_token_scoped(self):
        device = Device.objects.create(
            device_id='child-002', name='Child Device', os='Android',
            consent_accepted=True, is_active=True,
        )
        heartbeat = self.client.post(reverse('child-heartbeat', args=[device.pairing_token]))
        self.assertEqual(heartbeat.status_code, 200)
        device.refresh_from_db()
        self.assertIsNotNone(device.last_seen)

        disconnect = self.client.post(reverse('child-control', args=[device.pairing_token]), {'action': 'disconnect'})
        self.assertEqual(disconnect.status_code, 200)
        device.refresh_from_db()
        self.assertFalse(device.is_active)
        self.assertEqual(device.connection_status, 'Disconnected')


class FamilyGuardApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.force_login(self.admin)
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
