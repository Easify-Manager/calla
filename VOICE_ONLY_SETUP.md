# Calla Platform - Voice-Only Setup Guide

## Overview

The Calla platform has been refactored to use a **voice-only** interface for patients. Patients no longer need to install a mobile app - they receive medication reminders via automated phone calls powered by Twilio.

### New User Journey

1. **Caregiver** → Uses web dashboard to:
   - Add patients (name + phone number)
   - Add prescriptions with schedules
   - Receive alerts when patients don't respond

2. **Patient** → Receives phone calls:
   - Gets called at medication times
   - Presses 1 to confirm, or 2 for "call me later"
   - No app installation required

3. **Backend** → Handles retry logic:
   - Calls patient up to 3 times
   - 3-minute intervals between attempts
   - Alerts caregiver if patient doesn't respond after 3 attempts

## Architecture Changes

### What Was Removed
- ❌ Flutter patient mobile app (`patient_app/` directory)
- ❌ Firebase push notifications dependency
- ❌ Device token registration endpoints
- ❌ WebSocket-based Gemini Live voice streaming

### What Was Added
- ✅ Twilio voice calling integration
- ✅ Retry logic with 3-minute intervals
- ✅ Caregiver alerting via phone calls
- ✅ Phone number-based patient identification

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Required: Gemini API Key (for chatbot only now)
GEMINI_API_KEY=your_gemini_api_key_here

# Required: Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Optional
JWT_SECRET=your-secret-key-change-in-production
```

**Get Twilio credentials:**
1. Sign up at https://console.twilio.com/
2. Get a phone number with voice capabilities
3. Copy Account SID and Auth Token from dashboard

**Important:** Make sure your Twilio phone number supports **Media Streams** for real-time audio (required for Gemini Live integration)

### 3. Run Database Migration

Apply the schema change for retry tracking:

```bash
psql -U medvoice -d medvoice -f backend/add_last_attempt_time_migration.sql
```

Or manually:
```sql
ALTER TABLE scheduled_reminders
ADD COLUMN IF NOT EXISTS last_attempt_time TIMESTAMP WITH TIME ZONE;
```

### 4. Start the Application

**Using Docker:**
```bash
docker-compose up -d
```

**Or manually:**
```bash
# Terminal 1 - PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_DB=medvoice -e POSTGRES_USER=medvoice -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine

# Terminal 2 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend
cd frontend
npm run dev
```

### 5. Configure Twilio for Media Streams

**For local testing:**
```bash
ngrok http 8000
# Note the ngrok URL (e.g., https://abc123.ngrok.io)
```

**Twilio Configuration:**
- Twilio will automatically connect to your WebSocket endpoint at:
  ```
  wss://your-backend-url.com/api/voice/twilio/stream
  ```
- No manual webhook configuration needed! The TwiML in the code handles it.

> **Note:** For production, ensure your backend is deployed with a public `wss://` URL (secure WebSocket)

## How It Works

### Medication Reminder Flow

```
1. Caregiver adds medication with schedule (e.g., 8:00 AM, 8:00 PM)
   ↓
2. Scheduler creates daily reminders at midnight
   ↓
3. At scheduled time (8:00 AM):
   - Scheduler triggers Twilio call to patient
   - Patient answers phone
   - Gemini AI has natural conversation:
     "Hello [name], it's time to take your [medication]. Have you taken it yet?"
   - Patient responds naturally:
     ✓ "Yes, I took it" / "Already did" / "Of course"
     ❌ "Not yet" / "I need more time" / "I forgot"
   ↓
4. If patient confirms (natural language):
   - ✓ Gemini understands confirmation
   - ✓ Reminder marked as "confirmed"
   - ✓ Adherence event logged with transcript
   - ✓ Call ends
   ↓
5. If patient doesn't answer or hasn't taken it:
   - Wait 3 minutes
   - Retry (attempt 2 of 3)
   - Wait 3 minutes
   - Retry (attempt 3 of 3)
   ↓
6. If all 3 attempts fail:
   - Mark as "escalated"
   - Log missed dose
   - Call caregiver to alert them
```

### Scheduler Jobs

