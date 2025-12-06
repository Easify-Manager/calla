# MedVoice: Voice-First Medication Adherence Platform

## Technical Documentation & Implementation Plan

---

## 1. Product Vision

**MedVoice** is a caregiver-centric medication management platform where patients interact primarily through AI-powered phone calls, not app interfaces. Caregivers manage everything through a web dashboard; patients simply answer the phone.

### Core Value Proposition
- **For Caregivers**: Single dashboard to manage medications for multiple patients, with AI handling all patient communication
- **For Patients**: Zero app learning curve — just answer phone calls from a friendly AI assistant
- **For Payers**: Higher adherence rates through unavoidable voice reminders + caregiver oversight

### Key Differentiators
1. **Voice-first patient interaction** — Phone calls have near-100% attention capture vs. 10% push notification open rates
2. **AI-powered onboarding** — Agent calls patient to collect routine info, no manual data entry
3. **Escalating call alerts** — Patient → Caregiver → Emergency contact chain
4. **Habit-aware scheduling** — Medications scheduled around patient's actual daily routine

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEDVOICE ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────────────┐
│                  │     │                  │     │                          │
│  CAREGIVER WEB   │────▶│   BACKEND API    │────▶│    VOICE AI SERVICE      │
│    DASHBOARD     │     │   (FastAPI)      │     │    (Vapi.ai / Twilio)    │
│                  │◀────│                  │◀────│                          │
└──────────────────┘     └────────┬─────────┘     └────────────┬─────────────┘
       │                          │                            │
       │                          ▼                            ▼
       │                 ┌──────────────────┐         ┌──────────────────┐
       │                 │                  │         │                  │
       │                 │    DATABASE      │         │   PATIENT PHONE  │
       │                 │   (Supabase)     │         │                  │
       │                 │                  │         └──────────────────┘
       │                 └──────────────────┘
       │                          │
       ▼                          ▼
┌──────────────────┐     ┌──────────────────┐
│  CAREGIVER APP   │     │   DRUG APIs      │
│  (optional PWA)  │     │ (RxNorm, OpenFDA)│
└──────────────────┘     └──────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose |
|-----------|------------|---------|
| Caregiver Dashboard | Next.js + Tailwind | Web interface for medication management |
| Backend API | FastAPI (Python) | Business logic, scheduling, API orchestration |
| Database | Supabase (Postgres) | Users, patients, medications, schedules, call logs |
| Voice AI | Vapi.ai | Conversational AI phone calls |
| LLM | Claude API / GPT-4 | Chatbot for prescription entry, call conversations |
| Drug Data | RxNorm + OpenFDA | Drug search, interactions, side effects |
| Scheduling | APScheduler / Celery | Trigger calls at scheduled times |
| SMS Fallback | Twilio | Text backup if call fails |

---

## 3. Database Schema

```sql
-- Core Tables

CREATE TABLE caregivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caregiver_id UUID REFERENCES caregivers(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    -- Daily routine (collected via AI call)
    wake_time TIME,
    sleep_time TIME,
    breakfast_time TIME,
    lunch_time TIME,
    dinner_time TIME,
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    voice_preference VARCHAR(50) DEFAULT 'friendly_female',
    call_retry_attempts INT DEFAULT 3,
    -- Status
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_call_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    -- Drug info
    drug_name VARCHAR(255) NOT NULL,
    rxcui VARCHAR(20),  -- RxNorm identifier
    dosage VARCHAR(100),
    dosage_form VARCHAR(100),  -- tablet, capsule, liquid, etc.
    -- Instructions
    frequency VARCHAR(50),  -- once_daily, twice_daily, three_times, as_needed
    timing_preference VARCHAR(50),  -- with_food, before_food, after_food, empty_stomach
    specific_times TIME[],  -- Array of scheduled times
    -- Additional
    prescribing_doctor VARCHAR(255),
    pharmacy VARCHAR(255),
    refill_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scheduled_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    medication_id UUID REFERENCES medications(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, calling, confirmed, missed, escalated
    attempt_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    caregiver_id UUID REFERENCES caregivers(id),
    call_type VARCHAR(50) NOT NULL,  -- onboarding, reminder, escalation, check_in
    call_provider_id VARCHAR(255),  -- Vapi call ID
    direction VARCHAR(20),  -- outbound, inbound
    status VARCHAR(20),  -- completed, no_answer, busy, failed
    duration_seconds INT,
    transcript TEXT,
    extracted_data JSONB,  -- Structured data extracted from call
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE adherence_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reminder_id UUID REFERENCES scheduled_reminders(id),
    medication_id UUID REFERENCES medications(id),
    patient_id UUID REFERENCES patients(id),
    scheduled_time TIMESTAMP,
    confirmed_time TIMESTAMP,
    confirmation_method VARCHAR(50),  -- voice_call, sms, manual
    was_taken BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_reminders_scheduled ON scheduled_reminders(scheduled_time, status);
CREATE INDEX idx_reminders_patient ON scheduled_reminders(patient_id);
CREATE INDEX idx_medications_patient ON medications(patient_id);
CREATE INDEX idx_adherence_patient ON adherence_events(patient_id, scheduled_time);
```

