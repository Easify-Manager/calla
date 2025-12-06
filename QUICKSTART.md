# Calla - Quick Start Guide

Complete guide to running the Calla platform locally.

## Overview

Calla consists of three main components:
1. **Backend** - FastAPI server with PostgreSQL (Python)
2. **Frontend** - Next.js caregiver dashboard (React/TypeScript)
3. **Patient App** - Flutter mobile app (Dart)

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Flutter SDK 3.0+ (for patient app)
- Firebase project (for patient app notifications)
- Gemini API key from https://aistudio.google.com/

---

## 1. Backend Setup

### Start Database
```bash
cd backend
docker-compose up -d
```

### Setup Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment
Create `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://medvoice:medvoice_secret@localhost:5432/medvoice
DATABASE_URL_SYNC=postgresql://medvoice:medvoice_secret@localhost:5432/medvoice
JWT_SECRET=your-secret-key-change-in-production
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini/gemini-2.0-flash
GEMINI_LIVE_MODEL=gemini-2.0-flash-exp
FRONTEND_URL=http://localhost:3000
```

### Run Backend
```bash
python run.py
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 2. Frontend Setup

### Install Dependencies
```bash
cd frontend
npm install
```

### Run Development Server
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## 3. Patient App Setup (Optional)

### Prerequisites
Install Flutter from https://docs.flutter.dev/get-started/install

Or if Flutter is already downloaded to ~/flutter:
```bash
export PATH="$PATH:$HOME/flutter/bin"
```

### Setup Firebase

1. Create a Firebase project at https://console.firebase.google.com/
2. Add Android app (package: `com.calla.patient_app`)
   - Download `google-services.json`
   - Place in `patient_app/android/app/`
3. Add iOS app (bundle ID: `com.calla.patientApp`)
   - Download `GoogleService-Info.plist`
   - Place in `patient_app/ios/Runner/`

### Configure Environment

Create `patient_app/.env`:
```env
# For Android Emulator
API_BASE_URL=http://10.0.2.2:8000
WS_BASE_URL=ws://10.0.2.2:8000

# For iOS Simulator
# API_BASE_URL=http://localhost:8000
# WS_BASE_URL=ws://localhost:8000

# For Physical Device (replace with your machine's IP)
# API_BASE_URL=http://192.168.1.X:8000
# WS_BASE_URL=ws://192.168.1.X:8000
```

### Install Dependencies & Run
```bash
cd patient_app
./setup.sh  # Or manually: flutter pub get

# Run on Android
flutter run -d android

# Run on iOS
flutter run -d ios
```

---

## Testing the Complete Flow

### 1. Create Caregiver Account

Open http://localhost:3000 and register a caregiver account.

### 2. Create Patient

Use the frontend dashboard or API:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Patient",
    "phone_number": "+1234567890",
    "password": "testpass123"
  }'
```

### 3. Login to Patient App

1. Open patient app on emulator/device
2. Login with patient credentials
3. Grant permissions (notifications, microphone)

### 4. Trigger a Call

From the caregiver dashboard:
- Navigate to the patient
- Click "Trigger Call" or "Start Reminder Call"

Or via API:
```bash
curl -X POST http://localhost:8000/api/patients/{patient_id}/trigger-call \
  -H "Authorization: Bearer YOUR_CAREGIVER_TOKEN"
```

### 5. Answer the Call

1. Patient app should show incoming call UI
2. Answer the call
3. Start speaking with the AI assistant
4. View transcript in real-time

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Caregiver Web  │     │                 │     │                 │
│    Dashboard    │────▶│   Backend API   │────▶│  Gemini Live    │
│  (localhost:    │     │   (FastAPI +    │◀────│     API         │
│    3000)        │     │   WebSocket)    │     │                 │
└─────────────────┘     │                 │     │                 │
                        │   PostgreSQL    │     │    LiteLLM      │
┌─────────────────┐     │   (Docker)      │     │                 │
│   Patient App   │◀───▶│                 │     │                 │
│   (Flutter)     │     └─────────────────┘     └─────────────────┘
└─────────────────┘          localhost:8000
```

---

## Common Issues

### Backend

**Database connection failed**
- Ensure Docker is running: `docker ps`
- Check PostgreSQL container: `docker-compose logs db`

**Gemini API errors**
- Verify API key is correct in `.env`
- Check quota at https://aistudio.google.com/

### Frontend

**API calls failing**
- Ensure backend is running on port 8000
- Check browser console for CORS errors

### Patient App

**Call UI not showing**
- Verify FCM token is registered (check backend logs)
- Ensure Firebase config files are in place
- Check notification permissions

**Audio not working**
- Grant microphone permissions
- Check WebSocket connection in app logs
- Ensure backend WebSocket endpoint is accessible

**Build errors**
```bash
flutter clean
flutter pub get
# For iOS
cd ios && pod install && cd ..
```

---

## Development Tips

### Hot Reload
- **Frontend**: Changes auto-reload in browser
- **Backend**: Restart `python run.py` for code changes
- **Patient App**: Press `r` in terminal for hot reload

### Logs
- **Backend**: Console output from `python run.py`
- **Frontend**: Browser console (F12)
- **Patient App**:
  - Android: `flutter logs` or `adb logcat`
  - iOS: `flutter logs` or Xcode console

### Database
Access PostgreSQL:
```bash
docker exec -it calla_postgres psql -U medvoice -d medvoice
```

View tables:
```sql
\dt
SELECT * FROM patients;
SELECT * FROM voice_sessions;
```

---

## Production Deployment

See individual README files:
- `/backend/README.md`
- `/frontend/README.md`
- `/patient_app/README.md`

---

## Getting Help

- Backend API Docs: http://localhost:8000/docs
- Check logs in each service
- Review error messages in browser/terminal
- Ensure all prerequisites are installed

---

**Happy Coding! 🚀**
