-- Migration: Add FCM tokens table for push notifications
-- Date: 2025-01-01
-- Description: Create table to store FCM tokens for push notifications

CREATE TABLE IF NOT EXISTS fcm_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Foreign key to users table
    CONSTRAINT fk_fcm_tokens_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_user_id ON fcm_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_token ON fcm_tokens(token);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_active ON fcm_tokens(is_active);

-- Add comments
COMMENT ON TABLE fcm_tokens IS 'Stores FCM tokens for push notifications';
COMMENT ON COLUMN fcm_tokens.user_id IS 'Reference to users table';
COMMENT ON COLUMN fcm_tokens.token IS 'Firebase Cloud Messaging token';
COMMENT ON COLUMN fcm_tokens.is_active IS 'Whether the token is still valid';

-- Insert sample data for testing (optional)
-- INSERT INTO fcm_tokens (user_id, token) VALUES (1, 'sample_token_for_testing'); 