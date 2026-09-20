# Family Guard Android Companion

This is a transparent Android permission-onboarding foundation for the consented child device.

## What it does

- Shows a disclosure and requires a local consent checkbox before any request.
- Uses Android permission prompts for notifications, SMS, and call-related permissions.
- Opens Android's App Usage Access settings for the user to enable manually.
- Uses Android's MediaProjection chooser for visible screen-sharing permission.
- Explains that WhatsApp content has no ordinary Android permission and is not scraped.

## Important platform limits

- SMS permissions may be restricted by Google Play policy and may require the app to be the default SMS handler for some use cases.
- Call-log permissions are also restricted and require a permitted core purpose and Play-compliant disclosure.
- App usage access is a special Settings permission, not a normal runtime dialog.
- Screen sharing is session-based and must be approved through Android's system picker.
- This project does not collect, upload, or hide personal content. A future backend connector must preserve the same explicit consent and revocation model.

Open `android-companion` in Android Studio, review the manifest declarations, and build the debug APK from there.