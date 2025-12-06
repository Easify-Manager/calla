# Calla Technical Documentation — Stack Changes

## Overview of Changes

| Original | New |
|----------|-----|
| Vapi.ai (telephony) | Gemini 2.0 Flash Live API + In-app call UI |
| Supabase | PostgreSQL + SQLAlchemy |
| OpenAI/Anthropic | Gemini via LiteLLM |
| Real phone calls | App-based "fake call" UX |

---

## 1. Architecture Changes

### Original Architecture
```
Caregiver Dashboard → Backend → Vapi.ai → Patient's Phone Number
```

### New Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Caregiver Web  │     │                 │     │                 │
│    Dashboard    │────▶│                 │     │                 │
└─────────────────┘     │                 │     │                 │
                        │   Backend API   │────▶│  Gemini Live    │
┌─────────────────┐     │   (FastAPI +    │◀────│     API         │
│   Patient App   │◀───▶│   WebSocket)    │     │                 │
│ (Flutter/React  │     │                 │     │                 │
│    Native)      │     │   PostgreSQL    │     │    LiteLLM      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Key difference**: Patient now needs the app installed. The app shows a "fake incoming call" screen that triggers a voice conversation with Gemini.

---

## 2. Database Changes

### Remove Supabase, Add SQLAlchemy + PostgreSQL

**Original dependencies:**
```bash
pip install supabase
```

**New dependencies:**
```bash
pip install sqlalchemy asyncpg psycopg2-binary alembic
```

### Database Connection

**Original (`database.py`):**
```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

**New (`database.py`):**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/calla"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### SQLAlchemy Models

**New file: `models.py`**
```python
from sqlalchemy import Column, String, DateTime, Boolean, Time, ForeignKey, Integer, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

class Caregiver(Base):
    __tablename__ = "caregivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patients = relationship("Patient", back_populates="caregiver")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="CASCADE"))
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)  # For SMS fallback only
    
    # Device token for push notifications (to trigger "call")
    device_token = Column(String(255))
    device_platform = Column(String(20))  # "ios" or "android"
    
    # Daily routine
    wake_time = Column(Time)
    sleep_time = Column(Time)
    breakfast_time = Column(Time)
    lunch_time = Column(Time)
    dinner_time = Column(Time)
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    voice_preference = Column(String(50), default="friendly_female")
    
    # Status
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    caregiver = relationship("Caregiver", back_populates="patients")
    medications = relationship("Medication", back_populates="patient")

class Medication(Base):
    __tablename__ = "medications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    
    drug_name = Column(String(255), nullable=False)
    rxcui = Column(String(20))
    dosage = Column(String(100))
    dosage_form = Column(String(100))
    frequency = Column(String(50))
    timing_preference = Column(String(50))
    specific_times = Column(ARRAY(Time))
    
    prescribing_doctor = Column(String(255))
    notes = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="medications")

class ScheduledReminder(Base):
    __tablename__ = "scheduled_reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class VoiceSession(Base):
    """Tracks active and completed voice sessions (replaces call_logs)"""
    __tablename__ = "voice_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id"))
    
    session_type = Column(String(50), nullable=False)  # onboarding, reminder, escalation
    status = Column(String(20), default="pending")  # pending, active, completed, missed
    
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    transcript = Column(String)
    extracted_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AdherenceEvent(Base):
    __tablename__ = "adherence_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_reminders.id"))
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    
    scheduled_time = Column(DateTime)
    confirmed_time = Column(DateTime)
    confirmation_method = Column(String(50))  # voice_session, manual
    was_taken = Column(Boolean)
    notes = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Query Pattern Changes

**Original (Supabase):**
```python
result = await supabase.table("patients").select("*").eq("caregiver_id", caregiver_id).execute()
patients = result.data
```

**New (SQLAlchemy):**
```python
from sqlalchemy import select
from app.models import Patient

async def get_patients(db: AsyncSession, caregiver_id: str):
    result = await db.execute(
        select(Patient).where(Patient.caregiver_id == caregiver_id)
    )
    return result.scalars().all()
```

**Original (Insert):**
```python
await supabase.table("patients").insert({"name": name, "phone": phone}).execute()
```

