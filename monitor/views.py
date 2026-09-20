import os
import uuid
import secrets
import json
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Max
from django.db import IntegrityError
from django.utils import timezone

from .models import Activity, CallRecord, Device, SMSMessage, WhatsAppMessage


def _device_to_dict(device):
    return {
        'id': str(device.id),
        'device_id': device.device_id,
        'name': device.name,
        'os': device.os,
        'battery': device.battery,
        'connection': 'Online' if device.connection_status.lower() == 'online' else device.connection_status,
        'connection_status': device.connection_status,
        'risk': device.risk_level,
        'risk_level': device.risk_level,
        'last_seen': device.enrolled_at.isoformat() if device.enrolled_at else None,
        'pairing_code': device.pairing_code,
        'pairing_token': str(device.pairing_token),
        'consent_accepted': device.consent_accepted,
        'consent_required': device.consent_required,
        'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        'visible_on_child': device.visible_on_child,
        'hidden_on_child': device.hidden_on_child,
        'is_active': device.is_active,
    }


def _message_to_dict(message, model_type='whatsapp'):
    return {
        'id': message.id,
        'sender': message.sender,
        'message': message.content,
        'content': message.content,
        'time': message.received_at.isoformat(),
        'received_at': message.received_at.isoformat(),
        'device': message.device.device_id,
        'type': model_type,
    }


def _call_to_dict(call):
    return {
        'id': call.id,
        'caller': call.caller,
        'duration': call.duration,
        'time': call.created_at.isoformat(),
        'created_at': call.created_at.isoformat(),
        'device': call.device.device_id,
    }


def _activity_to_dict(activity):
    return {
        'id': activity.id,
        'title': activity.title,
        'summary': activity.summary,
        'type': activity.activity_type,
        'device': activity.device.device_id,
        'time': activity.created_at.isoformat(),
        'created_at': activity.created_at.isoformat(),
    }


def health(request):
    return JsonResponse({'ok': True, 'app': 'family-guard-monitor', 'environment': os.getenv('DJANGO_SETTINGS_MODULE', 'local')})


def dashboard_api(request):
    devices = list(Device.objects.all().order_by('name'))
    whatsapp_count = WhatsAppMessage.objects.count()
    sms_count = SMSMessage.objects.count()
    call_count = CallRecord.objects.count()
    timeline = [
        _activity_to_dict(activity)
        for activity in Activity.objects.select_related('device').order_by('-created_at')[:10]
    ]
    stats = {
        'monitored_devices': Device.objects.count(),
        'whatsapp_messages': whatsapp_count,
        'sms_messages': sms_count,
        'call_recordings': call_count,
    }
    return JsonResponse({'stats': stats, 'timeline': timeline, 'devices': [_device_to_dict(device) for device in devices]})


def devices_api(request):
    devices = Device.objects.all().order_by('name')
    return JsonResponse({'devices': [_device_to_dict(device) for device in devices]})


def device_detail_api(request, device_id):
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'detail': 'Device not found'}, status=404)
    return JsonResponse({'device': _device_to_dict(device)})


def whatsapp_api(request):
    messages = WhatsAppMessage.objects.select_related('device').order_by('-received_at')
    return JsonResponse({'messages': [_message_to_dict(message, 'whatsapp') for message in messages]})


def sms_api(request):
    messages = SMSMessage.objects.select_related('device').order_by('-received_at')
    return JsonResponse({'messages': [_message_to_dict(message, 'sms') for message in messages]})


def calls_api(request):
    calls = CallRecord.objects.select_related('device').order_by('-created_at')
    return JsonResponse({'calls': [_call_to_dict(call) for call in calls]})


def recordings_api(request):
    calls = CallRecord.objects.select_related('device').order_by('-created_at')
    recordings = []
    for call in calls:
        recordings.append({
            'id': f'rec-{call.id}',
            'source': call.device.device_id,
            'duration': call.duration,
            'date': call.created_at.date().isoformat(),
            'status': 'Ready',
        })
    return JsonResponse({'recordings': recordings})


