"""Gemini 2.0 Flash Live API integration for real-time voice conversations"""

import asyncio
from typing import Optional, Callable, Any
from app.config import settings

# Agent prompts for different session types
AGENT_PROMPTS = {
    "onboarding": """
You are Calla, a friendly healthcare assistant helping to set up medication reminders. 
The caregiver {{caregiver_name}} has registered {{patient_name}} for medication reminders.

Your goals:
1. Greet warmly and confirm you're speaking with the right person
2. Learn about their daily routine (wake up, meals, bedtime)
3. Collect information about their current medications
4. Explain how reminder calls will work

Guidelines:
- Speak slowly and clearly
- Use simple language, avoid medical jargon
- Be patient with repetition
- Keep the conversation warm and reassuring
- Confirm important details by repeating them back

Start by introducing yourself and asking if now is a good time to chat for about 5 minutes.

At the end, summarize what you learned and tell them they'll receive friendly reminder calls.

When you have collected all the information, include this JSON in your response:
```json
{
  "wake_time": "HH:MM",
  "breakfast_time": "HH:MM",
  "lunch_time": "HH:MM",
  "dinner_time": "HH:MM",
  "sleep_time": "HH:MM",
  "medications": [
    {"name": "drug name", "dosage": "amount", "frequency": "how often", "with_food": true/false}
  ],
  "consent_given": true/false
}
```
""",
    
    "reminder": """
You are Calla, a friendly medication reminder assistant.
You're reminding {{patient_name}} to take their {{medication_name}} ({{dosage}}).

Instructions for this medication: {{instructions}}

Your goals:
1. Greet them warmly by name
2. Remind them it's time for their medication
3. Confirm whether they've taken it
4. If not taken, gently encourage them
5. Keep the call brief (under 2 minutes)

If they confirm they took it, thank them warmly.
If they haven't, encourage them to take it now.
If they refuse, ask if there's a reason (side effects, ran out, etc.)
If they seem confused, offer to have their caregiver call them.

Be warm and encouraging, never nagging.

At the end of the conversation, include this JSON:
```json
{
  "medication_taken": true/false,
  "reason_not_taken": "reason if not taken",
  "needs_refill": true/false,
  "escalate_to_caregiver": true/false
}
```
""",
    
    "escalation": """
You are Calla, calling to alert a caregiver about a medication concern.

Alert type: {{alert_type}}
Patient: {{patient_name}}
Details: {{alert_details}}

Your goals:
1. Identify yourself and the purpose of the call
2. Clearly communicate the alert
3. Provide relevant details
4. Ask if they can follow up with the patient
5. Offer to retry contacting the patient if requested

Keep this call brief and professional.

At the end, include this JSON:
```json
{
  "caregiver_acknowledged": true/false,
  "will_follow_up": true/false,
  "requested_retry": true/false
}
```
"""
}


def get_agent_prompt(session_type: str, variables: dict = None) -> str:
    """Get the agent prompt for a session type with variables substituted"""
    prompt = AGENT_PROMPTS.get(session_type, AGENT_PROMPTS["reminder"])
    
    if variables:
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value or ""))
    
    return prompt


class GeminiVoiceService:
    """Service for managing Gemini Live API voice sessions"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_LIVE_MODEL
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Gemini client"""
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("google-genai package not installed")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
        return self._client
    
    def is_available(self) -> bool:
        """Check if Gemini voice service is available"""
        return self.api_key and self.client is not None
    
    def create_session_config(
        self,
        session_type: str,
        variables: dict = None,
        voice_name: str = "Puck"
    ) -> dict:
        """
        Create a voice session configuration.
        Returns session config to be used by the mobile app via WebSocket.
        
        Voice options: Puck, Charon, Kore, Fenrir, Aoede
        """
        system_prompt = get_agent_prompt(session_type, variables)
        
        return {
            "model": self.model,
            "system_instruction": system_prompt,
            "voice_config": {
                "voice_name": voice_name,
            },
            "response_modalities": ["AUDIO", "TEXT"],
            "session_type": session_type,
            "variables": variables or {},
        }
    
    async def run_voice_session(
        self,
        config: dict,
        audio_input_queue: asyncio.Queue,
        audio_output_callback: Callable[[bytes], Any],
        on_transcript_update: Callable[[str], Any],
        on_session_end: Callable[[str, dict], Any]
    ):
        """
        Run a real-time voice session with Gemini Live API.
        
        This method handles the bidirectional audio streaming between
        the mobile app (via WebSocket) and Gemini.
        
        Args:
            config: Session configuration from create_session_config()
            audio_input_queue: Queue receiving audio chunks from the user
            audio_output_callback: Callback to send audio to the user
            on_transcript_update: Callback for transcript updates
            on_session_end: Callback when session ends (transcript, extracted_data)
        """
        if not self.is_available():
            await on_session_end("Voice service not available", {})
            return
        
        try:
            from google.genai import types
            
            full_transcript = []
            extracted_data = {}
            
            async with self.client.aio.live.connect(
                model=config["model"],
                config=types.LiveConnectConfig(
                    system_instruction=types.Content(
                        parts=[types.Part(text=config["system_instruction"])]
                    ),
                    voice=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=config["voice_config"]["voice_name"]
                        )
                    ),
                    response_modalities=config["response_modalities"]
                )
            ) as session:
                
                async def send_audio():
                    """Send audio chunks from the user to Gemini"""
                    try:
                        while True:
                            audio_chunk = await audio_input_queue.get()
                            if audio_chunk is None:  # End signal
                                break
                            await session.send(
                                types.LiveClientRealtimeInput(
                                    media_chunks=[
                                        types.Blob(data=audio_chunk, mime_type="audio/pcm")
                                    ]
                                )
                            )
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                
                async def receive_responses():
                    """Receive audio/text responses from Gemini"""
                    try:
                        async for response in session.receive():
                            # Handle audio response
                            if hasattr(response, 'data') and response.data:
                                await audio_output_callback(response.data)
                            
                            # Handle text (transcript)
                            if hasattr(response, 'text') and response.text:
                                full_transcript.append(response.text)
                                await on_transcript_update(response.text)
                                
                                # Try to extract JSON data from response
                                if "```json" in response.text:
                                    try:
                                        import json
                                        start = response.text.find("```json") + 7
                                        end = response.text.find("```", start)
                                        if end > start:
                                            json_str = response.text[start:end].strip()
                                            extracted_data.update(json.loads(json_str))
                                    except:
                                        pass
                    except Exception as e:
                        print(f"Error receiving responses: {e}")
                
                # Run send and receive concurrently
                await asyncio.gather(
                    send_audio(),
                    receive_responses(),
                    return_exceptions=True
                )
            
            # Session ended
            await on_session_end(
                "\n".join(full_transcript),
                extracted_data
            )
        
        except ImportError:
            print("google-genai package not properly installed")
            await on_session_end("Voice service error", {})
        except Exception as e:
            print(f"Voice session error: {e}")
            await on_session_end(f"Error: {str(e)}", {})


# Singleton instance
gemini_voice_service = GeminiVoiceService()

