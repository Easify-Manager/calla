"""Scheduler jobs for medication reminders using Twilio voice calls"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, time
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload
from app.database import sync_engine
from app.models import ScheduledReminder, Medication, Patient, Caregiver, AdherenceEvent, VoiceSession
from app.twilio_service import twilio_service
from app.config import settings
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def get_sync_session():
    """Get a sync session for scheduler jobs"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=sync_engine)
    return SessionLocal()


def trigger_reminder_via_twilio(
    patient: Patient,
    medication: Medication,
    reminder_id: str
) -> str:
    """Trigger a reminder call via Twilio with Gemini Live conversation"""
    if not patient.phone_number:
        logger.warning(f"Patient {patient.id} has no phone number")
        return None

    # Build WebSocket stream URL for Twilio Media Streams
    # Use wss:// for production, ws:// for local testing
    backend_url = settings.FRONTEND_URL.replace("3000", "8000").replace("http://", "ws://").replace("https://", "wss://")
    stream_url = (
        f"{backend_url}/api/voice/twilio/stream"
        f"?reminder_id={reminder_id}"
        f"&patient_name={patient.full_name}"
        f"&medication_name={medication.drug_name}"
        f"&dosage={medication.dosage or ''}"
    )

    # Initiate the call
    call_sid = twilio_service.initiate_reminder_call(
        patient_phone=patient.phone_number,
        patient_name=patient.full_name,
        medication_name=medication.drug_name,
        dosage=medication.dosage or "",
        reminder_id=reminder_id,
        stream_url=stream_url
    )

    return call_sid


async def check_pending_reminders():
    """Check for reminders due in the next minute and trigger Twilio calls"""
    try:
        session = get_sync_session()
        now = datetime.utcnow()
        window_end = now + timedelta(minutes=1)

        # Get pending reminders with related data
        reminders = session.query(ScheduledReminder)\
            .options(
                selectinload(ScheduledReminder.medication),
                selectinload(ScheduledReminder.patient)
            )\
            .filter(ScheduledReminder.status == "pending")\
            .filter(ScheduledReminder.scheduled_time >= now)\
            .filter(ScheduledReminder.scheduled_time <= window_end)\
            .all()

        for reminder in reminders:
            try:
                patient = reminder.patient
                medication = reminder.medication

                if not patient or not medication:
                    continue

                if patient.phone_number:
                    # Trigger Twilio call
                    call_sid = trigger_reminder_via_twilio(
                        patient=patient,
                        medication=medication,
                        reminder_id=str(reminder.id)
                    )

                    if call_sid:
                        reminder.status = "calling"
                        reminder.attempt_count = 1
                        reminder.last_attempt_time = now
                        logger.info(f"Triggered Twilio call {call_sid} for reminder {reminder.id}")
                    else:
                        reminder.status = "call_failed"
                        logger.error(f"Failed to initiate Twilio call for reminder {reminder.id}")
                else:
                    # No phone number
                    reminder.status = "no_phone"
                    logger.warning(f"Patient {patient.id} has no phone number")

                session.commit()

            except Exception as e:
                logger.error(f"Failed to trigger reminder {reminder.id}: {e}")

        session.close()

    except Exception as e:
        logger.error(f"Error checking pending reminders: {e}")