**New (Insert):**
```python
patient = Patient(full_name=name, phone_number=phone, caregiver_id=caregiver_id)
db.add(patient)
await db.commit()
await db.refresh(patient)
return patient
```

---

## 3. Voice System Changes (Vapi → Gemini Live)

### Remove Vapi, Add Gemini

**Original dependencies:**
```bash
# Vapi client (custom httpx calls)
pip install httpx
```

**New dependencies:**
```bash
pip install google-genai litellm
```

### Environment Variables

**Remove:**
```bash
VAPI_API_KEY=...
VAPI_PHONE_NUMBER_ID=...
VAPI_ONBOARDING_ASSISTANT_ID=...
VAPI_REMINDER_ASSISTANT_ID=...
```

**Add:**
```bash
GEMINI_API_KEY=your_gemini_api_key

# LiteLLM config (for chatbot, not voice)
LITELLM_MODEL=gemini/gemini-2.0-flash
```

### New Voice Service

**Delete:** `backend/app/external/vapi.py`

**Create:** `backend/app/voice/gemini_voice.py`

```python
from google import genai
from google.genai import types
import asyncio
import json

class GeminiVoiceService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp"
    
    async def create_voice_session(
        self,
        session_type: str,
        system_prompt: str,
        variables: dict = None
    ):
        """
        Create a voice session configuration.
        Returns session config to be used by the mobile app via WebSocket.
        """
        # Inject variables into system prompt
        if variables:
            for key, value in variables.items():
                system_prompt = system_prompt.replace(f"{{{{{key}}}}}", str(value))
        
        config = {
            "model": self.model,
            "system_instruction": system_prompt,
            "voice_config": {
                "voice_name": "Puck",  # Options: Puck, Charon, Kore, Fenrir, Aoede
            },
            "response_modalities": ["AUDIO", "TEXT"],
        }
        
        return config
    
    async def run_voice_session(
        self,
        config: dict,
        audio_input_queue: asyncio.Queue,
        audio_output_callback,
        on_transcript_update,
        on_session_end
    ):
        """
        Run a real-time voice session.
        This is called from the WebSocket handler that connects to the mobile app.
        """
        full_transcript = []
        extracted_data = {}
        
        async with self.client.aio.live.connect(
            model=config["model"],
            config=types.LiveConnectConfig(
                system_instruction=types.Content(
                    parts=[types.Part(text=config["system_instruction"])]
                ),
                voice=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=config["voice_config"]["voice_name"]
                    )
                ),
                response_modalities=config["response_modalities"]
            )
        ) as session:
            
            async def send_audio():
                """Send audio chunks from the user to Gemini"""
                while True:
                    audio_chunk = await audio_input_queue.get()
                    if audio_chunk is None:  # End signal
                        break
                    await session.send(
                        types.LiveClientRealtimeInput(
                            media_chunks=[
                                types.Blob(data=audio_chunk, mime_type="audio/pcm")
                            ]
                        )
                    )
            
            async def receive_audio():
                """Receive audio/text responses from Gemini"""
                async for response in session.receive():
                    # Handle audio response
                    if response.data:
                        await audio_output_callback(response.data)
                    
                    # Handle text (transcript)
                    if response.text:
                        full_transcript.append(response.text)
                        await on_transcript_update(response.text)
                    
                    # Handle tool calls / structured output
                    if response.tool_call:
                        # Process extraction
                        pass
            
            # Run send and receive concurrently
            await asyncio.gather(send_audio(), receive_audio())
        
        # Session ended
        await on_session_end(
            transcript="\n".join(full_transcript),
            extracted_data=extracted_data
        )


# Agent prompts (moved from Vapi configs)
AGENT_PROMPTS = {
    "onboarding": """
You are Calla, a friendly healthcare assistant helping to set up medication reminders. 
The caregiver {{caregiver_name}} has registered {{patient_name}} for medication reminders.

Your goals:
1. Greet warmly and confirm you're speaking with the right person
2. Learn about their daily routine (wake up, meals, bedtime)
3. Collect information about their current medications
4. Explain how reminder calls will work

Guidelines:
- Speak slowly and clearly
- Use simple language, avoid medical jargon
- Be patient with repetition
- Keep the conversation warm and reassuring
- Confirm important details by repeating them back

Start by introducing yourself and asking if now is a good time to chat for about 5 minutes.

At the end, summarize what you learned and tell them they'll receive friendly reminder calls.
""",
    
    "reminder": """
You are Calla, a friendly medication reminder assistant.
You're reminding {{patient_name}} to take their {{medication_name}} ({{dosage}}).

Instructions for this medication: {{instructions}}

Your goals:
1. Greet them warmly by name
2. Remind them it's time for their medication
3. Confirm whether they've taken it
4. If not taken, gently encourage them
5. Keep the call brief (under 2 minutes)

If they confirm they took it, thank them warmly.
If they haven't, encourage them to take it now.
If they refuse, ask if there's a reason (side effects, ran out, etc.)
If they seem confused, offer to have their caregiver call them.

Be warm and encouraging, never nagging.
""",
    
    "escalation": """
You are Calla, calling to alert a caregiver about a medication concern.

Alert type: {{alert_type}}
Patient: {{patient_name}}
Details: {{alert_details}}

Your goals:
1. Identify yourself and the purpose of the call
2. Clearly communicate the alert
3. Provide relevant details
4. Ask if they can follow up with the patient
5. Offer to retry contacting the patient if requested

Keep this call brief and professional.
"""
}
```

