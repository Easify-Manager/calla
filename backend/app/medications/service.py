"""Medication service layer"""

from typing import List, Optional
from datetime import datetime, timedelta, time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Medication, ScheduledReminder
from app.medications.schemas import MedicationCreate, MedicationUpdate


class MedicationService:
    
    @staticmethod
    async def get_patient_medications(db: AsyncSession, patient_id: str) -> List[Medication]:
        """Get all medications for a patient"""
        result = await db.execute(
            select(Medication)
            .where(Medication.patient_id == patient_id)
            .order_by(Medication.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_medication(db: AsyncSession, medication_id: str) -> Optional[Medication]:
        """Get a specific medication"""
        result = await db.execute(
            select(Medication).where(Medication.id == medication_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_medication(db: AsyncSession, medication_data: MedicationCreate) -> Optional[Medication]:
        """Create a new medication and generate initial reminders"""
        try:
            medication = Medication(
                patient_id=medication_data.patient_id,
                drug_name=medication_data.drug_name,
                rxcui=medication_data.rxcui,
                dosage=medication_data.dosage,
                dosage_form=medication_data.dosage_form,
                frequency=medication_data.frequency,
                timing_preference=medication_data.timing_preference,
                specific_times=medication_data.specific_times,
                prescribing_doctor=medication_data.prescribing_doctor,
                pharmacy=medication_data.pharmacy,
                refill_date=medication_data.refill_date,
                notes=medication_data.notes,
                is_active=True
            )
            db.add(medication)
            await db.commit()
            await db.refresh(medication)
            
            # Generate reminders for the next 7 days
            await MedicationService.generate_reminders(db, medication, days=7)
            
            return medication
        except Exception as e:
            await db.rollback()
            print(f"Error creating medication: {e}")
            return None
    
    @staticmethod
    async def update_medication(db: AsyncSession, medication_id: str, data: MedicationUpdate) -> Optional[Medication]:
        """Update a medication"""
        medication = await MedicationService.get_medication(db, medication_id)
        if not medication:
            return None
        
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(medication, key, value)
        
        await db.commit()
        await db.refresh(medication)
        
        # Regenerate reminders if times changed
        if data.specific_times is not None:
            await MedicationService.regenerate_reminders(db, medication)
        
        return medication
    
    @staticmethod
    async def delete_medication(db: AsyncSession, medication_id: str) -> bool:
        """Delete a medication"""
        medication = await MedicationService.get_medication(db, medication_id)
        if not medication:
            return False
        
        await db.delete(medication)
        await db.commit()
        return True
    
    @staticmethod
    async def generate_reminders(db: AsyncSession, medication: Medication, days: int = 7):
        """Generate scheduled reminders for a medication"""
        if not medication.specific_times:
            return
        
        today = datetime.utcnow().date()
        
        for day_offset in range(days):
            reminder_date = today + timedelta(days=day_offset)
            
            for time_str in medication.specific_times:
                try:
                    # Parse time string (HH:MM format)
                    parts = time_str.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    
                    scheduled_time = datetime.combine(
                        reminder_date,
                        time(hour=hour, minute=minute)
                    )
                    
                    # Skip if time is in the past
                    if scheduled_time <= datetime.utcnow():
                        continue
                    
                    # Check if reminder already exists
                    existing = await db.execute(
                        select(ScheduledReminder)
                        .where(ScheduledReminder.medication_id == medication.id)
                        .where(ScheduledReminder.scheduled_time == scheduled_time)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    reminder = ScheduledReminder(
                        medication_id=medication.id,
                        patient_id=medication.patient_id,
                        scheduled_time=scheduled_time,
                        status="pending",
                        attempt_count=0
                    )
                    db.add(reminder)
                
                except (ValueError, TypeError) as e:
                    print(f"Invalid time format: {time_str} - {e}")
                    continue
        
        await db.commit()
    
    @staticmethod
    async def regenerate_reminders(db: AsyncSession, medication: Medication):
        """Delete future reminders and regenerate them"""
        now = datetime.utcnow()
        
        # Delete future pending reminders
        result = await db.execute(
            select(ScheduledReminder)
            .where(ScheduledReminder.medication_id == medication.id)
            .where(ScheduledReminder.scheduled_time > now)
            .where(ScheduledReminder.status == "pending")
        )
        future_reminders = result.scalars().all()
        
        for reminder in future_reminders:
            await db.delete(reminder)
        
        await db.commit()
        
        # Generate new reminders
        await MedicationService.generate_reminders(db, medication)