async def check_missed_reminders():
    """Check for reminders that weren't confirmed and handle retries/escalation with 3-minute intervals"""
    try:
        session = get_sync_session()
        now = datetime.utcnow()

        # Get reminders that are still "calling" (not confirmed)
        reminders = session.query(ScheduledReminder)\
            .options(
                selectinload(ScheduledReminder.medication),
                selectinload(ScheduledReminder.patient).selectinload(Patient.caregiver)
            )\
            .filter(ScheduledReminder.status == "calling")\
            .all()

        for reminder in reminders:
            try:
                patient = reminder.patient
                medication = reminder.medication
                caregiver = patient.caregiver if patient else None

                if not patient or not medication:
                    continue

                # Check if 3 minutes have passed since last attempt
                if reminder.last_attempt_time:
                    time_since_last_attempt = now - reminder.last_attempt_time
                    if time_since_last_attempt < timedelta(minutes=3):
                        # Not yet time for retry, skip
                        continue

                if reminder.attempt_count >= 3:
                    # Max attempts reached - escalate and alert caregiver
                    reminder.status = "escalated"

                    # Log missed dose
                    adherence_event = AdherenceEvent(
                        reminder_id=reminder.id,
                        medication_id=reminder.medication_id,
                        patient_id=reminder.patient_id,
                        scheduled_time=reminder.scheduled_time,
                        confirmation_method="twilio_call",
                        was_taken=False,
                        notes="Escalated after 3 failed Twilio call attempts"
                    )
                    session.add(adherence_event)

                    # Alert caregiver via phone call
                    if caregiver and caregiver.phone_number:
                        scheduled_time_str = reminder.scheduled_time.strftime("%I:%M %p")
                        call_sid = twilio_service.initiate_caregiver_alert_call(
                            caregiver_phone=caregiver.phone_number,
                            caregiver_name=caregiver.full_name,
                            patient_name=patient.full_name,
                            medication_name=medication.drug_name,
                            scheduled_time=scheduled_time_str
                        )

                        if call_sid:
                            logger.info(f"Alerted caregiver {caregiver.id} via call {call_sid} for missed reminder {reminder.id}")
                        else:
                            logger.error(f"Failed to alert caregiver for reminder {reminder.id}")
                    else:
                        logger.warning(f"Caregiver has no phone number for escalation of reminder {reminder.id}")

                    logger.info(f"Escalated reminder {reminder.id} after 3 failed attempts")
                else:
                    # Retry the call (attempt 2 or 3)
                    if patient.phone_number:
                        call_sid = trigger_reminder_via_twilio(
                            patient=patient,
                            medication=medication,
                            reminder_id=str(reminder.id)
                        )

                        if call_sid:
                            reminder.attempt_count += 1
                            reminder.last_attempt_time = now
                            logger.info(f"Retrying reminder {reminder.id} (attempt {reminder.attempt_count}) via call {call_sid}")
                        else:
                            reminder.status = "call_failed"
                    else:
                        reminder.status = "no_phone"

                session.commit()

            except Exception as e:
                logger.error(f"Failed to handle missed reminder {reminder.id}: {e}")

        session.close()

    except Exception as e:
        logger.error(f"Error checking missed reminders: {e}")


async def generate_daily_reminders():
    """Generate reminders for medications each day"""
    try:
        session = get_sync_session()
        
        # Get all active medications
        medications = session.query(Medication)\
            .filter(Medication.is_active == True)\
            .all()
        
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        
        for medication in medications:
            specific_times = medication.specific_times or []
            if not specific_times:
                continue
            
            for time_str in specific_times:
                try:
                    hour, minute = map(int, time_str.split(":"))
                    scheduled_time = datetime.combine(
                        tomorrow,
                        time(hour=hour, minute=minute)
                    )
                    
                    # Check if reminder already exists
                    existing = session.query(ScheduledReminder)\
                        .filter(ScheduledReminder.medication_id == medication.id)\
                        .filter(ScheduledReminder.scheduled_time == scheduled_time)\
                        .first()
                    
                    if not existing:
                        reminder = ScheduledReminder(
                            medication_id=medication.id,
                            patient_id=medication.patient_id,
                            scheduled_time=scheduled_time,
                            status="pending",
                            attempt_count=0
                        )
                        session.add(reminder)
                
                except (ValueError, TypeError):
                    continue
        
        session.commit()
        session.close()
        print(f"Generated daily reminders for {len(medications)} medications")
    
    except Exception as e:
        print(f"Error generating daily reminders: {e}")


def run_async_job(coro):
    """Helper to run async job in scheduler"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def start_scheduler():
    """Initialize and start the scheduler"""
    # Check for due reminders every minute
    scheduler.add_job(
        lambda: run_async_job(check_pending_reminders()),
        CronTrigger(minute="*"),
        id="check_reminders",
        replace_existing=True
    )
    
    # Check for missed reminders every 5 minutes
    scheduler.add_job(
        lambda: run_async_job(check_missed_reminders()),
        CronTrigger(minute="*/5"),
        id="check_missed",
        replace_existing=True
    )
    
    # Generate next day's reminders at midnight
    scheduler.add_job(
        lambda: run_async_job(generate_daily_reminders()),
        CronTrigger(hour=0, minute=0),
        id="generate_daily",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with Twilio voice call reminder jobs")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")