---

## 4. API Endpoints

### Authentication
```
POST /api/auth/register          - Caregiver registration
POST /api/auth/login             - Caregiver login
POST /api/auth/refresh           - Refresh JWT token
```

### Patients
```
GET    /api/patients             - List all patients for caregiver
POST   /api/patients             - Add new patient (triggers onboarding call)
GET    /api/patients/{id}        - Get patient details
PUT    /api/patients/{id}        - Update patient info
DELETE /api/patients/{id}        - Remove patient

POST   /api/patients/{id}/onboarding-call    - Trigger/retry onboarding call
GET    /api/patients/{id}/adherence-stats    - Get adherence statistics
```

### Medications
```
GET    /api/patients/{id}/medications        - List patient's medications
POST   /api/patients/{id}/medications        - Add medication (via chatbot)
GET    /api/medications/{id}                 - Get medication details
PUT    /api/medications/{id}                 - Update medication
DELETE /api/medications/{id}                 - Remove medication

POST   /api/medications/search               - Search drugs (RxNorm)
GET    /api/medications/{rxcui}/interactions - Check drug interactions
```

### Reminders & Calls
```
GET    /api/reminders/today                  - Today's scheduled reminders
GET    /api/reminders/upcoming               - Next 7 days reminders
POST   /api/reminders/{id}/mark-taken        - Manually mark as taken

GET    /api/calls/history                    - Call history
GET    /api/calls/{id}/transcript            - Get call transcript
```

### Chatbot
```
POST   /api/chat/prescription               - Chatbot for adding prescription
POST   /api/chat/message                    - Send message to chatbot
```

### Webhooks (from Vapi.ai)
```
POST   /api/webhooks/vapi/call-started      - Call initiated
POST   /api/webhooks/vapi/call-ended        - Call completed
POST   /api/webhooks/vapi/transcript        - Real-time transcript
```

---

## 5. Voice AI Agent Configurations

### 5.1 Patient Onboarding Agent

**Purpose**: Call new patient, collect personal info, medications, and daily routine.

