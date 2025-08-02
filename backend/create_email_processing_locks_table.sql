-- Create email processing locks table to prevent race conditions
CREATE TABLE IF NOT EXISTS email_processing_locks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(user_id)
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_email_processing_locks_expires 
ON email_processing_locks(expires_at);

-- Create index for user lookups
CREATE INDEX IF NOT EXISTS idx_email_processing_locks_user 
ON email_processing_locks(user_id);

-- Add comment
COMMENT ON TABLE email_processing_locks IS 'Prevents multiple users from processing emails simultaneously'; 