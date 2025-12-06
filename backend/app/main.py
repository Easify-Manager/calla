from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.auth.router import router as auth_router
from app.patients.router import router as patients_router
from app.medications.router import router as medications_router
from app.voice.router import router as voice_router
from app.chat.router import router as chat_router
from app.reminders.router import router as reminders_router
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.notifications import init_firebase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("Starting Calla API...")
    print(f"Database: {settings.DATABASE_URL[:50]}...")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"Voice Model: {settings.GEMINI_LIVE_MODEL}")
    
    # Initialize Firebase for push notifications
    init_firebase()
    
    # Start scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    print("Shutting down Calla API...")
    stop_scheduler()


app = FastAPI(
    title="Calla API",
    description="Voice-First Medication Adherence Platform API using Gemini Live",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8081",  # Expo
        "http://localhost:19006",  # Expo web
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(medications_router)
app.include_router(voice_router)
app.include_router(chat_router)
app.include_router(reminders_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Calla API",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    from app.voice.gemini_voice import gemini_voice_service
    
    return {
        "status": "healthy",
        "database": "postgresql",
        "voice_ai": "available" if gemini_voice_service.is_available() else "not configured",
        "llm": f"configured ({settings.LLM_MODEL})" if settings.GEMINI_API_KEY else "not configured",
        "push_notifications": "check firebase credentials"
    }