```json
{
  "agent_name": "MedVoice Onboarding Assistant",
  "voice": "jennifer",
  "language": "en-US",
  "first_message": "Hello! This is MedVoice calling on behalf of {caregiver_name}, who has registered you for medication reminders. This call will take about 5 minutes. Is now a good time to chat?",
  
  "system_prompt": """
You are a friendly, patient healthcare assistant helping to set up medication reminders for an elderly patient. Your caregiver {caregiver_name} has asked you to collect some information.

Your goals:
1. Confirm the patient's name and basic info
2. Learn about their daily routine (wake up, meals, bedtime)
3. Collect information about their current medications
4. Explain how the reminder system works

Guidelines:
- Speak slowly and clearly
- Use simple language, avoid medical jargon
- Be patient with repetition - they may be elderly or have cognitive issues
- Confirm important details by repeating them back
- If they seem confused, offer to have their caregiver call them instead
- Keep the conversation warm and reassuring

Information to collect:
- Confirmation of full name
- Daily routine: What time do you usually wake up? Have breakfast? Lunch? Dinner? Go to bed?
- Current medications: What medications are you currently taking? How often? With food or without?
- Any allergies or concerns

At the end, summarize what you've learned and explain they'll receive friendly reminder calls when it's time to take their medications.
""",

  "extraction_schema": {
    "confirmed_name": "string",
    "wake_time": "time",
    "breakfast_time": "time", 
    "lunch_time": "time",
    "dinner_time": "time",
    "sleep_time": "time",
    "medications": [
      {
        "name": "string",
        "dosage": "string",
        "frequency": "string",
        "timing": "string",
        "with_food": "boolean"
      }
    ],
    "allergies": ["string"],
    "concerns": "string",
    "consent_given": "boolean"
  }
}
```

### 5.2 Medication Reminder Agent

**Purpose**: Call patient at scheduled time, confirm they took their medication.

```json
{
  "agent_name": "MedVoice Reminder Assistant",
  "voice": "jennifer",
  "language": "en-US",
  "first_message": "Hello {patient_name}! This is your MedVoice reminder. It's time to take your {medication_name}. Have you taken it yet?",
  
  "system_prompt": """
You are a friendly medication reminder assistant. Your job is to remind {patient_name} to take their {medication_name} ({dosage}).

Instructions for this medication: {instructions}

Your goals:
1. Remind them to take their medication
2. Confirm whether they've taken it
3. If not taken, encourage them to take it now
4. Log their response

Guidelines:
- Be warm and encouraging, not nagging
- If they say they already took it, thank them and confirm
- If they haven't taken it, gently remind them of the importance
- If they refuse or can't take it, ask if there's a reason (side effects, ran out, etc.)
- Keep the call brief - under 2 minutes ideally
- If they seem confused or distressed, offer to contact their caregiver

Possible responses to handle:
- "Yes, I took it" → Confirm and thank them
- "Not yet" → Encourage them to take it now, offer to wait
- "I don't want to" → Ask why, note the reason
- "I ran out" → Note this for caregiver, express understanding
- "What medication?" → Describe it clearly (color, shape if known)
""",

  "extraction_schema": {
    "medication_taken": "boolean",
    "taken_time": "string",
    "reason_not_taken": "string",
    "needs_refill": "boolean",
    "reported_side_effects": "string",
    "patient_mood": "string",
    "escalate_to_caregiver": "boolean"
  }
}
```

### 5.3 Caregiver Escalation Agent

**Purpose**: Alert caregiver when patient misses medication.

```json
{
  "agent_name": "MedVoice Alert",
  "voice": "davis",
  "language": "en-US",
  "first_message": "Hello {caregiver_name}, this is an alert from MedVoice about {patient_name}.",
  
  "system_prompt": """
You are calling to alert a caregiver about a missed medication or concern.

Alert type: {alert_type}
Patient: {patient_name}
Details: {alert_details}

Your goals:
1. Clearly communicate the alert
2. Provide relevant details
3. Ask if they can follow up with the patient
4. Offer to retry the patient call if requested

Keep this call brief and professional. The caregiver may be busy.
""",

  "extraction_schema": {
    "caregiver_acknowledged": "boolean",
    "will_follow_up": "boolean",
    "requested_retry": "boolean",
    "notes": "string"
  }
}
```

---

## 6. Core Flows

### 6.1 Add Patient Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Caregiver  │     │   Backend   │     │   Vapi.ai   │     │   Patient   │
│  Dashboard  │     │     API     │     │             │     │   Phone     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ POST /patients    │                   │                   │
       │ {name, phone}     │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │                   │ Create patient    │                   │
       │                   │ (onboarding:false)│                   │
       │                   │                   │                   │
       │                   │ Trigger call      │                   │
       │                   │──────────────────▶│                   │
       │                   │                   │                   │
       │                   │                   │ Outbound call     │
       │                   │                   │──────────────────▶│
       │                   │                   │                   │
       │                   │                   │   Conversation    │
       │                   │                   │◀─────────────────▶│
       │                   │                   │                   │
       │                   │ Webhook: call_ended                   │
       │                   │ + extracted_data  │                   │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │                   │ Update patient    │                   │
       │                   │ Create medications│                   │
       │                   │ Create schedule   │                   │
       │                   │                   │                   │
       │ Patient updated   │                   │                   │
       │ (via WebSocket)   │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