### WebSocket Handler for Voice Sessions

**Create:** `backend/app/voice/websocket_handler.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.voice.gemini_voice import GeminiVoiceService, AGENT_PROMPTS
from app.database import AsyncSessionLocal
from app.models import VoiceSession, Patient, ScheduledReminder, AdherenceEvent
import asyncio
import json
from datetime import datetime

voice_service = GeminiVoiceService(api_key=settings.GEMINI_API_KEY)

async def handle_voice_websocket(
    websocket: WebSocket,
    session_id: str,
    session_type: str,
    patient_id: str
):
    """
    WebSocket endpoint that bridges mobile app audio ↔ Gemini Live API
    
    Protocol:
    - Client sends: binary audio chunks (PCM 16-bit, 16kHz)
    - Server sends: binary audio chunks (PCM 16-bit, 24kHz) + JSON messages
    """
    await websocket.accept()
    
    audio_input_queue = asyncio.Queue()
    
    async with AsyncSessionLocal() as db:
        # Load patient and session data
        patient = await db.get(Patient, patient_id)
        
        # Create voice session record
        voice_session = VoiceSession(
            id=session_id,
            patient_id=patient_id,
            session_type=session_type,
            status="active",
            started_at=datetime.utcnow()
        )
        db.add(voice_session)
        await db.commit()
        
        # Prepare variables for prompt
        variables = {
            "patient_name": patient.full_name,
            "caregiver_name": patient.caregiver.full_name if patient.caregiver else "your caregiver",
        }
        
        # Add medication info for reminder sessions
        if session_type == "reminder":
            # Load from scheduled reminder context
            # (passed via session metadata)
            pass
        
        # Get system prompt
        system_prompt = AGENT_PROMPTS.get(session_type, AGENT_PROMPTS["reminder"])
        
        # Create Gemini config
        config = await voice_service.create_voice_session(
            session_type=session_type,
            system_prompt=system_prompt,
            variables=variables
        )
        
        transcript_parts = []
        
        async def audio_output_callback(audio_data: bytes):
            """Send audio back to mobile app"""
            await websocket.send_bytes(audio_data)
        
        async def on_transcript_update(text: str):
            """Send transcript update to mobile app"""
            transcript_parts.append(text)
            await websocket.send_json({
                "type": "transcript",
                "text": text
            })
        
        async def on_session_end(transcript: str, extracted_data: dict):
            """Handle session completion"""
            voice_session.status = "completed"
            voice_session.ended_at = datetime.utcnow()
            voice_session.transcript = transcript
            voice_session.extracted_data = extracted_data
            voice_session.duration_seconds = int(
                (voice_session.ended_at - voice_session.started_at).total_seconds()
            )
            await db.commit()
            
            await websocket.send_json({
                "type": "session_end",
                "transcript": transcript,
                "extracted_data": extracted_data
            })
        
        # Handle incoming audio from mobile app
        async def receive_from_client():
            try:
                while True:
                    data = await websocket.receive()
                    if "bytes" in data:
                        await audio_input_queue.put(data["bytes"])
                    elif "text" in data:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "end":
                            await audio_input_queue.put(None)
                            break
            except WebSocketDisconnect:
                await audio_input_queue.put(None)
        
        # Run voice session
        await asyncio.gather(
            receive_from_client(),
            voice_service.run_voice_session(
                config=config,
                audio_input_queue=audio_input_queue,
                audio_output_callback=audio_output_callback,
                on_transcript_update=on_transcript_update,
                on_session_end=on_session_end
            )
        )
```

