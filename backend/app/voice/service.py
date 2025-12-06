"""Voice service for triggering and managing voice sessions"""

from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import VoiceSession, Patient
from app.notifications import send_call_notification
from app.config import settings


class VoiceService:
    """Service for managing voice sessions and triggering calls"""
    
    @staticmethod
    async def trigger_call(
        db: AsyncSession,
        patient_id: str,
        session_type: str,
        metadata: dict = None,
        caregiver_id: str = None,
        reminder_id: str = None
    ) -> Optional[str]:
        """
        Trigger a "call" to patient's app via push notification.
        
        Returns session_id if successful, None if failed.
        """
        # Get patient
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            print(f"Patient {patient_id} not found")
            return None
        
        if not patient.device_token:
            print(f"Patient {patient_id} has no registered device")
            return None
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create pending voice session
        voice_session = VoiceSession(
            id=session_id,
            patient_id=patient_id,
            caregiver_id=caregiver_id,
            reminder_id=reminder_id,
            session_type=session_type,
            status="pending",
            metadata=metadata or {}
        )
        db.add(voice_session)
        await db.commit()
        
        # Send push notification to trigger call UI
        notification_result = await send_call_notification(
            device_token=patient.device_token,
            device_platform=patient.device_platform or "android",
            session_id=session_id,
            session_type=session_type,
            caller_name="Calla",
            metadata=metadata or {}
        )
        
        if notification_result:
            print(f"Call triggered for patient {patient_id}, session {session_id}")
            return session_id
        else:
            # Update session status if notification failed
            voice_session.status = "notification_failed"
            await db.commit()
            return None
    
    @staticmethod
    async def trigger_onboarding_call(
        db: AsyncSession,
        patient_id: str,
        patient_name: str,
        caregiver_name: str,
        caregiver_id: str = None
    ) -> Optional[str]:
        """Trigger an onboarding call to a new patient"""
        return await VoiceService.trigger_call(
            db=db,
            patient_id=patient_id,
            session_type="onboarding",
            metadata={
                "patient_name": patient_name,
                "caregiver_name": caregiver_name
            },
            caregiver_id=caregiver_id
        )
    
    @staticmethod
    async def trigger_reminder_call(
        db: AsyncSession,
        patient_id: str,
        patient_name: str,
        medication_id: str,
        medication_name: str,
        medication_dosage: str = "",
        medication_notes: str = "",
        timing_preference: str = "",
        reminder_id: str = None
    ) -> Optional[str]:
        """Trigger a medication reminder call"""
        instructions = medication_notes or ""
        if timing_preference:
            instructions += f" Take {timing_preference.replace('_', ' ')}."
        
        return await VoiceService.trigger_call(
            db=db,
            patient_id=patient_id,
            session_type="reminder",
            reminder_id=reminder_id,
            metadata={
                "patient_name": patient_name,
                "medication_name": medication_name,
                "medication_id": medication_id,
                "dosage": medication_dosage,
                "instructions": instructions.strip(),
                "reminder_id": reminder_id
            }
        )
    
    @staticmethod
    async def trigger_escalation_call(
        db: AsyncSession,
        caregiver_id: str,
        caregiver_name: str,
        patient_id: str,
        patient_name: str,
        medication_name: str,
        reason: str
    ) -> Optional[str]:
        """Trigger an escalation call to the caregiver"""
        # For escalation, we need the caregiver's device token
        # This would require caregivers to also have the app installed
        # For now, we'll create the session but it may not work without caregiver device
        
        alert_details = f"{patient_name} has not confirmed taking {medication_name} after 3 call attempts."
        
        return await VoiceService.trigger_call(
            db=db,
            patient_id=patient_id,  # Still associate with patient for tracking
            session_type="escalation",
            caregiver_id=caregiver_id,
            metadata={
                "caregiver_name": caregiver_name,
                "patient_name": patient_name,
                "medication_name": medication_name,
                "alert_type": reason,
                "alert_details": alert_details
            }
        )
    
    @staticmethod
    async def mark_session_missed(db: AsyncSession, session_id: str):
        """Mark a voice session as missed (patient didn't answer)"""
        result = await db.execute(
            select(VoiceSession).where(VoiceSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session and session.status == "pending":
            session.status = "missed"
            await db.commit()
    
    @staticmethod
    async def mark_session_declined(db: AsyncSession, session_id: str):
        """Mark a voice session as declined (patient declined the call)"""
        result = await db.execute(
            select(VoiceSession).where(VoiceSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session and session.status in ("pending", "active"):
            session.status = "declined"
            await db.commit()
