"""Medication routes"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.medications.schemas import MedicationCreate, MedicationUpdate, MedicationResponse, DrugSearchResult
from app.medications.service import MedicationService
from app.external.rxnorm import RxNormClient
from app.database import get_db
from app.auth.utils import get_current_caregiver
from app.models import Caregiver
from app.patients.service import PatientService

router = APIRouter(tags=["medications"])


@router.get("/api/patients/{patient_id}/medications", response_model=List[MedicationResponse])
async def get_patient_medications(
    patient_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get all medications for a patient"""
    # Verify patient belongs to caregiver
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    medications = await MedicationService.get_patient_medications(db, patient_id)
    return [MedicationResponse.from_model(med) for med in medications]


@router.post("/api/patients/{patient_id}/medications", response_model=MedicationResponse)
async def create_medication(
    patient_id: str,
    medication: MedicationCreate,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Create a new medication for a patient"""
    # Verify patient belongs to caregiver
    patient = await PatientService.get_patient(db, patient_id, str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Override patient_id from path
    medication.patient_id = patient_id
    
    created = await MedicationService.create_medication(db, medication)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create medication"
        )
    
    return MedicationResponse.from_model(created)


@router.get("/api/medications/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific medication"""
    medication = await MedicationService.get_medication(db, medication_id)
    if not medication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    # Verify ownership via patient
    patient = await PatientService.get_patient(db, str(medication.patient_id), str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    return MedicationResponse.from_model(medication)


@router.put("/api/medications/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: str,
    medication: MedicationUpdate,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Update a medication"""
    existing = await MedicationService.get_medication(db, medication_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    # Verify ownership via patient
    patient = await PatientService.get_patient(db, str(existing.patient_id), str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    updated = await MedicationService.update_medication(db, medication_id, medication)
    return MedicationResponse.from_model(updated)


@router.delete("/api/medications/{medication_id}")
async def delete_medication(
    medication_id: str,
    caregiver: Caregiver = Depends(get_current_caregiver),
    db: AsyncSession = Depends(get_db)
):
    """Delete a medication"""
    existing = await MedicationService.get_medication(db, medication_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    # Verify ownership via patient
    patient = await PatientService.get_patient(db, str(existing.patient_id), str(caregiver.id))
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    
    await MedicationService.delete_medication(db, medication_id)
    return {"message": "Medication deleted successfully"}


@router.post("/api/medications/search", response_model=List[DrugSearchResult])
async def search_drugs(
    query: str = Query(..., min_length=2),
    caregiver: Caregiver = Depends(get_current_caregiver)
):
    """Search for drugs using RxNorm API"""
    results = await RxNormClient.search_drugs(query, max_results=10)
    return results