Three cron jobs run continuously:

| Job | Frequency | Purpose |
|-----|-----------|---------|
| `check_pending_reminders` | Every 1 minute | Triggers calls for reminders due in next 60 seconds |
| `check_missed_reminders` | Every 5 minutes | Handles retries (3-min intervals) and escalation |
| `generate_daily_reminders` | Daily at midnight | Creates next day's reminders from medications |

### Database Schema

**Key Models:**

```python
Patient
├── phone_number (required)
├── full_name
└── caregiver_id

Medication
├── drug_name
├── dosage
├── specific_times: ["08:00", "20:00"]
└── patient_id

ScheduledReminder
├── scheduled_time
├── status: pending → calling → confirmed/escalated
├── attempt_count: 0-3
├── last_attempt_time (for 3-minute intervals)
└── medication_id, patient_id
```

## API Endpoints

### For Caregivers (Web Dashboard)

```
POST   /api/auth/register         # Create caregiver account
POST   /api/auth/login            # Login
GET    /api/patients              # List patients
POST   /api/patients              # Add patient (name + phone)
POST   /api/medications           # Add medication with schedule
GET    /api/medications/patient/{id}  # View patient's medications
GET    /api/voice/sessions        # View call history
```

### For Twilio (Webhooks)

```
POST   /api/voice/twilio/callback     # Handle patient keypress (1 or 2)
POST   /api/voice/twilio/status       # Track call status (answered, missed, etc.)
```

## Testing the System

### 1. Add a Test Patient

```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Patient",
    "phone_number": "+1234567890"
  }'
```

### 2. Add a Test Medication

```bash
curl -X POST http://localhost:8000/api/medications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid",
    "drug_name": "Aspirin",
    "dosage": "81mg",
    "specific_times": ["14:30"]  # Set to current time + 2 minutes for testing
  }'
```

### 3. Wait for Call

- Scheduler will trigger call at the specified time
- Answer the call
- Press 1 to confirm or 2 to request retry
- Check logs to see retry logic in action

### 4. Test Natural Language

- Answer the call
- When Gemini asks if you've taken your medication, try:
  - "Yes, I took it"
  - "Of course"
  - "Already did"
  - "Not yet" (should retry)
  - "I need more time" (should retry)

### 5. Test Escalation

- Don't answer any of the 3 calls
- After 9 minutes (3 attempts × 3-minute intervals), caregiver will receive an alert call

## Troubleshooting

### "No phone number" errors
- Make sure patient has a valid phone number in database
- Phone number must include country code (e.g., +1234567890)

### Calls not triggering
- Check scheduler is running: Look for "Scheduler started with Twilio voice call reminder jobs" in logs
- Verify Twilio credentials in environment variables
- Check `scheduled_reminders` table has pending reminders

### Retries not working
- Verify `last_attempt_time` column exists in database
- Check `check_missed_reminders` job is running every 5 minutes
- Look for "Retrying reminder" messages in logs

### Caregiver not receiving alerts
- Ensure caregiver has phone_number set in database
- Check Twilio logs in console for failed calls
- Verify backend URL is accessible from Twilio (use ngrok for local testing)

## Future Enhancements

Potential improvements for the voice-only system:

1. **SMS Fallback** - Send SMS if calls fail
2. **Multi-language Support** - Configure voice language per patient
3. **Custom Voice Messages** - Let caregivers record personalized messages
4. **Smart Scheduling** - Learn patient's preferred call times
5. **Two-way Voice AI** - Use Gemini Live for natural conversations (if needed)

## Migrating from Old System

If you were using the Flutter app version:

1. **Patients**: No action needed - they'll start receiving calls instead of app notifications
2. **Caregivers**: Continue using web dashboard as before
3. **Database**: Run migration script to add `last_attempt_time` column
4. **Environment**: Add Twilio credentials to `.env`
5. **Code**: Pull latest changes and rebuild containers

## Support

For issues or questions:
- Check logs: `docker logs calla_backend`
- View Twilio call logs: https://console.twilio.com/logs
- Review scheduler jobs in code: `backend/app/scheduler/jobs.py`

---

**Last updated:** 2025-12-06
