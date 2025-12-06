"""WebSocket handler for Twilio Media Streams → Gemini Live bridge"""

import asyncio
import json
import base64
import logging
import audioop
from fastapi import WebSocket
from typing import Optional
from app.voice.gemini_voice import gemini_voice_service
from app.models import ScheduledReminder, AdherenceEvent
from sqlalchemy import select
from datetime import datetime

logger = logging.getLogger(__name__)


class TwilioStreamHandler:
    """
    Bridges Twilio Media Streams with Gemini Live API for natural voice conversations.

    Flow:
    1. Twilio sends audio via WebSocket (mulaw, 8kHz)
    2. Convert mulaw → PCM 16-bit 16kHz for Gemini
    3. Send to Gemini Live API
    4. Receive Gemini audio response
    5. Convert PCM → mulaw for Twilio
    6. Send back to Twilio
    """

    def __init__(
        self,
        websocket: WebSocket,
        reminder_id: str,
        patient_name: str,
        medication_name: str,
        dosage: str
    ):
        self.websocket = websocket
        self.reminder_id = reminder_id
        self.patient_name = patient_name
        self.medication_name = medication_name
        self.dosage = dosage
        self.stream_sid = None
        self.call_sid = None
        self.confirmed = False
        self.transcript = []
        self.audio_input_queue = asyncio.Queue()
        self.session_ended = False

    async def handle(self):
        """Main handler for Twilio Media Stream"""
        try:
            # Create Gemini session config
            config = gemini_voice_service.create_session_config(
                session_type="reminder",
                variables={
                    "patient_name": self.patient_name,
                    "medication_name": self.medication_name,
                    "dosage": self.dosage,
                    "instructions": ""
                },
                voice_name="Puck"
            )

            # Modify the prompt to include confirmation markers
            config["system_instruction"] += """

IMPORTANT: After the conversation, include this JSON in your response:
```json
{
  "medication_taken": true/false,
  "needs_retry": true/false
}
```
"""

            # Start Gemini voice session
            gemini_task = asyncio.create_task(
                gemini_voice_service.run_voice_session(
                    config=config,
                    audio_input_queue=self.audio_input_queue,
                    audio_output_callback=self._send_audio_to_twilio,
                    on_transcript_update=self._on_transcript_update,
                    on_session_end=self._on_session_end
                )
            )

            # Process Twilio stream messages
            while not self.session_ended:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.receive_text(),
                        timeout=1.0
                    )
                    await self._process_twilio_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving Twilio message: {e}")
                    break

            # Signal end of audio input
            await self.audio_input_queue.put(None)
            await gemini_task

        except Exception as e:
            logger.error(f"Error in Twilio stream handler: {e}")
        finally:
            await self._cleanup()

    async def _process_twilio_message(self, message: str):
        """Process incoming Twilio WebSocket messages"""
        try:
            data = json.loads(message)
            event = data.get('event')

            if event == 'start':
                # Stream started
                self.stream_sid = data['start']['streamSid']
                self.call_sid = data['start']['callSid']
                logger.info(f"Twilio stream started: {self.stream_sid}")

            elif event == 'media':
                # Audio data from patient
                payload = data['media']['payload']

                # Decode mulaw audio (base64 → bytes)
                audio_mulaw = base64.b64decode(payload)

                # Convert mulaw 8kHz → PCM 16-bit 16kHz for Gemini
                audio_pcm = self._convert_mulaw_to_pcm16(audio_mulaw)

                # Send to Gemini via queue
                await self.audio_input_queue.put(audio_pcm)

            elif event == 'stop':
                # Stream ended
                logger.info(f"Twilio stream stopped: {self.stream_sid}")
                self.session_ended = True

        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}")

    async def _send_audio_to_twilio(self, audio_pcm: bytes):
        """Send Gemini audio response to Twilio"""
        try:
            # Convert PCM 16kHz → mulaw 8kHz for Twilio
            audio_mulaw = self._convert_pcm16_to_mulaw(audio_pcm)

            # Encode to base64
            audio_b64 = base64.b64encode(audio_mulaw).decode('utf-8')

            # Send to Twilio
            await self.websocket.send_json({
                'event': 'media',
                'streamSid': self.stream_sid,
                'media': {
                    'payload': audio_b64
                }
            })

        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {e}")

    async def _on_transcript_update(self, text: str):
        """Handle transcript updates from Gemini"""
        self.transcript.append(text)
        logger.info(f"Gemini: {text}")

    async def _on_session_end(self, full_transcript: str, extracted_data: dict):
        """Handle session end and save results"""
        try:
            # Check if medication was confirmed
            if extracted_data.get("medication_taken"):
                self.confirmed = True
                logger.info(f"Patient confirmed medication for reminder {self.reminder_id}")
            else:
                logger.info(f"Patient did not confirm - will retry for reminder {self.reminder_id}")

            # Save to database
            await self._save_results(extracted_data)

        except Exception as e:
            logger.error(f"Error handling session end: {e}")

    def _convert_mulaw_to_pcm16(self, mulaw_data: bytes) -> bytes:
        """
        Convert mulaw 8kHz to PCM 16-bit 16kHz

        Twilio sends: mulaw, 8kHz, mono
        Gemini expects: PCM 16-bit, 16kHz, mono
        """
        import audioop

        # Decode mulaw to PCM 16-bit at 8kHz
        pcm_8khz = audioop.ulaw2lin(mulaw_data, 2)

        # Upsample from 8kHz to 16kHz
        pcm_16khz, _ = audioop.ratecv(
            pcm_8khz,
            2,  # sample width (16-bit)
            1,  # channels (mono)
            8000,  # original rate
            16000,  # target rate
            None
        )

        return pcm_16khz

    def _convert_pcm16_to_mulaw(self, pcm_data: bytes) -> bytes:
        """
        Convert PCM 16-bit 16kHz to mulaw 8kHz

        Gemini sends: PCM 16-bit, 16kHz
        Twilio expects: mulaw, 8kHz
        """
        import audioop

        # Downsample from 16kHz to 8kHz
        pcm_8khz, _ = audioop.ratecv(
            pcm_data,
            2,  # sample width
            1,  # channels
            16000,  # original rate
            8000,  # target rate
            None
        )

        # Encode to mulaw
        mulaw = audioop.lin2ulaw(pcm_8khz, 2)

        return mulaw

    async def _save_results(self, extracted_data: dict):
        """Save conversation results to database"""
        try:
            # Get async database session
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Get the reminder
                result = await db.execute(
                    select(ScheduledReminder).where(ScheduledReminder.id == self.reminder_id)
                )
                reminder = result.scalar_one_or_none()

                if not reminder:
                    logger.error(f"Reminder {self.reminder_id} not found")
                    return

                if self.confirmed:
                    # Patient confirmed taking medication
                    reminder.status = "confirmed"

                    # Log adherence event
                    adherence = AdherenceEvent(
                        reminder_id=reminder.id,
                        medication_id=reminder.medication_id,
                        patient_id=reminder.patient_id,
                        scheduled_time=reminder.scheduled_time,
                        confirmed_time=datetime.utcnow(),
                        confirmation_method="twilio_gemini_call",
                        was_taken=True,
                        notes=f"Natural language confirmation. Transcript: {' ... '.join(self.transcript[:3])}"
                    )
                    db.add(adherence)
                    logger.info(f"Saved confirmation for reminder {self.reminder_id}")
                else:
                    # Patient didn't confirm - keep status as "calling" for retry
                    logger.info(f"No confirmation for reminder {self.reminder_id}, will retry")

                await db.commit()

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    async def _cleanup(self):
        """Clean up resources"""
        try:
            # Signal end of audio input if not already done
            if not self.session_ended:
                await self.audio_input_queue.put(None)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def handle_twilio_stream(
    websocket: WebSocket,
    reminder_id: str,
    patient_name: str,
    medication_name: str,
    dosage: str
):
    """Entry point for Twilio Media Stream WebSocket"""
    await websocket.accept()

    handler = TwilioStreamHandler(
        websocket=websocket,
        reminder_id=reminder_id,
        patient_name=patient_name,
        medication_name=medication_name,
        dosage=dosage
    )

    await handler.handle()
