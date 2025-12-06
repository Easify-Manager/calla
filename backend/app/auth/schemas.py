from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CaregiverBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None


class CaregiverCreate(CaregiverBase):
    password: str


class CaregiverLogin(BaseModel):
    email: EmailStr
    password: str


class CaregiverResponse(CaregiverBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    caregiver: CaregiverResponse


class TokenData(BaseModel):
    caregiver_id: Optional[str] = None

