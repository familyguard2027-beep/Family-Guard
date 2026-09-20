from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from monitor import views as monitor_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', monitor_views.index, name='index'),
    path('login/', monitor_views.login_view, name='login'),
    path('logout/', monitor_views.logout_view, name='logout'),
    path('dashboard/', monitor_views.index, name='dashboard'),
    path('pages/<str:page_name>/', monitor_views.page_view, name='page_view'),
    path('child/consent/<uuid:pairing_token>/', monitor_views.child_consent_view, name='child_consent'),
    path('child/dashboard/<uuid:pairing_token>/', monitor_views.child_dashboard_view, name='child_dashboard'),
    path('api/', include('monitor.urls')),
    path('manifest.json', monitor_views.manifest_view, name='manifest'),
    path('child/manifest/<uuid:pairing_token>.json', monitor_views.child_manifest_view, name='child_manifest'),
    path('sw.js', monitor_views.service_worker_view, name='sw'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
