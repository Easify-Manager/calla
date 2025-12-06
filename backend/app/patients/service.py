"""Patient service layer for database operations"""

from typing import List, Optional
from datetime import datetime, timedelta, time
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Patient, Medication, AdherenceEvent, ScheduledReminder
from app.patients.schemas import PatientCreate, PatientUpdate, AdherenceStats


class PatientService:
    
    @staticmethod
    async def get_all_patients(db: AsyncSession, caregiver_id: str) -> List[Patient]:
        """Get all patients for a caregiver"""
        result = await db.execute(
            select(Patient)
            .where(Patient.caregiver_id == caregiver_id)
            .order_by(Patient.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_patient(db: AsyncSession, patient_id: str, caregiver_id: str) -> Optional[Patient]:
        """Get a specific patient"""
        result = await db.execute(
            select(Patient)
            .where(Patient.id == patient_id)
            .where(Patient.caregiver_id == caregiver_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_patient(db: AsyncSession, caregiver_id: str, patient_data: PatientCreate) -> Optional[Patient]:
        """Create a new patient"""
        try:
            patient = Patient(
                caregiver_id=caregiver_id,
                full_name=patient_data.full_name,
                phone_number=patient_data.phone_number,
                date_of_birth=patient_data.date_of_birth,
                preferred_language=patient_data.preferred_language,
                voice_preference=patient_data.voice_preference,
                call_retry_attempts=patient_data.call_retry_attempts,
                onboarding_completed=False
            )
            db.add(patient)
            await db.commit()
            await db.refresh(patient)
            return patient
        except Exception as e:
            await db.rollback()
            print(f"Error creating patient: {e}")
            return None
    
    @staticmethod
    async def update_patient(
        db: AsyncSession, 
        patient_id: str, 
        caregiver_id: str, 
        patient_data: PatientUpdate
    ) -> Optional[Patient]:
        """Update a patient"""
        patient = await PatientService.get_patient(db, patient_id, caregiver_id)
        if not patient:
            return None
        
        update_dict = patient_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(patient, key, value)
        
        await db.commit()
        await db.refresh(patient)
        return patient
    
    @staticmethod
    async def delete_patient(db: AsyncSession, patient_id: str, caregiver_id: str) -> bool:
        """Delete a patient"""
        patient = await PatientService.get_patient(db, patient_id, caregiver_id)
        if not patient:
            return False
        
        await db.delete(patient)
        await db.commit()
        return True
    
    @staticmethod
    async def get_adherence_stats(db: AsyncSession, patient_id: str, days: int = 30) -> AdherenceStats:
        """Get adherence statistics for a patient"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total scheduled reminders
        total_result = await db.execute(
            select(func.count(ScheduledReminder.id))
            .where(ScheduledReminder.patient_id == patient_id)
            .where(ScheduledReminder.scheduled_time >= cutoff_date)
        )
        total_scheduled = total_result.scalar() or 0
        
        # Get confirmed reminders
        taken_result = await db.execute(
            select(func.count(AdherenceEvent.id))
            .where(AdherenceEvent.patient_id == patient_id)
            .where(AdherenceEvent.was_taken == True)
            .where(AdherenceEvent.created_at >= cutoff_date)
        )
        total_taken = taken_result.scalar() or 0
        
        # Calculate missed
        total_missed = max(0, total_scheduled - total_taken)
        
        # Calculate rate
        adherence_rate = 0.0
        if total_scheduled > 0:
            adherence_rate = round((total_taken / total_scheduled) * 100, 1)
        
        # Calculate streak (simplified - consecutive days with all meds taken)
        streak_days = 0
        today = datetime.utcnow().date()
        
        for i in range(days):
            check_date = today - timedelta(days=i)
            check_start = datetime.combine(check_date, time.min)
            check_end = datetime.combine(check_date, time.max)
            
            # Get reminders for the day
            day_reminders_result = await db.execute(
                select(func.count(ScheduledReminder.id))
                .where(ScheduledReminder.patient_id == patient_id)
                .where(ScheduledReminder.scheduled_time >= check_start)
                .where(ScheduledReminder.scheduled_time <= check_end)
            )
            day_reminders = day_reminders_result.scalar() or 0
            
            if day_reminders == 0:
                continue  # Skip days with no reminders
            
            # Get adherence for the day
            day_taken_result = await db.execute(
                select(func.count(AdherenceEvent.id))
                .where(AdherenceEvent.patient_id == patient_id)
                .where(AdherenceEvent.was_taken == True)
                .where(AdherenceEvent.created_at >= check_start)
                .where(AdherenceEvent.created_at <= check_end)
            )
            day_taken = day_taken_result.scalar() or 0
            
            if day_taken >= day_reminders:
                streak_days += 1
            else:
                break  # Streak broken
        
        return AdherenceStats(
            total_scheduled=total_scheduled,
            total_taken=total_taken,
            total_missed=total_missed,
            adherence_rate=adherence_rate,
            streak_days=streak_days
        )
