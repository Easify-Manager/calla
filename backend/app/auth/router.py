"""Authentication routes"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import CaregiverCreate, CaregiverLogin, Token, CaregiverResponse
from app.auth.utils import (
    hash_password, 
    verify_password, 
    create_access_token,
    get_current_caregiver
)
from app.database import get_db
from app.models import Caregiver

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: CaregiverCreate, db: AsyncSession = Depends(get_db)):
    """Register a new caregiver account"""
    
    # Check if email exists
    result = await db.execute(
        select(Caregiver).where(Caregiver.email == user.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create caregiver
    caregiver = Caregiver(
        email=user.email,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
        phone_number=user.phone_number
    )
    db.add(caregiver)
    await db.commit()
    await db.refresh(caregiver)
    
    # Create token
    access_token = create_access_token(data={"sub": str(caregiver.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        caregiver=CaregiverResponse(
            id=str(caregiver.id),
            email=caregiver.email,
            full_name=caregiver.full_name,
            phone_number=caregiver.phone_number,
            created_at=caregiver.created_at
        )
    )


@router.post("/login", response_model=Token)
async def login(credentials: CaregiverLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    
    result = await db.execute(
        select(Caregiver).where(Caregiver.email == credentials.email)
    )
    caregiver = result.scalar_one_or_none()
    
    if not caregiver or not verify_password(credentials.password, caregiver.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": str(caregiver.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        caregiver=CaregiverResponse(
            id=str(caregiver.id),
            email=caregiver.email,
            full_name=caregiver.full_name,
            phone_number=caregiver.phone_number,
            created_at=caregiver.created_at
        )
    )


@router.get("/me", response_model=CaregiverResponse)
async def get_me(caregiver: Caregiver = Depends(get_current_caregiver)):
    """Get current caregiver info"""
    return CaregiverResponse(
        id=str(caregiver.id),
        email=caregiver.email,
        full_name=caregiver.full_name,
        phone_number=caregiver.phone_number
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(caregiver: Caregiver = Depends(get_current_caregiver)):
    """Refresh access token"""
    access_token = create_access_token(data={"sub": str(caregiver.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        caregiver=CaregiverResponse(
            id=str(caregiver.id),
            email=caregiver.email,
            full_name=caregiver.full_name,
            phone_number=caregiver.phone_number,
            created_at=caregiver.created_at
        )
    )
