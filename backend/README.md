# Calla Backend

Voice-Only Medication Adherence Platform API using Twilio voice calls.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Caregiver Web  │     │                 │     │                 │
│    Dashboard    │────▶│   Backend API   │────▶│  Twilio Voice   │
└─────────────────┘     │   (FastAPI)     │◀────│     Calls       │
                        │                 │     │                 │
┌─────────────────┐     │   PostgreSQL    │     │    LiteLLM      │
│ Patient Phone   │◀────│   + Scheduler   │     │   (Chatbot)     │
│  (Voice Only)   │     └─────────────────┘     └─────────────────┘
└─────────────────┘
```

**New Architecture (Voice-Only):**
- ✅ Patients receive automated phone calls via Twilio
- ✅ No mobile app required
- ✅ 3 retry attempts with 3-minute intervals
- ✅ Automatic caregiver alerts on missed doses

## Tech Stack

- **FastAPI** - Python web framework
- **PostgreSQL** - Database (via Docker)
- **SQLAlchemy** - Async ORM
- **Twilio** - Voice calls to patients and caregivers
- **LiteLLM** - Unified LLM interface for chatbot
- **APScheduler** - Job scheduling for reminders and retries

## Quick Start

### 1. Start PostgreSQL

```bash
cd backend
docker-compose up -d
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://medvoice:medvoice_secret@localhost:5432/medvoice
DATABASE_URL_SYNC=postgresql://medvoice:medvoice_secret@localhost:5432/medvoice

# Authentication
JWT_SECRET=your-secret-key-change-in-production

# Gemini API (for chatbot only)
GEMINI_API_KEY=your_gemini_api_key

# LiteLLM model for chatbot
LLM_MODEL=gemini/gemini-2.0-flash

# Twilio (required - for voice calls)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Frontend
FRONTEND_URL=http://localhost:3000
```

### 5. Run the Server

```bash
python run.py
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register caregiver
- `POST /api/auth/login` - Login

### Patients
- `GET /api/patients` - List patients
- `POST /api/patients` - Create patient
- `POST /api/patients/{id}/trigger-call` - Trigger voice call

### Voice Calls (Twilio)
- `POST /api/voice/twilio/callback` - Handle patient response (webhook)
- `POST /api/voice/twilio/status` - Track call status (webhook)
- `GET /api/voice/sessions` - Call history

### Chatbot
- `POST /api/chat/prescription` - Add medications via chat

## Voice Call Flow (Twilio)

1. **Scheduler triggers reminder** → Runs every minute
2. **Backend calls Twilio API** → Initiates outbound call
3. **Patient answers phone** → Hears medication reminder
4. **Patient responds** → Presses 1 (confirmed) or 2 (need more time)
5. **Twilio webhook** → Sends response to backend
6. **Backend processes** → Updates reminder status, logs adherence
7. **Retry logic** → If not confirmed, retry after 3 minutes (up to 3 attempts)
8. **Escalation** → After 3 failed attempts, call caregiver to alert

## Twilio Setup

1. Sign up at https://console.twilio.com/
2. Get a phone number with voice capabilities
3. Copy Account SID, Auth Token, and Phone Number
4. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxx
   TWILIO_AUTH_TOKEN=xxxxx
   TWILIO_PHONE_NUMBER=+1234567890
   ```
5. Configure webhooks (see VOICE_ONLY_SETUP.md)

## Getting a Gemini API Key (for chatbot)

1. Go to https://aistudio.google.com/
2. Click "Get API Key"
3. Create and copy your API key
4. Add to `.env` as `GEMINI_API_KEY`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy
│   ├── models.py            # All models
│   ├── twilio_service.py    # Twilio voice calls
│   ├── auth/                # Authentication
│   ├── patients/            # Patient management
│   ├── medications/         # Medications & reminders
│   ├── voice/
│   │   └── router.py        # Twilio webhook endpoints
│   ├── chat/                # Prescription chatbot
│   ├── scheduler/           # Reminder jobs + retry logic
│   └── external/            # RxNorm API
├── docker-compose.yml
├── init.sql
├── requirements.txt
├── add_last_attempt_time_migration.sql
└── run.py

See VOICE_ONLY_SETUP.md for complete documentation.
```