def notifications_api(request):
    notifications = []
    for activity in Activity.objects.select_related('device').filter(activity_type='notification').order_by('-created_at')[:20]:
        notifications.append({
            'id': f'note-{activity.id}',
            'title': activity.title,
            'source': activity.device.name,
            'time': activity.created_at.isoformat(),
            'severity': 'info',
        })
    return JsonResponse({'notifications': notifications})


def timeline_api(request):
    timeline = [_activity_to_dict(activity) for activity in Activity.objects.select_related('device').order_by('-created_at')[:20]]
    return JsonResponse({'timeline': timeline})


def _generate_unique_pairing_code():
    for _ in range(50):
        code = f"PAIR-{secrets.token_hex(4).upper()}"
        if not Device.objects.filter(pairing_code=code).exists():
            return code
    return f"PAIR-{secrets.token_hex(8).upper()}"


@login_required(login_url='/login/')
def pairing_code_api(request):
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)
    return JsonResponse({'pairing_code': _generate_unique_pairing_code()})


@login_required(login_url='/login/')
def profile_api(request):
    user = request.user
    full_name = user.get_full_name() or user.username
    return JsonResponse({
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': full_name,
        'email': user.email,
        'is_authenticated': True,
    })


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def bind_device(request):
    device_id = (request.POST.get('device_id') or '').strip()
    name = (request.POST.get('name') or '').strip()
    os_name = (request.POST.get('os') or '').strip()
    battery = (request.POST.get('battery') or '').strip()
    connection_status = (request.POST.get('connection_status') or '').strip() or 'Online'
    risk_level = (request.POST.get('risk_level') or '').strip()

    missing_fields = []
    if not device_id:
        missing_fields.append('device_id')
    if not name:
        missing_fields.append('name')
    if not os_name:
        missing_fields.append('os')
    if not battery:
        missing_fields.append('battery')
    if not risk_level:
        missing_fields.append('risk_level')

    if missing_fields:
        return JsonResponse({
            'detail': f"Missing required device details: {', '.join(missing_fields)}.",
            'missing_fields': missing_fields,
        }, status=400)

    try:
        battery_int = int(battery)
    except (TypeError, ValueError):
        return JsonResponse({
            'detail': 'Missing required device details: battery must be an integer number.',
            'missing_fields': ['battery'],
        }, status=400)

    raw_pairing_code = (request.POST.get('pairing_code') or '').strip()
    if raw_pairing_code:
        reused = Device.objects.filter(pairing_code=raw_pairing_code).exclude(device_id=device_id).first()
        if reused:
            return JsonResponse({
                'detail': 'That pairing code is already used by another device.',
                'code': raw_pairing_code,
                'missing_fields': [],
            }, status=409)
        pairing_code = raw_pairing_code
    else:
        pairing_code = _generate_unique_pairing_code()

    pairing_token = uuid.uuid4()
    existing_device = Device.objects.filter(device_id=device_id).first()

    try:
        if existing_device:
            existing_device.name = name
            existing_device.os = os_name
            existing_device.battery = battery_int
            existing_device.connection_status = connection_status
            existing_device.risk_level = risk_level
            existing_device.pairing_code = pairing_code
            existing_device.pairing_token = pairing_token
            existing_device.consent_accepted = False
            existing_device.consent_required = True
            existing_device.visible_on_child = True
            existing_device.hidden_on_child = False
            existing_device.is_active = False
            existing_device.last_seen = None
            existing_device.monitoring_permissions = {}
            existing_device.child_notifications_enabled = False
            existing_device.save()
            created = False
            device = existing_device
        else:
            device = Device.objects.create(
                device_id=device_id,
                name=name,
                os=os_name,
                battery=battery_int,
                connection_status=connection_status,
                risk_level=risk_level,
                pairing_code=pairing_code,
                pairing_token=pairing_token,
                consent_accepted=False,
                consent_required=True,
                visible_on_child=True,
                hidden_on_child=False,
                is_active=False,
            )
            created = True
    except IntegrityError:
        return JsonResponse({
            'detail': 'This device id or pairing code is already in use.',
            'missing_fields': [],
        }, status=409)

    return JsonResponse({
        'detail': 'Device paired successfully',
        'created': created,
        'redirect_url': '/pages/devices/',
        'consent_url': f'/child/consent/{device.pairing_token}/',
        'device': _device_to_dict(device),
    }, status=201 if created else 200)


