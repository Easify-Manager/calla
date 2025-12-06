from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Time, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Caregiver(Base):
    __tablename__ = "caregivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    patients = relationship("Patient", back_populates="caregiver", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="CASCADE"))
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)  # For SMS fallback only
    date_of_birth = Column(Date)
    
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
    voice_preference = Column(String(50), default="Puck")  # Gemini voice: Puck, Charon, Kore, Fenrir, Aoede
    call_retry_attempts = Column(Integer, default=3)
    
    # Status
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    caregiver = relationship("Caregiver", back_populates="patients")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    reminders = relationship("ScheduledReminder", back_populates="patient", cascade="all, delete-orphan")
    voice_sessions = relationship("VoiceSession", back_populates="patient", cascade="all, delete-orphan")


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
    specific_times = Column(ARRAY(Text))
    prescribing_doctor = Column(String(255))
    pharmacy = Column(String(255))
    refill_date = Column(Date)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    patient = relationship("Patient", back_populates="medications")
    reminders = relationship("ScheduledReminder", back_populates="medication", cascade="all, delete-orphan")


class ScheduledReminder(Base):
    __tablename__ = "scheduled_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")  # pending, calling, confirmed, missed, escalated, no_device
    attempt_count = Column(Integer, default=0)
    last_attempt_time = Column(DateTime(timezone=True))  # Track when last call attempt was made
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    medication = relationship("Medication", back_populates="reminders")
    patient = relationship("Patient", back_populates="reminders")


class VoiceSession(Base):
    """Tracks active and completed voice sessions (replaces call_logs)"""
    __tablename__ = "voice_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id"))
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_reminders.id"), nullable=True)
    
    session_type = Column(String(50), nullable=False)  # onboarding, reminder, escalation
    status = Column(String(20), default="pending")  # pending, active, completed, missed, declined
    
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    transcript = Column(Text)
    extracted_data = Column(JSONB)
    
    # Metadata passed during call trigger
    session_metadata = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    patient = relationship("Patient", back_populates="voice_sessions")


class AdherenceEvent(Base):
    __tablename__ = "adherence_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_reminders.id"))
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    voice_session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=True)
    
    scheduled_time = Column(DateTime(timezone=True))
    confirmed_time = Column(DateTime(timezone=True))
    confirmation_method = Column(String(50))  # voice_session, manual
    was_taken = Column(Boolean)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
