-- Migration: Add failed_attempts and lockout_until to users table for account lockout
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_until TIMESTAMP NULL;
