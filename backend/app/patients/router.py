from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.patients.schemas import PatientCreate, PatientUpdate, PatientResponse, AdherenceStats
from app.patients.service import PatientService
from app.auth.utils import get_current_caregiver
from app.voice.service import VoiceService
from app.database import get_db
from app.models import Caregiver

router = APIRouter(prefix="/api/patients", tags=["patients"])


def patient_to_response(patient) -> PatientResponse:
    """Convert Patient model to response schema"""
    return PatientResponse(
        id=str(patient.id),
        caregiver_id=str(patient.caregiver_id),
        full_name=patient.full_name,
        phone_number=patient.phone_number,
        date_of_birth=patient.date_of_birth,
        wake_time=patient.wake_time.isoformat() if patient.wake_time else None,
        sleep_time=patient.sleep_time.isoformat() if patient.sleep_time else None,
        breakfast_time=patient.breakfast_time.isoformat() if patient.breakfast_time else None,
        lunch_time=patient.lunch_time.isoformat() if patient.lunch_time else None,
        dinner_time=patient.dinner_time.isoformat() if patient.dinner_time else None,
        preferred_language=patient.preferred_language,
        voice_preference=patient.voice_preference or "Puck",
        call_retry_attempts=patient.call_retry_attempts,
        onboarding_completed=patient.onboarding_completed,
        device_token=patient.device_token,
        device_platform=patient.device_platform,
        has_device=bool(patient.device_token),
        created_at=patient.created_at
    )


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """List all patients for the current caregiver"""
    patients = await PatientService.get_all_patients(db, str(caregiver.id))
    return [patient_to_response(p) for p in patients]


@router.post("", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient"""
    new_patient = await PatientService.create_patient(db, str(caregiver.id), patient)
    
    if not new_patient:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient"
        )
    
    # Note: Onboarding call will be triggered after patient registers their device
    # The patient needs to install the app and register their device first
    
    return patient_to_response(new_patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific patient"""
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient_to_response(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient: PatientUpdate,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Update a patient"""
    updated = await PatientService.update_patient(db, patient_id, str(caregiver.id), patient)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient_to_response(updated)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Delete a patient"""
    deleted = await PatientService.delete_patient(db, patient_id, str(caregiver.id))
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return {"message": "Patient deleted successfully"}


@router.post("/{patient_id}/trigger-call")
async def trigger_call(
    patient_id: str,
    session_type: str = "onboarding",
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a voice call to a patient.
    
    The patient must have the app installed and their device registered.
    This sends a push notification that shows an incoming call UI.
    
    session_type: onboarding, reminder, or escalation
    """
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if not patient.device_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient has not registered their device. They need to install the app first."
        )
    
    try:
        if session_type == "onboarding":
            session_id = await VoiceService.trigger_onboarding_call(
                db=db,
                patient_id=str(patient.id),
                patient_name=patient.full_name,
                caregiver_name=caregiver.full_name,
                caregiver_id=str(caregiver.id)
            )
        else:
            session_id = await VoiceService.trigger_call(
                db=db,
                patient_id=str(patient.id),
                session_type=session_type,
                caregiver_id=str(caregiver.id),
                metadata={
                    "patient_name": patient.full_name,
                    "caregiver_name": caregiver.full_name
                }
            )
        
        if session_id:
            return {"message": "Call triggered", "session_id": session_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger call"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger call: {str(e)}"
        )


@router.get("/{patient_id}/adherence-stats", response_model=AdherenceStats)
async def get_adherence_stats(
    patient_id: str,
    days: int = 30,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get adherence statistics for a patient"""
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    stats = await PatientService.get_adherence_stats(db, patient_id, days)
    return stats
