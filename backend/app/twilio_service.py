"""Twilio service for outbound voice calls to patients with Gemini Live AI"""

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TwilioService:
    """Handle Twilio voice calls for medication reminders using Gemini Live"""

    def __init__(self):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured")
            self.client = None
        else:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )

    def initiate_reminder_call(
        self,
        patient_phone: str,
        patient_name: str,
        medication_name: str,
        dosage: str,
        reminder_id: str,
        stream_url: str
    ) -> Optional[str]:
        """
        Initiate outbound call to patient for medication reminder.
        Uses Twilio Media Streams to connect to Gemini Live for natural conversation.

        Returns:
            call_sid if successful, None if failed
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None

        try:
            # Create TwiML that streams audio to our WebSocket
            twiml = VoiceResponse()

            # Brief greeting before connecting to Gemini
            twiml.say(
                f"Hello {patient_name}",
                voice='Polly.Joanna',
                language='en-US'
            )

            # Connect to Media Stream for Gemini Live conversation
            connect = Connect()
            stream = Stream(
                url=stream_url,
                track='both_tracks'  # Send both inbound and outbound audio
            )

            # Pass metadata to the stream
            stream.parameter(name='reminder_id', value=reminder_id)
            stream.parameter(name='patient_name', value=patient_name)
            stream.parameter(name='medication_name', value=medication_name)
            stream.parameter(name='dosage', value=dosage)

            connect.append(stream)
            twiml.append(connect)

            # Initiate the call
            call = self.client.calls.create(
                to=patient_phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                twiml=str(twiml),
                timeout=30,  # Ring for 30 seconds
                record=False
            )

            logger.info(f"Initiated call {call.sid} to {patient_phone} for reminder {reminder_id}")
            return call.sid

        except Exception as e:
            logger.error(f"Failed to initiate call: {e}")
            return None

    def initiate_caregiver_alert_call(
        self,
        caregiver_phone: str,
        caregiver_name: str,
        patient_name: str,
        medication_name: str,
        scheduled_time: str
    ) -> Optional[str]:
        """
        Alert caregiver that patient didn't respond to medication reminders.

        Returns:
            call_sid if successful, None if failed
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None

        try:
            # Create TwiML for caregiver alert
            twiml = VoiceResponse()
            twiml.say(
                f"Hello {caregiver_name}, this is an urgent alert from Calla. "
                f"{patient_name} has not responded to three medication reminder calls "
                f"for {medication_name}, scheduled at {scheduled_time}. "
                f"Please check on them as soon as possible. "
                f"This message will repeat once.",
                voice='alice',
                language='en-US'
            )

            # Repeat the alert
            twiml.pause(length=1)
            twiml.say(
                f"Alert: {patient_name} has not confirmed taking {medication_name}. "
                f"Please check on them.",
                voice='alice',
                language='en-US'
            )

            # Initiate the call
            call = self.client.calls.create(
                to=caregiver_phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                twiml=str(twiml),
                timeout=30,
                record=False
            )

            logger.info(f"Initiated alert call {call.sid} to caregiver at {caregiver_phone}")
            return call.sid

        except Exception as e:
            logger.error(f"Failed to initiate caregiver alert: {e}")
            return None

    def get_call_status(self, call_sid: str) -> Optional[dict]:
        """Get status of a call"""
        if not self.client:
            return None

        try:
            call = self.client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'direction': call.direction,
                'answered_by': call.answered_by
            }
        except Exception as e:
            logger.error(f"Failed to fetch call status: {e}")
            return None


# Global instance
twilio_service = TwilioService()