### Voice Router Changes

**Delete:** Vapi webhook endpoints

**Create:** `backend/app/voice/router.py`

```python
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from app.voice.websocket_handler import handle_voice_websocket
from app.voice.gemini_voice import GeminiVoiceService, AGENT_PROMPTS
from app.database import get_db, AsyncSession
from app.models import Patient, ScheduledReminder, VoiceSession
from app.notifications import send_call_notification
import uuid

router = APIRouter(prefix="/voice", tags=["voice"])

@router.websocket("/session/{session_id}")
async def voice_session_websocket(
    websocket: WebSocket,
    session_id: str,
    session_type: str,
    patient_id: str
):
    """
    WebSocket endpoint for real-time voice conversation.
    Mobile app connects here after user answers the "call".
    """
    await handle_voice_websocket(
        websocket=websocket,
        session_id=session_id,
        session_type=session_type,
        patient_id=patient_id
    )

@router.post("/trigger-call/{patient_id}")
async def trigger_call(
    patient_id: str,
    session_type: str,
    metadata: dict = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a "call" to patient's app.
    This sends a push notification that shows incoming call UI.
    """
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if not patient.device_token:
        raise HTTPException(status_code=400, detail="Patient has no registered device")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create pending voice session
    voice_session = VoiceSession(
        id=session_id,
        patient_id=patient_id,
        session_type=session_type,
        status="pending"
    )
    db.add(voice_session)
    await db.commit()
    
    # Send push notification to trigger call UI
    await send_call_notification(
        device_token=patient.device_token,
        device_platform=patient.device_platform,
        session_id=session_id,
        session_type=session_type,
        caller_name="Calla",
        metadata=metadata or {}
    )
    
    return {"session_id": session_id, "status": "notification_sent"}
```

---

## 4. Push Notifications (Trigger "Incoming Call")

**Create:** `backend/app/notifications.py`

```python
import httpx
from firebase_admin import messaging, initialize_app, credentials
import json

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-service-account.json")
initialize_app(cred)

async def send_call_notification(
    device_token: str,
    device_platform: str,
    session_id: str,
    session_type: str,
    caller_name: str,
    metadata: dict
):
    """
    Send high-priority push notification that triggers incoming call UI.
    
    On Android: Use FCM with high priority + call channel
    On iOS: Use VoIP push (requires special certificate) or regular push with CallKit
    """
    
    if device_platform == "android":
        message = messaging.Message(
            token=device_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="incoming_calls",
                    title="Incoming Call",
                    body=f"{caller_name} is calling...",
                    sound="ringtone",
                    priority="max",
                ),
            ),
            data={
                "type": "incoming_call",
                "session_id": session_id,
                "session_type": session_type,
                "caller_name": caller_name,
                "metadata": json.dumps(metadata),
            }
        )
    else:  # iOS
        message = messaging.Message(
            token=device_token,
            apns=messaging.APNSConfig(
                headers={
                    "apns-priority": "10",
                    "apns-push-type": "voip",  # Requires VoIP certificate
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title="Incoming Call",
                            body=f"{caller_name} is calling...",
                        ),
                        sound="ringtone.caf",
                        category="INCOMING_CALL",
                    ),
                    custom_data={
                        "session_id": session_id,
                        "session_type": session_type,
                        "caller_name": caller_name,
                    }
                )
            )
        )
    
    response = messaging.send(message)
    return response
```

