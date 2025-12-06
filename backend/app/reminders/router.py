"""Reminder routes"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta, time
from pydantic import BaseModel

from app.database import get_db
from app.auth.utils import get_current_caregiver
from app.models import Caregiver, Patient, ScheduledReminder, Medication, AdherenceEvent

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderResponse(BaseModel):
    id: str
    medication_id: str
    patient_id: str
    patient_name: str
    medication_name: str
    dosage: str | None
    scheduled_time: datetime
    status: str
    attempt_count: int

    class Config:
        from_attributes = True


@router.get("/today", response_model=List[ReminderResponse])
async def get_today_reminders(
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get all reminders scheduled for today"""
    # Get caregiver's patient IDs
    patients_result = await db.execute(
        select(Patient.id, Patient.full_name)
        .where(Patient.caregiver_id == caregiver.id)
    )
    patients = {str(p.id): p.full_name for p in patients_result.all()}
    patient_ids = list(patients.keys())
    
    if not patient_ids:
        return []
    
    # Get today's reminders
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_end = datetime.combine(datetime.utcnow().date(), time.max)
    
    result = await db.execute(
        select(ScheduledReminder)
        .options(selectinload(ScheduledReminder.medication))
        .where(ScheduledReminder.patient_id.in_(patient_ids))
        .where(ScheduledReminder.scheduled_time >= today_start)
        .where(ScheduledReminder.scheduled_time <= today_end)
        .order_by(ScheduledReminder.scheduled_time)
    )
    reminders = result.scalars().all()
    
    return [
        ReminderResponse(
            id=str(r.id),
            medication_id=str(r.medication_id),
            patient_id=str(r.patient_id),
            patient_name=patients.get(str(r.patient_id), "Unknown"),
            medication_name=r.medication.drug_name if r.medication else "Unknown",
            dosage=r.medication.dosage if r.medication else None,
            scheduled_time=r.scheduled_time,
            status=r.status,
            attempt_count=r.attempt_count
        )
        for r in reminders
    ]


@router.get("/upcoming", response_model=List[ReminderResponse])
async def get_upcoming_reminders(
    days: int = 7,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming reminders for the next N days"""
    # Get caregiver's patient IDs
    patients_result = await db.execute(
        select(Patient.id, Patient.full_name)
        .where(Patient.caregiver_id == caregiver.id)
    )
    patients = {str(p.id): p.full_name for p in patients_result.all()}
    patient_ids = list(patients.keys())
    
    if not patient_ids:
        return []
    
    # Get upcoming reminders
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    result = await db.execute(
        select(ScheduledReminder)
        .options(selectinload(ScheduledReminder.medication))
        .where(ScheduledReminder.patient_id.in_(patient_ids))
        .where(ScheduledReminder.scheduled_time >= now)
        .where(ScheduledReminder.scheduled_time <= end_date)
        .where(ScheduledReminder.status == "pending")
        .order_by(ScheduledReminder.scheduled_time)
    )
    reminders = result.scalars().all()
    
    return [
        ReminderResponse(
            id=str(r.id),
            medication_id=str(r.medication_id),
            patient_id=str(r.patient_id),
            patient_name=patients.get(str(r.patient_id), "Unknown"),
            medication_name=r.medication.drug_name if r.medication else "Unknown",
            dosage=r.medication.dosage if r.medication else None,
            scheduled_time=r.scheduled_time,
            status=r.status,
            attempt_count=r.attempt_count
        )
        for r in reminders
    ]


@router.post("/{reminder_id}/mark-taken")
async def mark_reminder_taken(
    reminder_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Manually mark a reminder as taken"""
    result = await db.execute(
        select(ScheduledReminder)
        .options(selectinload(ScheduledReminder.patient))
        .where(ScheduledReminder.id == reminder_id)
    )
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    
    # Verify ownership
    if reminder.patient and reminder.patient.caregiver_id != caregiver.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    
    # Update reminder status
    reminder.status = "confirmed"
    
    # Create adherence event
    adherence_event = AdherenceEvent(
        reminder_id=reminder.id,
        medication_id=reminder.medication_id,
        patient_id=reminder.patient_id,
        scheduled_time=reminder.scheduled_time,
        confirmed_time=datetime.utcnow(),
        confirmation_method="manual",
        was_taken=True
    )
    db.add(adherence_event)
    await db.commit()
    
    return {"message": "Reminder marked as taken"}

