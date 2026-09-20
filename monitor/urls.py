from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('dashboard/', views.dashboard_api, name='dashboard_api'),
    path('devices/', views.devices_api, name='devices_api'),
    path('devices/<str:device_id>/', views.device_detail_api, name='device_detail_api'),
    path('whatsapp/', views.whatsapp_api, name='whatsapp_api'),
    path('sms/', views.sms_api, name='sms_api'),
    path('calls/', views.calls_api, name='calls_api'),
    path('recordings/', views.recordings_api, name='recordings_api'),
    path('notifications/', views.notifications_api, name='notifications_api'),
    path('timeline/', views.timeline_api, name='timeline_api'),
    path('profile/', views.profile_api, name='profile_api'),
    path('pairing-code/', views.pairing_code_api, name='pairing-code'),
    path('bind-device/', views.bind_device, name='bind-device'),
    path('child/<uuid:pairing_token>/status/', views.child_status_api, name='child-status'),
    path('child/<uuid:pairing_token>/heartbeat/', views.child_heartbeat_api, name='child-heartbeat'),
    path('child/<uuid:pairing_token>/control/', views.child_control_api, name='child-control'),
]
