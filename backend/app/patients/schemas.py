from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time


class PatientBase(BaseModel):
    full_name: str
    phone_number: str
    date_of_birth: Optional[date] = None
    preferred_language: str = "en"
    voice_preference: str = "Puck"  # Gemini voice: Puck, Charon, Kore, Fenrir, Aoede
    call_retry_attempts: int = 3


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    breakfast_time: Optional[time] = None
    lunch_time: Optional[time] = None
    dinner_time: Optional[time] = None
    preferred_language: Optional[str] = None
    voice_preference: Optional[str] = None
    call_retry_attempts: Optional[int] = None
    device_token: Optional[str] = None
    device_platform: Optional[str] = None


class PatientRoutine(BaseModel):
    wake_time: Optional[str] = None
    sleep_time: Optional[str] = None
    breakfast_time: Optional[str] = None
    lunch_time: Optional[str] = None
    dinner_time: Optional[str] = None


class PatientResponse(PatientBase):
    id: str
    caregiver_id: str
    wake_time: Optional[str] = None
    sleep_time: Optional[str] = None
    breakfast_time: Optional[str] = None
    lunch_time: Optional[str] = None
    dinner_time: Optional[str] = None
    onboarding_completed: bool = False
    device_token: Optional[str] = None
    device_platform: Optional[str] = None
    has_device: bool = False  # Computed field
    created_at: datetime

    class Config:
        from_attributes = True


class AdherenceStats(BaseModel):
    total_scheduled: int
    total_taken: int
    total_missed: int
    adherence_rate: float
    streak_days: int