```

### 6.2 Medication Reminder Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Scheduler  │     │   Backend   │     │   Vapi.ai   │     │   Patient   │
│  (Celery)   │     │     API     │     │             │     │   Phone     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ Trigger: reminder │                   │                   │
       │ due in 1 min      │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │                   │ Initiate call     │                   │
       │                   │──────────────────▶│                   │
       │                   │                   │                   │
       │                   │                   │ Ring patient      │
       │                   │                   │──────────────────▶│
       │                   │                   │                   │
       │                   │                   │   "Did you take   │
       │                   │                   │    your Metformin?"
       │                   │                   │◀─────────────────▶│
       │                   │                   │                   │
       │                   │                   │   "Yes I did"     │
       │                   │                   │                   │
       │                   │ Webhook: confirmed│                   │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │                   │ Log adherence     │                   │
       │                   │ event (taken:true)│                   │
       │                   │                   │                   │
```

### 6.3 Escalation Flow (Missed Dose)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Backend   │     │   Vapi.ai   │     │   Patient   │     │  Caregiver  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ Call attempt 1    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │──────────────────▶│ No answer         │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │ Wait 15 min       │                   │                   │
       │ Call attempt 2    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │──────────────────▶│ No answer         │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │ Wait 15 min       │                   │                   │
       │ Call attempt 3    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │──────────────────▶│ No answer         │
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │ ESCALATE          │                   │                   │
       │ Call caregiver    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │──────────────────────────────────────▶│
       │                   │                   │                   │
       │                   │    "Patient missed medication,        │
       │                   │     3 call attempts failed"           │
       │                   │◀──────────────────────────────────────│
       │                   │                   │                   │
```

---

## 7. Chatbot for Adding Prescriptions

The prescription chatbot uses an LLM to have a natural conversation with the caregiver, extracting structured medication data.

### Chatbot System Prompt

```
You are a helpful assistant for adding medication prescriptions to MedVoice. 
You're chatting with a caregiver who wants to add a medication for their patient.

Your job:
1. Ask for the medication name (help them search if needed)
2. Confirm the dosage
3. Ask about frequency (once daily, twice daily, etc.)
4. Ask about timing (with food, before bed, etc.)
5. Ask about any special instructions
6. Summarize and confirm before saving

Be conversational and helpful. If they give partial information, ask follow-up questions.
If they mention a drug name, use the drug search function to find the exact medication and show them options.

When you have all required information, output a structured JSON at the end:
{
  "ready_to_save": true,
  "medication": {
    "drug_name": "...",
    "rxcui": "...",
    "dosage": "...",
    "frequency": "...",
    "timing_preference": "...",
    "specific_times": [...],
    "instructions": "..."
  }
}
```

### Example Conversation

```
Caregiver: I need to add metformin for my mom
Bot: I found Metformin! Let me help you set this up. 

I see a few options:
• Metformin 500mg tablet
• Metformin 850mg tablet  
• Metformin 1000mg tablet
• Metformin ER 500mg (extended release)

Which one does your mom take?

Caregiver: 500mg twice a day

Bot: Got it - Metformin 500mg, twice daily. 

Does she need to take it with food, or does it matter?

Caregiver: With breakfast and dinner

Bot: Perfect! So I'll schedule reminders for:
• Morning dose: around breakfast time
• Evening dose: around dinner time

Based on her routine (breakfast at 8am, dinner at 6pm), I'll set reminders for 8:00 AM and 6:00 PM.

Any special instructions? For example, "take with a full glass of water" or "avoid alcohol"?