---

## 5. LiteLLM for Chatbot (Prescription Entry)

**Original (OpenAI direct):**
```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...]
)
```

**New (LiteLLM with Gemini):**
```python
from litellm import completion

async def chat_completion(messages: list, system_prompt: str = None):
    """
    Use LiteLLM for chatbot interactions (prescription entry, etc.)
    This is separate from the real-time voice (which uses Gemini Live API directly)
    """
    full_messages = []
    
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    
    full_messages.extend(messages)
    
    response = completion(
        model="gemini/gemini-2.0-flash",  # LiteLLM format
        messages=full_messages,
        api_key=settings.GEMINI_API_KEY
    )
    
    return response.choices[0].message.content
```

**Update chatbot service:** `backend/app/chat/service.py`

```python
from litellm import completion
from app.external.rxnorm import search_drugs
import json

PRESCRIPTION_SYSTEM_PROMPT = """
You are a helpful assistant for adding medication prescriptions to Calla.
You're chatting with a caregiver who wants to add a medication for their patient.

Your job:
1. Ask for the medication name (help them search if needed)
2. Confirm the dosage
3. Ask about frequency (once daily, twice daily, etc.)
4. Ask about timing (with food, before bed, etc.)
5. Ask about any special instructions
6. Summarize and confirm before saving

When you need to search for a drug, output:
{"action": "search_drug", "query": "drug name"}

When you have all required information, output:
{
  "action": "save_medication",
  "medication": {
    "drug_name": "...",
    "rxcui": "...",
    "dosage": "...",
    "frequency": "...",
    "timing_preference": "...",
    "instructions": "..."
  }
}

Be conversational and helpful. If they give partial information, ask follow-up questions.
"""

class PrescriptionChatbot:
    def __init__(self):
        self.conversations = {}  # session_id -> message history
    
    async def process_message(self, session_id: str, user_message: str):
        # Get or create conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        history = self.conversations[session_id]
        history.append({"role": "user", "content": user_message})
        
        # Call LiteLLM
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": "system", "content": PRESCRIPTION_SYSTEM_PROMPT},
                *history
            ],
            api_key=settings.GEMINI_API_KEY
        )
        
        assistant_message = response.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_message})
        
        # Check for actions in response
        result = {"message": assistant_message, "action": None, "data": None}
        
        try:
            # Try to parse JSON action from response
            if "{" in assistant_message:
                json_start = assistant_message.index("{")
                json_end = assistant_message.rindex("}") + 1
                action_data = json.loads(assistant_message[json_start:json_end])
                
                if action_data.get("action") == "search_drug":
                    # Perform drug search
                    drugs = await search_drugs(action_data["query"])
                    result["action"] = "show_drug_options"
                    result["data"] = drugs
                
                elif action_data.get("action") == "save_medication":
                    result["action"] = "save_medication"
                    result["data"] = action_data["medication"]
        except (json.JSONDecodeError, ValueError):
            pass  # No action, just conversation
        
        return result
```

---

## 6. Scheduler Changes

**Original (Vapi calls):**
```python
await VoiceService.trigger_reminder_call(...)
```

**New (Push notification + WebSocket):**
```python
from app.notifications import send_call_notification

async def check_pending_reminders():
    """Check for reminders due and trigger app calls"""
    now = datetime.utcnow()
    window_end = now + timedelta(minutes=1)
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledReminder)
            .options(selectinload(ScheduledReminder.patient))
            .options(selectinload(ScheduledReminder.medication))
            .where(ScheduledReminder.status == "pending")
            .where(ScheduledReminder.scheduled_time >= now)
            .where(ScheduledReminder.scheduled_time <= window_end)
        )
        reminders = result.scalars().all()
        
        for reminder in reminders:
            patient = reminder.patient
            medication = reminder.medication
            
            if patient.device_token:
                # Trigger call via push notification
                session_id = str(uuid.uuid4())
                
                await send_call_notification(
                    device_token=patient.device_token,
                    device_platform=patient.device_platform,
                    session_id=session_id,
                    session_type="reminder",
                    caller_name="Calla",
                    metadata={
                        "reminder_id": str(reminder.id),
                        "medication_name": medication.drug_name,
                        "dosage": medication.dosage,
                        "instructions": medication.notes or ""
                    }
                )
                
                reminder.status = "calling"
                await db.commit()
            else:
                # No device registered - mark for SMS fallback or skip
                reminder.status = "no_device"
                await db.commit()
```

