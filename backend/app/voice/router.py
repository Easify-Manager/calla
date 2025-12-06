"""Voice API routes - WebSocket and REST endpoints for voice sessions"""

from fastapi import APIRouter, WebSocket, Depends, HTTPException, Query, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from twilio.twiml.voice_response import VoiceResponse
import uuid

from app.voice.websocket_handler import handle_voice_websocket
from app.voice.service import VoiceService
from app.database import get_db
from app.models import VoiceSession, Patient, Caregiver, ScheduledReminder, AdherenceEvent
from app.auth.utils import get_current_caregiver
from app.patients.service import PatientService

router = APIRouter(tags=["voice"])


# ============== WebSocket Endpoint ==============

@router.websocket("/api/voice/session/{session_id}")
async def voice_session_websocket(
    websocket: WebSocket,
    session_id: str,
    session_type: str = Query(...),
    patient_id: str = Query(...)
):
    """
    WebSocket endpoint for real-time voice conversation.
    
    Mobile app connects here after user answers the "call".
    
    Query params:
    - session_type: onboarding, reminder, or escalation
    - patient_id: UUID of the patient
    
    Protocol:
    - Client sends: binary audio chunks (PCM 16-bit, 16kHz)
    - Server sends: binary audio chunks + JSON messages
    """
    await handle_voice_websocket(
        websocket=websocket,
        session_id=session_id,
        session_type=session_type,
        patient_id=patient_id
    )


# ============== REST Endpoints ==============

class TriggerCallRequest(BaseModel):
    session_type: str  # onboarding, reminder, escalation
    metadata: Optional[dict] = None


class TriggerCallResponse(BaseModel):
    session_id: str
    status: str


@router.post("/api/voice/trigger-call/{patient_id}", response_model=TriggerCallResponse)
async def trigger_call(
    patient_id: str,
    request: TriggerCallRequest,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a "call" to patient's app.
    
    This sends a push notification that shows incoming call UI on the patient's device.
    """
    # Verify patient belongs to caregiver
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if not patient.device_token:
        raise HTTPException(
            status_code=400, 
            detail="Patient has no registered device. They need to install the app first."
        )
    
    session_id = await VoiceService.trigger_call(
        db=db,
        patient_id=patient_id,
        session_type=request.session_type,
        metadata=request.metadata,
        caregiver_id=str(caregiver.id)
    )
    
    if session_id:
        return TriggerCallResponse(
            session_id=session_id,
            status="notification_sent"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger call. Push notification may have failed."
        )


class SessionResponse(BaseModel):
    id: str
    patient_id: str
    session_type: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    extracted_data: Optional[dict] = None
    created_at: datetime
    patient_name: Optional[str] = None


@router.get("/api/voice/sessions", response_model=List[SessionResponse])
async def get_voice_sessions(
    limit: int = 50,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get voice session history for caregiver's patients"""
    # Get caregiver's patients
    patients_result = await db.execute(
        select(Patient.id, Patient.full_name)
        .where(Patient.caregiver_id == caregiver.id)
    )
    patients = {str(p.id): p.full_name for p in patients_result.all()}
    patient_ids = list(patients.keys())
    
    if not patient_ids:
        return []
    
    # Get voice sessions
    result = await db.execute(
        select(VoiceSession)
        .where(VoiceSession.patient_id.in_(patient_ids))
        .order_by(VoiceSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return [
        SessionResponse(
            id=str(s.id),
            patient_id=str(s.patient_id),
            session_type=s.session_type,
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_seconds=s.duration_seconds,
            transcript=s.transcript,
            extracted_data=s.extracted_data,
            created_at=s.created_at,
            patient_name=patients.get(str(s.patient_id))
        )
        for s in sessions
    ]


@router.get("/api/voice/sessions/{session_id}", response_model=SessionResponse)
async def get_voice_session(
    session_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific voice session"""
    result = await db.execute(
        select(VoiceSession)
        .options(selectinload(VoiceSession.patient))
        .where(VoiceSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify caregiver owns the patient
    if session.patient and session.patient.caregiver_id != caregiver.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=str(session.id),
        patient_id=str(session.patient_id),
        session_type=session.session_type,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        transcript=session.transcript,
        extracted_data=session.extracted_data,
        created_at=session.created_at,
        patient_name=session.patient.full_name if session.patient else None
    )


# ============== Device Registration (for Patient App) ==============

class RegisterDeviceRequest(BaseModel):
    patient_id: str
    device_token: str
    device_platform: str  # "ios" or "android"


@router.post("/api/voice/register-device")
async def register_device(
    request: RegisterDeviceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a patient's device for push notifications.
    
    Called by the patient app after getting push notification permission.
    Note: This endpoint doesn't require auth - it uses patient_id directly.
    In production, you'd want to add patient authentication.
    """
    result = await db.execute(
        select(Patient).where(Patient.id == request.patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient.device_token = request.device_token
    patient.device_platform = request.device_platform
    await db.commit()
    
    return {"status": "device_registered"}


# ============== Session Control (for Patient App) ==============

@router.post("/api/voice/sessions/{session_id}/decline")
async def decline_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Mark a session as declined (patient declined the call)"""
    await VoiceService.mark_session_declined(db, session_id)
    return {"status": "declined"}


@router.post("/api/voice/sessions/{session_id}/missed")
async def mark_session_missed(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Mark a session as missed (call timed out without answer)"""
    await VoiceService.mark_session_missed(db, session_id)
    return {"status": "missed"}


# ============== Twilio Media Stream WebSocket ==============

@router.websocket("/api/voice/twilio/stream")
async def twilio_media_stream(
    websocket: WebSocket,
    reminder_id: str = Query(...),
    patient_name: str = Query(...),
    medication_name: str = Query(...),
    dosage: str = Query(...)
):
    """
    WebSocket endpoint for Twilio Media Streams.

    Twilio connects here to stream audio bidirectionally.
    This bridges Twilio audio with Gemini Live for natural conversation.

    Flow:
    1. Twilio sends patient audio (mulaw 8kHz)
    2. We convert and forward to Gemini Live
    3. Gemini responds with voice (PCM 16kHz)
    4. We convert and send back to Twilio
    """
    from app.voice.twilio_stream_handler import handle_twilio_stream

    await handle_twilio_stream(
        websocket=websocket,
        reminder_id=reminder_id,
        patient_name=patient_name,
        medication_name=medication_name,
        dosage=dosage
    )