Caregiver: No that's it

Bot: Great! Here's what I have:

**Metformin 500mg**
• Twice daily (with breakfast and dinner)
• Reminder times: 8:00 AM and 6:00 PM
• Take with food

Should I add this medication?

Caregiver: Yes

Bot: ✓ Metformin has been added! Your mom will start receiving reminder calls at her next scheduled time.
```

---

## 8. Tech Stack Details

### Frontend (Caregiver Dashboard)

```bash
# Create Next.js project
npx create-next-app@latest medvoice-dashboard --typescript --tailwind --app

# Key dependencies
npm install @supabase/supabase-js     # Database client
npm install @tanstack/react-query      # Data fetching
npm install zustand                    # State management
npm install react-hook-form            # Forms
npm install zod                        # Validation
npm install lucide-react               # Icons
npm install date-fns                   # Date handling
npm install recharts                   # Charts for adherence stats
```

### Backend (FastAPI)

```bash
# Create Python environment
python -m venv venv
source venv/bin/activate

# Key dependencies
pip install fastapi
pip install uvicorn
pip install supabase
pip install python-jose[cryptography]  # JWT auth
pip install passlib[bcrypt]            # Password hashing
pip install httpx                       # HTTP client for APIs
pip install apscheduler                 # Job scheduling
pip install openai                      # or anthropic for Claude
pip install python-dotenv
pip install pydantic
```

### Project Structure

```
medvoice/
├── frontend/                    # Next.js Dashboard
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/
│   │   │   ├── patients/
│   │   │   │   ├── page.tsx           # Patient list
│   │   │   │   ├── [id]/page.tsx      # Patient detail
│   │   │   │   └── add/page.tsx       # Add patient
│   │   │   ├── medications/
│   │   │   ├── calendar/
│   │   │   ├── calls/
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/                        # Shadcn components
│   │   ├── patient-card.tsx
│   │   ├── medication-list.tsx
│   │   ├── prescription-chatbot.tsx   # LLM chatbot UI
│   │   ├── calendar-view.tsx
│   │   └── adherence-chart.tsx
│   └── lib/
│       ├── supabase.ts
│       ├── api.ts
│       └── utils.ts
│
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   ├── config.py                  # Settings
│   │   ├── database.py                # Supabase client
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── utils.py
│   │   ├── patients/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── medications/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── voice/
│   │   │   ├── router.py              # Vapi webhooks
│   │   │   ├── agents.py              # Agent configurations
│   │   │   └── service.py             # Call triggering
│   │   ├── chat/
│   │   │   ├── router.py
│   │   │   └── service.py             # LLM prescription chatbot
│   │   ├── scheduler/
│   │   │   └── jobs.py                # Scheduled reminder jobs
│   │   └── external/
│   │       ├── rxnorm.py              # RxNorm API client
│   │       ├── openfda.py             # OpenFDA API client
│   │       └── vapi.py                # Vapi.ai API client
│   ├── requirements.txt
│   └── Dockerfile
│
└── docker-compose.yml
```

---

## 9. Vapi.ai Integration

### Setup

```python
# backend/app/external/vapi.py

import httpx
from app.config import settings

VAPI_BASE_URL = "https://api.vapi.ai"

class VapiClient:
    def __init__(self):
        self.api_key = settings.VAPI_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_call(
        self,
        phone_number: str,
        assistant_id: str,
        assistant_overrides: dict = None
    ):
        """Initiate an outbound call"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VAPI_BASE_URL}/call/phone",
                headers=self.headers,
                json={
                    "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
                    "assistantId": assistant_id,
                    "assistantOverrides": assistant_overrides or {},
                    "customer": {
                        "number": phone_number
                    }
                }
            )
            return response.json()
    
    async def create_assistant(self, config: dict):
        """Create a new voice assistant"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VAPI_BASE_URL}/assistant",
                headers=self.headers,
                json=config
            )
            return response.json()
```

### Webhook Handler

```python
# backend/app/voice/router.py

