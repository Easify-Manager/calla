from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class MedicationBase(BaseModel):
    drug_name: str
    rxcui: Optional[str] = None
    dosage: Optional[str] = None
    dosage_form: Optional[str] = None
    frequency: Optional[str] = None  # once_daily, twice_daily, three_times, as_needed
    timing_preference: Optional[str] = None  # with_food, before_food, after_food, empty_stomach, bedtime
    specific_times: Optional[List[str]] = None  # ["08:00", "20:00"]
    prescribing_doctor: Optional[str] = None
    pharmacy: Optional[str] = None
    refill_date: Optional[date] = None
    notes: Optional[str] = None


class MedicationCreate(MedicationBase):
    patient_id: Optional[str] = None  # Will be set from path


class MedicationUpdate(BaseModel):
    drug_name: Optional[str] = None
    rxcui: Optional[str] = None
    dosage: Optional[str] = None
    dosage_form: Optional[str] = None
    frequency: Optional[str] = None
    timing_preference: Optional[str] = None
    specific_times: Optional[List[str]] = None
    prescribing_doctor: Optional[str] = None
    pharmacy: Optional[str] = None
    refill_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MedicationResponse(MedicationBase):
    id: str
    patient_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
    
    @classmethod
    def from_model(cls, medication):
        return cls(
            id=str(medication.id),
            patient_id=str(medication.patient_id),
            drug_name=medication.drug_name,
            rxcui=medication.rxcui,
            dosage=medication.dosage,
            dosage_form=medication.dosage_form,
            frequency=medication.frequency,
            timing_preference=medication.timing_preference,
            specific_times=medication.specific_times,
            prescribing_doctor=medication.prescribing_doctor,
            pharmacy=medication.pharmacy,
            refill_date=medication.refill_date,
            notes=medication.notes,
            is_active=medication.is_active,
            created_at=medication.created_at
        )


class DrugSearchResult(BaseModel):
    rxcui: str
    name: str
    synonym: Optional[str] = None
    strengths: Optional[List[str]] = None