def child_consent_view(request, pairing_token):
    try:
        device = Device.objects.get(pairing_token=pairing_token)
    except Device.DoesNotExist:
        return HttpResponse('Pairing token not found', status=404)

    if request.method == 'GET' and device.consent_accepted and device.is_active:
        return HttpResponseRedirect(f'/child/dashboard/{device.pairing_token}/')

    if request.method == 'POST':
        submitted_pairing_code = (request.POST.get('pairing_code') or '').strip().upper()
        if submitted_pairing_code != (device.pairing_code or '').upper():
            return render(request, 'child/consent.html', {
                'device': device,
                'error': 'Enter the pairing code supplied by the parent before accepting consent.',
            })
        accepted = request.POST.get('consent_accepted') == 'on'
        selected_permissions = request.POST.getlist('permissions')
        allowed_permissions = {
            'presence': 'Device online/offline status and last seen time',
            'battery': 'Battery level',
            'screen': 'Screen sharing when separately started and approved',
            'activity': 'Activity shared by an explicitly authorized native app',
        }
        permissions = {key: key in selected_permissions for key in allowed_permissions}
        notifications_enabled = request.POST.get('child_notifications') == 'on'
        if accepted and permissions['presence']:
            device.consent_accepted = True
            device.consent_required = True
            device.visible_on_child = True
            device.hidden_on_child = False
            device.is_active = True
            device.last_seen = timezone.now()
            device.monitoring_permissions = permissions
            device.child_notifications_enabled = notifications_enabled
            device.save(update_fields=['consent_accepted', 'consent_required', 'visible_on_child', 'hidden_on_child', 'is_active', 'last_seen', 'monitoring_permissions', 'child_notifications_enabled'])
            return HttpResponseRedirect(f'/child/dashboard/{device.pairing_token}/')
        return render(request, 'child/consent.html', {'device': device, 'error': 'Accept the consent statement and device status permission to continue.'})

    return render(request, 'child/consent.html', {'device': device})


def child_dashboard_view(request, pairing_token):
    try:
        device = Device.objects.get(pairing_token=pairing_token)
    except Device.DoesNotExist:
        return HttpResponse('Pairing token not found', status=404)
    if not device.consent_accepted or not device.is_active:
        return HttpResponseRedirect(f'/child/consent/{device.pairing_token}/')
    device.last_seen = timezone.now()
    device.connection_status = 'Online'
    device.save(update_fields=['last_seen', 'connection_status'])
    return render(request, 'child/dashboard.html', {'device': device})


def _child_device(pairing_token):
    try:
        return Device.objects.get(pairing_token=pairing_token)
    except Device.DoesNotExist:
        return None


def child_status_api(request, pairing_token):
    device = _child_device(pairing_token)
    if device is None:
        return JsonResponse({'detail': 'Pairing token not found'}, status=404)
    return JsonResponse({
        'device': {
            'name': device.name,
            'device_id': device.device_id,
            'os': device.os,
            'battery': device.battery,
            'connection_status': device.connection_status,
            'consent_accepted': device.consent_accepted,
            'is_active': device.is_active,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        },
    })


@require_http_methods(['POST'])
def child_heartbeat_api(request, pairing_token):
    device = _child_device(pairing_token)
    if device is None:
        return JsonResponse({'detail': 'Pairing token not found'}, status=404)
    if not device.consent_accepted:
        return JsonResponse({'detail': 'Consent is required before monitoring can start.'}, status=403)
    if device.is_active:
        device.last_seen = timezone.now()
        device.connection_status = 'Online'
        device.save(update_fields=['last_seen', 'connection_status'])
    return JsonResponse({'ok': True, 'is_active': device.is_active})