from fastapi import APIRouter, Request, HTTPException
from app.voice.service import VoiceService
from app.database import supabase

router = APIRouter(prefix="/webhooks/vapi", tags=["webhooks"])

@router.post("/call-ended")
async def handle_call_ended(request: Request):
    """Process completed call and extract data"""
    payload = await request.json()
    
    call_id = payload.get("call", {}).get("id")
    call_type = payload.get("call", {}).get("metadata", {}).get("call_type")
    status = payload.get("call", {}).get("status")
    transcript = payload.get("transcript")
    analysis = payload.get("analysis")  # Extracted structured data
    
    # Log the call
    await supabase.table("call_logs").insert({
        "call_provider_id": call_id,
        "call_type": call_type,
        "status": status,
        "transcript": transcript,
        "extracted_data": analysis
    }).execute()
    
    # Handle based on call type
    if call_type == "onboarding":
        await VoiceService.process_onboarding_results(
            patient_id=payload["call"]["metadata"]["patient_id"],
            extracted_data=analysis
        )
    
    elif call_type == "reminder":
        await VoiceService.process_reminder_results(
            reminder_id=payload["call"]["metadata"]["reminder_id"],
            medication_taken=analysis.get("medication_taken", False),
            extracted_data=analysis
        )
    
    return {"status": "ok"}
```

---

## 10. Scheduler Implementation

```python
# backend/app/scheduler/jobs.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app.database import supabase
from app.voice.service import VoiceService

scheduler = AsyncIOScheduler()

async def check_pending_reminders():
    """Check for reminders due in the next minute and trigger calls"""
    now = datetime.utcnow()
    window_end = now + timedelta(minutes=1)
    
    # Get pending reminders
    result = await supabase.table("scheduled_reminders")\
        .select("*, medications(*), patients(*)")\
        .eq("status", "pending")\
        .gte("scheduled_time", now.isoformat())\
        .lte("scheduled_time", window_end.isoformat())\
        .execute()
    
    for reminder in result.data:
        # Trigger the reminder call
        await VoiceService.trigger_reminder_call(
            reminder_id=reminder["id"],
            patient=reminder["patients"],
            medication=reminder["medications"]
        )
        
        # Update status
        await supabase.table("scheduled_reminders")\
            .update({"status": "calling"})\
            .eq("id", reminder["id"])\
            .execute()

async def check_missed_reminders():
    """Check for reminders that weren't confirmed and escalate"""
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    
    # Get reminders that are still "calling" after 30 min
    result = await supabase.table("scheduled_reminders")\
        .select("*, medications(*), patients(*, caregivers(*))")\
        .eq("status", "calling")\
        .lt("scheduled_time", cutoff.isoformat())\
        .execute()
    
    for reminder in result.data:
        if reminder["attempt_count"] >= 3:
            # Escalate to caregiver
            await VoiceService.trigger_escalation_call(
                caregiver=reminder["patients"]["caregivers"],
                patient=reminder["patients"],
                medication=reminder["medications"],
                reason="missed_dose"
            )
            
            await supabase.table("scheduled_reminders")\
                .update({"status": "escalated"})\
                .eq("id", reminder["id"])\
                .execute()
        else:
            # Retry the call
            await VoiceService.trigger_reminder_call(
                reminder_id=reminder["id"],
                patient=reminder["patients"],
                medication=reminder["medications"]
            )
            
            await supabase.table("scheduled_reminders")\
                .update({"attempt_count": reminder["attempt_count"] + 1})\
                .eq("id", reminder["id"])\
                .execute()

def start_scheduler():
    """Initialize and start the scheduler"""
    # Check for due reminders every minute
    scheduler.add_job(
        check_pending_reminders,
        CronTrigger(minute="*"),
        id="check_reminders",
        replace_existing=True
    )
    
    # Check for missed reminders every 5 minutes
    scheduler.add_job(
        check_missed_reminders,
        CronTrigger(minute="*/5"),
        id="check_missed",
        replace_existing=True
    )
    
    scheduler.start()
```

---

## 11. Environment Variables

```bash
# .env

