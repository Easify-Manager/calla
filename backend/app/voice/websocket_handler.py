"""WebSocket handler for real-time voice sessions"""

import asyncio
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.voice.gemini_voice import gemini_voice_service
from app.database import AsyncSessionLocal
from app.models import VoiceSession, Patient, ScheduledReminder, AdherenceEvent, Medication
from app.config import settings


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
    
    JSON messages from server:
    - {"type": "session_start", "session_id": "..."}
    - {"type": "transcript", "text": "..."}
    - {"type": "session_end", "transcript": "...", "extracted_data": {...}}
    - {"type": "error", "message": "..."}
    
    JSON messages from client:
    - {"type": "end"} - Signal to end the session
    """
    await websocket.accept()
    
    audio_input_queue = asyncio.Queue()
    
    try:
        async with AsyncSessionLocal() as db:
            # Load voice session
            result = await db.execute(
                select(VoiceSession)
                .options(selectinload(VoiceSession.patient).selectinload(Patient.caregiver))
                .where(VoiceSession.id == session_id)
            )
            voice_session = result.scalar_one_or_none()
            
            if not voice_session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                await websocket.close()
                return
            
            patient = voice_session.patient
            if not patient:
                await websocket.send_json({
                    "type": "error",
                    "message": "Patient not found"
                })
                await websocket.close()
                return
            
            # Update session status
            voice_session.status = "active"
            voice_session.started_at = datetime.utcnow()
            await db.commit()
            
            # Prepare variables for prompt
            variables = {
                "patient_name": patient.full_name,
                "caregiver_name": patient.caregiver.full_name if patient.caregiver else "your caregiver",
            }
            
            # Add medication info for reminder sessions
            metadata = voice_session.metadata or {}
            if session_type == "reminder":
                variables["medication_name"] = metadata.get("medication_name", "your medication")
                variables["dosage"] = metadata.get("dosage", "")
                variables["instructions"] = metadata.get("instructions", "")
            elif session_type == "escalation":
                variables["alert_type"] = metadata.get("alert_type", "missed medication")
                variables["alert_details"] = metadata.get("alert_details", "")
            
            # Create Gemini config
            config = gemini_voice_service.create_session_config(
                session_type=session_type,
                variables=variables,
                voice_name=patient.voice_preference or "Puck"
            )
            
            # Notify client session is starting
            await websocket.send_json({
                "type": "session_start",
                "session_id": session_id,
                "session_type": session_type
            })
            
            transcript_parts = []
            
            async def audio_output_callback(audio_data: bytes):
                """Send audio back to mobile app"""
                try:
                    await websocket.send_bytes(audio_data)
                except Exception as e:
                    print(f"Error sending audio: {e}")
            
            async def on_transcript_update(text: str):
                """Send transcript update to mobile app"""
                transcript_parts.append(text)
                try:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": text
                    })
                except Exception as e:
                    print(f"Error sending transcript: {e}")
            
            async def on_session_end(transcript: str, extracted_data: dict):
                """Handle session completion"""
                voice_session.status = "completed"
                voice_session.ended_at = datetime.utcnow()
                voice_session.transcript = transcript
                voice_session.extracted_data = extracted_data
                
                if voice_session.started_at:
                    voice_session.duration_seconds = int(
                        (voice_session.ended_at - voice_session.started_at).total_seconds()
                    )
                
                await db.commit()
                
                # Process results based on session type
                await process_session_results(
                    db, voice_session, session_type, extracted_data, metadata
                )
                
                try:
                    await websocket.send_json({
                        "type": "session_end",
                        "transcript": transcript,
                        "extracted_data": extracted_data
                    })
                except:
                    pass
            
            # Handle incoming messages from mobile app
            async def receive_from_client():
                try:
                    while True:
                        message = await websocket.receive()
                        
                        if message["type"] == "websocket.disconnect":
                            await audio_input_queue.put(None)
                            break
                        
                        if "bytes" in message:
                            # Audio data
                            await audio_input_queue.put(message["bytes"])
                        elif "text" in message:
                            # JSON control message
                            try:
                                msg = json.loads(message["text"])
                                if msg.get("type") == "end":
                                    await audio_input_queue.put(None)
                                    break
                            except json.JSONDecodeError:
                                pass
                
                except WebSocketDisconnect:
                    await audio_input_queue.put(None)
                except Exception as e:
                    print(f"Error receiving from client: {e}")
                    await audio_input_queue.put(None)
            
            # Check if Gemini is available
            if not gemini_voice_service.is_available():
                # Fallback: simulate a simple session
                await websocket.send_json({
                    "type": "transcript",
                    "text": "Hello! This is Calla. Voice service is currently unavailable. Please try again later."
                })
                await on_session_end(
                    "Voice service unavailable",
                    {"error": "Gemini API not configured"}
                )
                return
            
            # Run voice session
            await asyncio.gather(
                receive_from_client(),
                gemini_voice_service.run_voice_session(
                    config=config,
                    audio_input_queue=audio_input_queue,
                    audio_output_callback=audio_output_callback,
                    on_transcript_update=on_transcript_update,
                    on_session_end=on_session_end
                ),
                return_exceptions=True
            )
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


async def process_session_results(
    db,
    voice_session: VoiceSession,
    session_type: str,
    extracted_data: dict,
    metadata: dict
):
    """Process the results of a voice session based on its type"""
    
    if session_type == "onboarding":
        # Update patient with collected routine data
        patient = voice_session.patient
        if patient and extracted_data:
            from datetime import time
            
            def parse_time(time_str):
                if not time_str:
                    return None
                try:
                    parts = time_str.split(":")
                    return time(int(parts[0]), int(parts[1]))
                except:
                    return None
            
            if extracted_data.get("wake_time"):
                patient.wake_time = parse_time(extracted_data["wake_time"])
            if extracted_data.get("breakfast_time"):
                patient.breakfast_time = parse_time(extracted_data["breakfast_time"])
            if extracted_data.get("lunch_time"):
                patient.lunch_time = parse_time(extracted_data["lunch_time"])
            if extracted_data.get("dinner_time"):
                patient.dinner_time = parse_time(extracted_data["dinner_time"])
            if extracted_data.get("sleep_time"):
                patient.sleep_time = parse_time(extracted_data["sleep_time"])
            
            if extracted_data.get("consent_given"):
                patient.onboarding_completed = True
            
            # Create medications from extracted data
            for med in extracted_data.get("medications", []):
                if med.get("name"):
                    from app.models import Medication
                    medication = Medication(
                        patient_id=patient.id,
                        drug_name=med["name"],
                        dosage=med.get("dosage"),
                        frequency=med.get("frequency"),
                        timing_preference="with_food" if med.get("with_food") else None,
                    )
                    db.add(medication)
            
            await db.commit()
    
    elif session_type == "reminder":
        # Process reminder results
        reminder_id = metadata.get("reminder_id")
        if reminder_id:
            result = await db.execute(
                select(ScheduledReminder).where(ScheduledReminder.id == reminder_id)
            )
            reminder = result.scalar_one_or_none()
            
            if reminder:
                medication_taken = extracted_data.get("medication_taken", False)
                
                if medication_taken:
                    reminder.status = "confirmed"
                    
                    # Log adherence event
                    adherence_event = AdherenceEvent(
                        reminder_id=reminder.id,
                        medication_id=reminder.medication_id,
                        patient_id=reminder.patient_id,
                        voice_session_id=voice_session.id,
                        scheduled_time=reminder.scheduled_time,
                        confirmed_time=datetime.utcnow(),
                        confirmation_method="voice_session",
                        was_taken=True
                    )
                    db.add(adherence_event)
                else:
                    # Check if we should escalate
                    if extracted_data.get("escalate_to_caregiver"):
                        reminder.status = "escalated"
                    elif extracted_data.get("needs_refill"):
                        # Mark medication as needing refill
                        if reminder.medication:
                            reminder.medication.notes = f"NEEDS REFILL - {reminder.medication.notes or ''}"
                
                await db.commit()

