"""Prescription chatbot routes"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.chat.service import ChatService
from app.database import get_db
from app.auth.utils import get_current_caregiver
from app.patients.service import PatientService
from app.medications.service import MedicationService
from app.medications.schemas import MedicationCreate
from app.models import Caregiver

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    patient_id: str
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    message: str
    medication_data: Optional[dict] = None
    medication_saved: bool = False


@router.post("/prescription", response_model=ChatResponse)
async def prescription_chat(
    request: ChatRequest,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat endpoint for adding medications via conversation.
    
    Send messages and receive AI responses. When the AI has collected
    enough information, it will return medication_data that can be saved.
    """
    # Verify patient belongs to caregiver
    patient = await PatientService.get_patient(db, request.patient_id, str(caregiver.id))
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Prepare patient routine
    patient_routine = {}
    if patient.wake_time:
        patient_routine["wake_time"] = patient.wake_time.isoformat()
    if patient.breakfast_time:
        patient_routine["breakfast_time"] = patient.breakfast_time.isoformat()
    if patient.lunch_time:
        patient_routine["lunch_time"] = patient.lunch_time.isoformat()
    if patient.dinner_time:
        patient_routine["dinner_time"] = patient.dinner_time.isoformat()
    if patient.sleep_time:
        patient_routine["sleep_time"] = patient.sleep_time.isoformat()
    
    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Process the message
    result = await ChatService.process_message(
        messages=messages,
        patient_name=patient.full_name,
        patient_routine=patient_routine
    )
    
    medication_saved = False
    
    # If medication data is ready, save it
    if result["medication_data"]:
        try:
            med_data = result["medication_data"]
            medication = MedicationCreate(
                patient_id=str(patient.id),
                drug_name=med_data.get("drug_name", "Unknown"),
                dosage=med_data.get("dosage"),
                frequency=med_data.get("frequency"),
                timing_preference=med_data.get("timing_preference"),
                specific_times=med_data.get("specific_times"),
                notes=med_data.get("notes")
            )
            
            created = await MedicationService.create_medication(db, medication)
            if created:
                medication_saved = True
                result["message"] += f"\n\n✅ I've saved {med_data.get('drug_name')} to {patient.full_name}'s medications!"
        except Exception as e:
            print(f"Error saving medication: {e}")
            result["message"] += "\n\n⚠️ I collected the medication info but had trouble saving it. Please try again."
    
    return ChatResponse(
        message=result["message"],
        medication_data=result["medication_data"],
        medication_saved=medication_saved
    )


@router.post("/search-drugs")
async def search_drugs_chat(
    query: str,
    caregiver: Caregiver = Depends(get_current_caregiver)
):
    """Search drugs and get formatted response for chat"""
    response = await ChatService.search_drugs_for_chat(query)
    return {"message": response}
