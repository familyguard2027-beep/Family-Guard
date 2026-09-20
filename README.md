# Device Monitor Admin Frontend

Static HTML/Bootstrap prototype organized for later Laravel/API integration.

## Pages
- Dashboard: ../index.html
- WhatsApp
- SMS
- Calls
- Call Recordings
- Live Screen
- Devices
- Notifications
- Settings

## Structure
assets/css/app.css  - shared styling
assets/js/app.js    - shared shell, navigation, device selector, modal
pages/               - feature pages

## Integration
The UI currently uses demo data. Replace page data with Laravel Blade/API responses later.
Suggested API resources:
GET /api/devices
GET /api/devices/{device}
GET /api/whatsapp/messages
GET /api/sms
GET /api/calls
GET /api/call-recordings
GET /api/notifications

Keep screen sharing and data collection restricted to appropriately authorized devices and platform-supported permissions.
