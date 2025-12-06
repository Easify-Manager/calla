"""Prescription chatbot service using LiteLLM with Gemini"""

import json
import re
from typing import Optional, List
import litellm
from app.config import settings
from app.external.rxnorm import RxNormClient

# Configure LiteLLM
litellm.set_verbose = False

PRESCRIPTION_SYSTEM_PROMPT = """You are a helpful assistant for adding medication prescriptions to Calla. 
You're chatting with a caregiver who wants to add a medication for their patient.

Your job:
1. Ask for the medication name (help them search if needed)
2. Confirm the dosage
3. Ask about frequency (once daily, twice daily, etc.)
4. Ask about timing (with food, before bed, etc.)
5. Ask about any special instructions
6. Summarize and confirm before saving

Be conversational and helpful. If they give partial information, ask follow-up questions.

When you have all required information, include a JSON block at the END of your message (after your human-readable response) in this exact format:
```json
{
  "ready_to_save": true,
  "medication": {
    "drug_name": "medication name",
    "dosage": "dosage amount",
    "frequency": "once_daily|twice_daily|three_times|as_needed",
    "timing_preference": "with_food|before_food|after_food|empty_stomach|bedtime",
    "specific_times": ["08:00", "20:00"],
    "notes": "any special instructions"
  }
}
```

IMPORTANT: The JSON block is for the system only and will be hidden from the user. Always write a friendly, human-readable confirmation message BEFORE the JSON block.

Common frequency mappings:
- "once a day" or "daily" → "once_daily"
- "twice a day" or "morning and night" → "twice_daily"  
- "three times a day" → "three_times"
- "as needed" or "when needed" → "as_needed"

If the medication info is incomplete, set "ready_to_save" to false and continue the conversation.
Do NOT include the JSON block until you have collected enough information (at minimum: drug name and frequency)."""


class ChatService:
    @staticmethod
    def _clean_response_text(response: str) -> str:
        """Remove JSON blocks from response text to show only human-readable content"""
        # Remove ```json ... ``` blocks
        cleaned = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', response)
        # Also remove any raw JSON blocks that might be at the end
        cleaned = re.sub(r'\{[^{}]*"ready_to_save"[^{}]*\}', '', cleaned)
        # Clean up extra whitespace and newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
    
    @staticmethod
    async def process_message(
        messages: List[dict],
        patient_name: str,
        patient_routine: dict = None
    ) -> dict:
        """Process a chat message for prescription entry using Gemini via LiteLLM"""
        
        # Add patient context to system prompt
        system_prompt = PRESCRIPTION_SYSTEM_PROMPT
        if patient_name:
            system_prompt += f"\n\nYou are adding medications for patient: {patient_name}"
        
        if patient_routine:
            routine_info = []
            if patient_routine.get("breakfast_time"):
                routine_info.append(f"Breakfast: {patient_routine['breakfast_time']}")
            if patient_routine.get("lunch_time"):
                routine_info.append(f"Lunch: {patient_routine['lunch_time']}")
            if patient_routine.get("dinner_time"):
                routine_info.append(f"Dinner: {patient_routine['dinner_time']}")
            if patient_routine.get("wake_time"):
                routine_info.append(f"Wake up: {patient_routine['wake_time']}")
            if patient_routine.get("sleep_time"):
                routine_info.append(f"Bedtime: {patient_routine['sleep_time']}")
            
            if routine_info:
                system_prompt += f"\n\nPatient's daily routine:\n" + "\n".join(routine_info)
                system_prompt += "\n\nUse this routine to suggest appropriate reminder times."
        
        try:
            # Check if Gemini API key is configured
            if not settings.GEMINI_API_KEY:
                return {
                    "message": "I apologize, but the chat service is not configured. Please set up your GEMINI_API_KEY in the backend .env file.",
                    "medication_data": None
                }
            
            # Prepare messages for LiteLLM
            full_messages = [{"role": "system", "content": system_prompt}]
            full_messages.extend(messages)
            
            # Call Gemini via LiteLLM
            response = await litellm.acompletion(
                model=settings.LLM_MODEL,  # "gemini/gemini-2.0-flash"
                messages=full_messages,
                api_key=settings.GEMINI_API_KEY,
                max_tokens=1000,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            # Parse response for medication data (before cleaning)
            medication_data = ChatService._extract_medication_data(response_text)
            
            # Clean the response text to remove JSON blocks for user display
            clean_message = ChatService._clean_response_text(response_text)
            
            return {
                "message": clean_message,
                "medication_data": medication_data
            }
        
        except litellm.AuthenticationError as e:
            print(f"Chat service auth error: {e}")
            return {
                "message": "Your Gemini API key appears to be invalid. Please check your GEMINI_API_KEY in the backend .env file and ensure it's a valid API key from Google AI Studio.",
                "medication_data": None
            }
        
        except Exception as e:
            error_str = str(e).lower()
            print(f"Chat service error: {e}")
            
            # Check for common API key errors
            if "api_key" in error_str or "authentication" in error_str or "invalid" in error_str:
                return {
                    "message": "There seems to be an issue with the API key. Please verify your GEMINI_API_KEY is correctly set in the backend .env file.",
                    "medication_data": None
                }
            
            return {
                "message": "I'm having trouble connecting to the AI service right now. Please try again in a moment.",
                "medication_data": None
            }
    
    @staticmethod
    def _extract_medication_data(response: str) -> Optional[dict]:
        """Extract medication JSON from response"""
        try:
            # Look for JSON block in response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    data = json.loads(json_str)
                    if data.get("ready_to_save"):
                        return data.get("medication")
            
            # Try to find raw JSON
            elif "{" in response and "ready_to_save" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                if end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    if data.get("ready_to_save"):
                        return data.get("medication")
        except json.JSONDecodeError:
            pass
        
        return None
    
    @staticmethod
    async def search_drugs_for_chat(query: str) -> str:
        """Search drugs and format for chat response"""
        results = await RxNormClient.search_drugs(query, max_results=5)
        
        if not results:
            return f"I couldn't find any medications matching '{query}'. Could you check the spelling or try a different name?"
        
        options = []
        for r in results:
            option = f"• {r.name}"
            if r.strengths:
                option += f" ({', '.join(r.strengths[:3])})"
            options.append(option)
        
        return f"I found these medications:\n" + "\n".join(options) + "\n\nWhich one does your patient take?"
