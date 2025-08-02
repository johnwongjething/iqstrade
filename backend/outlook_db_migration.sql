-- Outlook Add-in Database Migration
-- Add Outlook-specific fields and tables for better multi-user support

-- Add Outlook tracking fields to customer_emails table
ALTER TABLE customer_emails 
ADD COLUMN IF NOT EXISTS outlook_message_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS processed_by_outlook BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS outlook_user_id VARCHAR(255);

-- Create table for AI drafts
CREATE TABLE IF NOT EXISTS ai_drafts (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES customer_emails(id) ON DELETE CASCADE,
    draft_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    sent_by VARCHAR(255),
    draft_type VARCHAR(50) DEFAULT 'ai_generated' -- ai_generated, user_edited, final
);

-- Create table for Outlook user sessions
CREATE TABLE IF NOT EXISTS outlook_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_outlook_message_id 
ON customer_emails(outlook_message_id);

CREATE INDEX IF NOT EXISTS idx_customer_emails_outlook_user_id 
ON customer_emails(outlook_user_id);

CREATE INDEX IF NOT EXISTS idx_ai_drafts_email_id 
ON ai_drafts(email_id);

CREATE INDEX IF NOT EXISTS idx_ai_drafts_sent_at 
ON ai_drafts(sent_at);

CREATE INDEX IF NOT EXISTS idx_outlook_sessions_user_id 
ON outlook_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_outlook_sessions_token 
ON outlook_sessions(session_token);

-- Add comments for documentation
COMMENT ON COLUMN customer_emails.outlook_message_id IS 'Outlook message ID for tracking';
COMMENT ON COLUMN customer_emails.processed_by_outlook IS 'Whether email was processed via Outlook add-in';
COMMENT ON COLUMN customer_emails.outlook_user_id IS 'ID of Outlook user who processed the email';
COMMENT ON TABLE ai_drafts IS 'Stores AI-generated and user-edited draft responses';
COMMENT ON TABLE outlook_sessions IS 'Tracks active Outlook user sessions';

-- Verify the migration
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as total_emails,
    COUNT(CASE WHEN outlook_message_id IS NOT NULL THEN 1 END) as outlook_processed_emails
FROM customer_emails; 