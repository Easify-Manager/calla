-- Migration to add last_attempt_time column to scheduled_reminders table
-- Run this SQL script on your PostgreSQL database

ALTER TABLE scheduled_reminders
ADD COLUMN IF NOT EXISTS last_attempt_time TIMESTAMP WITH TIME ZONE;

-- Update existing "calling" reminders to have a last_attempt_time if they don't have one
UPDATE scheduled_reminders
SET last_attempt_time = created_at
WHERE status = 'calling' AND last_attempt_time IS NULL;
