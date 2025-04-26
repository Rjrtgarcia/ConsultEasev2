# Technical Context
*Last updated: {{DATE}}*

## Core Stack
### Raspberry Pi Central System
- OS: Raspberry Pi OS Bookworm (Debian 12)
- Runtime: Python 3.11.4
- Database: Firebase Realtime Database + Admin SDK 6.2.0
- UI: PyQt6 6.6.0 (Qt 6.6)
- Comm Protocol: Paho-MQTT 1.6.1
- Display: 10.1" 1024x600 Touchscreen
- Input: Squeekboard On-Screen Keyboard

### ESP32 Faculty Unit
- Framework: Arduino Core 2.0.9
- Firebase: Firebase-ESP-Client 1.2.2
- BLE: NimBLE 1.4.3

## Firebase Configuration
- Project ID: consultease-prod
- Database URL: https://consultease-prod.firebaseio.com
- Region: asia-southeast1
- Service Account: consultease-service-account.json

## Security Rules
```json
{
  "rules": {
    "faculty": {
      ".read": "auth != null",
      ".write": "auth.token.admin === true"
    },
    "sessions": {
      ".read": "auth != null",
      ".write": "auth.token.admin === true"
    }
  }
}
```

## Python Requirements
```python
firebase-admin==6.2.0
pyrebase4==4.6.1
google-cloud-firestore==2.11.1
python-dotenv==0.21.1
PyQt6==6.6.0
```

## System Requirements
```bash
# Install Squeekboard for on-screen keyboard
sudo apt-get install squeekboard onboard -y
```

## ESP32 Libraries
```arduino
Firebase-ESP-Client @ 1.2.2
NimBLE-Arduino @ 1.4.3
PubSubClient @ 2.8.2
```

## Environment Setup
```bash
# Firebase initialization
firebase login
firebase init database
firebase deploy --only database
```

## Touchscreen Configuration
```bash
# Add to /boot/config.txt for touchscreen
hdmi_cvt=1024 600 60 6 0 0 0
hdmi_group=2
hdmi_mode=87
hdmi_drive=1
```

// File version: 1.2-touchscreen