# Database
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Voice AI (Vapi.ai)
VAPI_API_KEY=your_vapi_api_key
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id
VAPI_ONBOARDING_ASSISTANT_ID=assistant_xxx
VAPI_REMINDER_ASSISTANT_ID=assistant_yyy
VAPI_ESCALATION_ASSISTANT_ID=assistant_zzz

# LLM (for prescription chatbot)
OPENAI_API_KEY=your_openai_key
# or
ANTHROPIC_API_KEY=your_anthropic_key

# Drug APIs
OPENFDA_API_KEY=your_openfda_key  # Optional, increases rate limit

# Twilio (SMS fallback)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 12. 36-Hour Implementation Timeline

### Phase 1: Foundation (Hours 1-8)

**Hour 1-2: Project Setup**
- [ ] Create GitHub repo
- [ ] Initialize Next.js frontend with Tailwind
- [ ] Initialize FastAPI backend
- [ ] Set up Supabase project and create tables
- [ ] Configure environment variables

**Hour 3-4: Authentication**
- [ ] Implement caregiver registration/login (Supabase Auth)
- [ ] Create login/register pages
- [ ] Set up protected routes

**Hour 5-8: Core Dashboard**
- [ ] Patient list page (CRUD)
- [ ] Basic medication list component
- [ ] Simple calendar view (just display)

### Phase 2: Voice Integration (Hours 9-18)

**Hour 9-12: Vapi.ai Setup**
- [ ] Create Vapi.ai account and get API keys
- [ ] Purchase/configure phone number
- [ ] Create Onboarding Assistant with prompt
- [ ] Create Reminder Assistant with prompt
- [ ] Test calls manually

**Hour 13-16: Call Integration**
- [ ] Implement Vapi client in backend
- [ ] Add "Add Patient" flow → triggers onboarding call
- [ ] Implement webhook handlers for call results
- [ ] Store call transcripts and extracted data

**Hour 17-18: Onboarding Call Flow**
- [ ] Process onboarding call results
- [ ] Auto-populate patient routine times
- [ ] Auto-create medications from extracted data
- [ ] Show call status in dashboard

### Phase 3: Reminder System (Hours 19-26)

**Hour 19-22: Scheduling**
- [ ] Implement APScheduler
- [ ] Create scheduled_reminders from medications
- [ ] Trigger reminder calls at scheduled times
- [ ] Handle call results (taken/not taken)

**Hour 23-26: Escalation**
- [ ] Implement retry logic (3 attempts)
- [ ] Create escalation call to caregiver
- [ ] Log adherence events
- [ ] Show adherence status in dashboard

### Phase 4: Chatbot & Polish (Hours 27-32)

**Hour 27-29: Prescription Chatbot**
- [ ] Implement LLM chat endpoint
- [ ] Create chatbot UI component
- [ ] Integrate RxNorm drug search
- [ ] Parse structured medication data from chat

**Hour 30-32: Polish**
- [ ] Adherence statistics/charts
- [ ] Call history page
- [ ] Transcript viewer
- [ ] Error handling and loading states

### Phase 5: Demo Prep (Hours 33-36)

**Hour 33-34: Demo Data**
- [ ] Create demo caregiver account
- [ ] Add 2-3 demo patients with medications
- [ ] Generate sample call logs and adherence data
- [ ] Ensure all flows work end-to-end

**Hour 35-36: Presentation**
- [ ] Record backup demo video
- [ ] Prepare pitch slides
- [ ] Practice 3-minute pitch
- [ ] Prepare for Q&A

---

## 13. Pitch Deck Outline

### Slide 1: Hook
*"Every 19 minutes, someone dies from medication non-adherence. That's 125,000 preventable deaths per year."*

### Slide 2: Problem
- 50% of patients don't take medications as prescribed
- $300 billion annual cost to healthcare system
- 63 million caregivers managing medications with zero training
- Current apps have 4% retention at 30 days

### Slide 3: Why Apps Fail
- Push notifications: 10% open rate, easily dismissed
- Complex interfaces confuse elderly/cognitively impaired
- Designed for self-managing patients, not caregivers
- Alert fatigue leads to disabled notifications

