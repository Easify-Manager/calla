-- Calla Database Schema
-- This runs automatically when the PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Caregivers Table
CREATE TABLE IF NOT EXISTS caregivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caregiver_id UUID REFERENCES caregivers(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    -- Device token for push notifications
    device_token VARCHAR(255),
    device_platform VARCHAR(20),
    -- Daily routine
    wake_time TIME,
    sleep_time TIME,
    breakfast_time TIME,
    lunch_time TIME,
    dinner_time TIME,
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    voice_preference VARCHAR(50) DEFAULT 'Puck',
    call_retry_attempts INT DEFAULT 3,
    -- Status
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medications Table
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    drug_name VARCHAR(255) NOT NULL,
    rxcui VARCHAR(20),
    dosage VARCHAR(100),
    dosage_form VARCHAR(100),
    frequency VARCHAR(50),
    timing_preference VARCHAR(50),
    specific_times TEXT[],
    prescribing_doctor VARCHAR(255),
    pharmacy VARCHAR(255),
    refill_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scheduled Reminders Table
CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medication_id UUID REFERENCES medications(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    attempt_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voice Sessions Table (replaces call_logs)
CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    caregiver_id UUID REFERENCES caregivers(id),
    reminder_id UUID REFERENCES scheduled_reminders(id),
    session_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    transcript TEXT,
    extracted_data JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adherence Events Table
CREATE TABLE IF NOT EXISTS adherence_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reminder_id UUID REFERENCES scheduled_reminders(id),
    medication_id UUID REFERENCES medications(id),
    patient_id UUID REFERENCES patients(id),
    voice_session_id UUID REFERENCES voice_sessions(id),
    scheduled_time TIMESTAMP WITH TIME ZONE,
    confirmed_time TIMESTAMP WITH TIME ZONE,
    confirmation_method VARCHAR(50),
    was_taken BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_patients_caregiver ON patients(caregiver_id);
CREATE INDEX IF NOT EXISTS idx_patients_device ON patients(device_token);
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON scheduled_reminders(scheduled_time, status);
CREATE INDEX IF NOT EXISTS idx_reminders_patient ON scheduled_reminders(patient_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_patient ON voice_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_adherence_patient ON adherence_events(patient_id, scheduled_time);