---

## 7. Mobile App Changes

The patient app needs to:

1. **Register device token** on login/install
2. **Handle incoming call push notifications**
3. **Show full-screen call UI** (CallKit on iOS, custom on Android)
4. **Connect to WebSocket** when user answers
5. **Stream audio** bidirectionally

### Flutter Implementation Outline

```dart
// Key packages needed:
// flutter_callkit_incoming: ^2.0.0
// web_socket_channel: ^2.4.0
// permission_handler: ^11.0.0
// record: ^5.0.0  (for microphone)
// just_audio: ^0.9.0  (for playback)
// firebase_messaging: ^14.0.0

class CallaCallService {
  WebSocketChannel? _channel;
  
  // Handle incoming push notification
  Future<void> handleIncomingCall(Map<String, dynamic> data) async {
    final sessionId = data['session_id'];
    final sessionType = data['session_type'];
    final callerName = data['caller_name'];
    
    // Show native call UI
    await FlutterCallkitIncoming.showCallkitIncoming(
      CallKitParams(
        id: sessionId,
        nameCaller: callerName,
        type: 0,  // Voice call
        textAccept: 'Answer',
        textDecline: 'Decline',
      ),
    );
  }
  
  // When user taps "Answer"
  Future<void> answerCall(String sessionId, String sessionType, String patientId) async {
    // Connect to WebSocket
    final wsUrl = 'wss://your-backend.com/voice/session/$sessionId'
        '?session_type=$sessionType&patient_id=$patientId';
    
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    
    // Start audio streaming
    await _startAudioStream();
  }
  
  Future<void> _startAudioStream() async {
    // Record from microphone and send to WebSocket
    final recorder = AudioRecorder();
    await recorder.start(
      RecordConfig(encoder: AudioEncoder.pcm16bit, sampleRate: 16000),
      path: '', // Stream mode
    );
    
    recorder.onStateChanged().listen((state) {
      // Send audio chunks to WebSocket
    });
    
    // Receive audio from WebSocket and play
    _channel!.stream.listen((data) {
      if (data is List<int>) {
        // Play audio response
        _playAudio(Uint8List.fromList(data));
      } else if (data is String) {
        // Handle JSON messages (transcript, session_end)
        final msg = jsonDecode(data);
        // Update UI with transcript, etc.
      }
    });
  }
}
```

---

## 8. Environment Variables (Final)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/calla

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini
GEMINI_API_KEY=your_gemini_api_key

# Firebase (for push notifications)
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json

# Optional: Twilio for SMS fallback
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 9. Updated Dependencies

### Backend (`requirements.txt`)

```
# Web framework
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Gemini / LLM
google-genai==0.3.0
litellm==1.17.0

# Firebase notifications
firebase-admin==6.4.0

# HTTP client
httpx==0.26.0

# Scheduling
apscheduler==3.10.4

# Utils
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
```

---

## Summary of Key Changes

| Component | Original | New |
|-----------|----------|-----|
| **Database client** | `supabase` | `sqlalchemy` + `asyncpg` |
| **Models** | Supabase tables | SQLAlchemy ORM models |
| **Voice calls** | Vapi.ai webhooks | Gemini Live API + WebSocket |
| **Call trigger** | Vapi outbound call | Push notification → App UI |
| **Chatbot LLM** | OpenAI/Anthropic | LiteLLM → Gemini |
| **Webhooks** | `/webhooks/vapi/*` | Removed (direct WebSocket) |
| **New endpoint** | N/A | `WebSocket /voice/session/{id}` |
| **New service** | N/A | Push notifications (Firebase) |

The core flows remain the same — only the underlying services change. The caregiver dashboard stays mostly identical; the patient experience shifts from real phone calls to in-app "fake calls" powered by Gemini Live.