### Slide 4: Solution - MedVoice
*"Phone calls, not push notifications"*
- AI voice calls are impossible to ignore
- Patients just answer the phone - zero app learning
- Caregivers manage everything from a dashboard
- Intelligent escalation when doses are missed

### Slide 5: Live Demo
- Show dashboard
- Trigger a reminder call (to your own phone)
- Show call transcript appearing in real-time
- Show adherence tracking

### Slide 6: Technology
- Voice AI (Vapi.ai) for natural conversations
- LLM-powered onboarding and prescription entry
- Habit-aware scheduling around patient routines
- Automatic drug interaction checking

### Slide 7: Business Model
- B2B to Medicare Advantage plans
- Medication adherence = 3x weighted Star Rating measures
- Each Star improvement = $350/member/year in bonuses
- Target: $5-15 PMPM for high-risk populations

### Slide 8: Market
- $5B medication adherence market → $12B by 2034
- 63M caregivers (growing 45%)
- 6.7M Alzheimer's patients (prime use case)
- Proven exits: Livongo ($18.5B), PillPack ($753M)

### Slide 9: Team
[Your team members and relevant experience]

### Slide 10: Ask
*"We're seeking pilot partnerships with Medicare Advantage plans to validate our 40%+ adherence improvement hypothesis."*

---

## 14. Key Demo Script

**Setup**: Have two phones ready - one as "patient", one as "caregiver"

1. **[Dashboard]** "This is the caregiver dashboard. I manage medications for my elderly mother."

2. **[Add Patient]** "When I add a patient, I just enter their phone number. Our AI calls them to learn their routine."

3. **[Trigger Call]** "Let me show you - I'll add myself as a patient." *[Enter your patient phone number]*

4. **[Answer Call on Patient Phone]** "Hello! This is MedVoice..." *[Have brief conversation, let it collect routine info]*

5. **[Show Dashboard Update]** "Now watch - the system automatically populated her routine and medications from that call."

6. **[Trigger Reminder]** "Now it's time for a medication reminder." *[Trigger reminder call]*

7. **[Patient Phone Rings]** "The patient's phone rings - not a notification they can ignore, an actual call."

8. **[Confirm Medication]** *[Answer, confirm medication]*

9. **[Show Adherence Log]** "And the caregiver sees it was confirmed, logged automatically."

10. **[Escalation]** "If she doesn't answer after 3 attempts, I get an alert call as her caregiver."

---

## 15. Fallback Options

If Vapi.ai has issues or you need alternatives:

| Service | Pros | Cons |
|---------|------|------|
| **Vapi.ai** | Best LLM integration, easy setup | Newer service |
| **Retell.ai** | Good voice quality | Similar to Vapi |
| **Bland.ai** | Simple API | Less customizable |
| **Twilio + OpenAI** | Most reliable | More setup work |

### Twilio + OpenAI Fallback

```python
# Simpler fallback using Twilio Voice + OpenAI TTS/STT

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

@router.post("/twilio/voice")
async def handle_twilio_voice(request: Request):
    """Handle incoming Twilio voice webhook"""
    response = VoiceResponse()
    
    gather = Gather(
        input="speech",
        action="/api/webhooks/twilio/process-speech",
        speech_timeout="auto",
        language="en-US"
    )
    gather.say(
        "Hello! This is your medication reminder. "
        "Have you taken your Metformin? Please say yes or no.",
        voice="Polly.Joanna"
    )
    response.append(gather)
    
    return Response(content=str(response), media_type="application/xml")
```

---

## Quick Start Commands

```bash
# Clone and setup
git clone <your-repo>
cd medvoice

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your keys
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local  # Fill in your keys
npm run dev

# Open http://localhost:3000
```

---

**Good luck at the hackathon! 🚀**

The key to winning: **Get the phone call demo working.** When judges see an actual AI call come through on a real phone, that's the "wow moment" that wins hackathons. Everything else is supporting that demo.