@require_http_methods(['POST'])
def child_control_api(request, pairing_token):
    device = _child_device(pairing_token)
    if device is None:
        return JsonResponse({'detail': 'Pairing token not found'}, status=404)
    if not device.consent_accepted:
        return JsonResponse({'detail': 'Consent is required before monitoring can start.'}, status=403)
    action = request.POST.get('action')
    if action == 'disconnect':
        device.is_active = False
        device.connection_status = 'Disconnected'
    elif action == 'reconnect':
        device.is_active = True
        device.connection_status = 'Online'
        device.last_seen = timezone.now()
    else:
        return JsonResponse({'detail': 'Unknown device action.'}, status=400)
    device.save(update_fields=['is_active', 'connection_status', 'last_seen'])
    return JsonResponse({'ok': True, 'is_active': device.is_active, 'connection_status': device.connection_status})


@csrf_exempt
@require_http_methods(['POST'])
def companion_enroll_api(request):
    pairing_code = (request.POST.get('pairing_code') or '').strip().upper()
    companion_id = (request.POST.get('companion_id') or '').strip()
    if not pairing_code or not companion_id:
        return JsonResponse({'detail': 'Pairing code and companion id are required.'}, status=400)
    device = Device.objects.filter(pairing_code__iexact=pairing_code).first()
    if device is None:
        return JsonResponse({'detail': 'Pairing code not found.'}, status=404)
    if not device.consent_accepted or not device.is_active:
        return JsonResponse({'detail': 'The child must accept web consent before the Android companion can enroll.'}, status=403)
    device.companion_id = companion_id
    device.last_seen = timezone.now()
    device.connection_status = 'Online'
    device.save(update_fields=['companion_id', 'last_seen', 'connection_status'])
    return JsonResponse({
        'token': str(device.pairing_token),
        'device_id': device.device_id,
        'name': device.name,
        'permissions': device.monitoring_permissions,
    })


@csrf_exempt
@require_http_methods(['POST'])
def companion_heartbeat_api(request, pairing_token):
    device = _child_device(pairing_token)
    if device is None:
        return JsonResponse({'detail': 'Device token not found.'}, status=404)
    if not device.consent_accepted or not device.is_active:
        return JsonResponse({'detail': 'Monitoring is not active for this device.'}, status=403)
    companion_id = (request.POST.get('companion_id') or '').strip()
    if not companion_id or companion_id != device.companion_id:
        return JsonResponse({'detail': 'Companion is not enrolled for this device.'}, status=403)
    permission_status = request.POST.get('permissions') or '{}'
    try:
        permissions = json.loads(permission_status)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid permission status.'}, status=400)
    device.companion_permissions = permissions
    device.last_seen = timezone.now()
    device.connection_status = 'Online'
    device.save(update_fields=['companion_permissions', 'last_seen', 'connection_status'])
    return JsonResponse({'ok': True, 'is_active': device.is_active})


@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html')


@never_cache
def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None and username:
            User = get_user_model()
            matching_user = User.objects.filter(username__iexact=username, is_active=True).first()
            if matching_user:
                user = authenticate(request, username=matching_user.username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return HttpResponseRedirect('/')
        return render(request, 'login.html', {'error': 'Invalid admin credentials.'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')


def page_view(request, page_name):
    allowed = {
        'whatsapp': 'whatsapp.html',
        'sms': 'sms.html',
        'calls': 'calls.html',
        'recordings': 'recordings.html',
        'live-screen': 'live-screen.html',
        'devices': 'devices.html',
        'notifications': 'notifications.html',
        'settings': 'settings.html',
    }
    template = allowed.get(page_name)
    if not template:
        return HttpResponse('Page not found', status=404)
    return render(request, 'pages/' + template)


def manifest_view(request):
    return HttpResponse(open(os.path.join(os.getcwd(), 'manifest.json'), 'rb'), content_type='application/manifest+json')


def child_manifest_view(request, pairing_token):
    device = _child_device(pairing_token)
    if device is None:
        return JsonResponse({'detail': 'Pairing token not found'}, status=404)
    return JsonResponse({
        'name': f'Family Guard - {device.name}',
        'short_name': device.name[:12],
        'start_url': f'/child/dashboard/{device.pairing_token}/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#f7f8fa',
        'theme_color': '#ff982f',
        'icons': [
            {'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/static/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        ],
    }, content_type='application/manifest+json')


def service_worker_view(request):
    return HttpResponse(open(os.path.join(os.getcwd(), 'sw.js'), 'rb'), content_type='application/javascript')
