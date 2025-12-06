import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # Database - PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://medvoice:medvoice_secret@localhost:5432/medvoice"
    DATABASE_URL_SYNC: str = "postgresql://medvoice:medvoice_secret@localhost:5432/medvoice"
    
    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Gemini API (for both voice and chatbot)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # LiteLLM model for chatbot
    LLM_MODEL: str = "gemini/gemini-2.0-flash"
    
    # Gemini Live model for voice
    GEMINI_LIVE_MODEL: str = "gemini-2.0-flash-exp"
    
    # Firebase (for push notifications)
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"
    
    # Drug APIs
    OPENFDA_API_KEY: str = ""
    
    # Twilio (SMS fallback)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
