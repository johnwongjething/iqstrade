-- ========================================
-- OPENAI INTEGRATION DATABASE SCHEMA
-- Run this on Railway PostgreSQL database
-- ========================================

-- 1. Create customer_emails table for OpenAI email integration
CREATE TABLE IF NOT EXISTS customer_emails (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    attachments TEXT[], -- Array of attachment filenames
    bl_numbers TEXT[], -- Array of BL numbers found in email
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    classification VARCHAR(50), -- 'invoice_request', 'payment_receipt', 'general_enquiry'
    openai_processed BOOLEAN DEFAULT FALSE
);

-- 2. Create customer_email_replies table for AI-generated draft replies
CREATE TABLE IF NOT EXISTS customer_email_replies (
    id SERIAL PRIMARY KEY,
    customer_email_id INTEGER REFERENCES customer_emails(id) ON DELETE CASCADE,
    sender VARCHAR(255) NOT NULL, -- 'openai_draft' or actual sender
    body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_draft BOOLEAN DEFAULT TRUE,
    sent_at TIMESTAMP,
    sent_via VARCHAR(50), -- 'email', 'whatsapp', etc.
    -- Confidence scoring columns for auto-send functionality
    confidence_score FLOAT, -- 0.0 to 1.0 confidence score
    confidence_reasoning JSONB, -- Detailed reasoning for confidence score
    auto_send_recommended BOOLEAN DEFAULT FALSE, -- Whether AI recommended auto-send
    auto_sent BOOLEAN DEFAULT FALSE, -- Whether email was actually auto-sent
    auto_sent_at TIMESTAMP -- When auto-sent (if applicable)
);

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender ON customer_emails(sender);
CREATE INDEX IF NOT EXISTS idx_customer_emails_created_at ON customer_emails(created_at);
CREATE INDEX IF NOT EXISTS idx_customer_emails_classification ON customer_emails(classification);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_email_id ON customer_email_replies(customer_email_id);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_is_draft ON customer_email_replies(is_draft);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_confidence ON customer_email_replies(confidence_score);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_auto_send ON customer_email_replies(auto_send_recommended);

-- 4. Add any missing columns to existing tables (if they exist)
DO $$
BEGIN
    -- Add confidence_score column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'confidence_score') THEN
        ALTER TABLE customer_email_replies ADD COLUMN confidence_score FLOAT;
    END IF;
    
    -- Add confidence_reasoning column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'confidence_reasoning') THEN
        ALTER TABLE customer_email_replies ADD COLUMN confidence_reasoning JSONB;
    END IF;
    
    -- Add auto_send_recommended column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_send_recommended') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_send_recommended BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add auto_sent column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_sent') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_sent BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add auto_sent_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_sent_at') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_sent_at TIMESTAMP;
    END IF;
END $$;

-- 5. Create a view for easy querying of email status
CREATE OR REPLACE VIEW email_status_view AS
SELECT 
    ce.id,
    ce.sender,
    ce.subject,
    ce.classification,
    ce.created_at,
    COUNT(cer.id) as reply_count,
    MAX(CASE WHEN cer.is_draft = FALSE THEN cer.sent_at END) as last_sent_at,
    MAX(cer.confidence_score) as max_confidence,
    BOOL_OR(cer.auto_sent) as has_auto_sent,
    BOOL_OR(cer.auto_send_recommended) as has_auto_send_recommended
FROM customer_emails ce
LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
GROUP BY ce.id, ce.sender, ce.subject, ce.classification, ce.created_at;

-- 6. Insert sample data for testing (optional)
-- INSERT INTO customer_emails (sender, subject, body, classification) VALUES 
-- ('test@example.com', 'Test Email', 'This is a test email', 'general_enquiry');

-- 7. Grant necessary permissions (if using different users)
-- GRANT ALL PRIVILEGES ON TABLE customer_emails TO your_app_user;
-- GRANT ALL PRIVILEGES ON TABLE customer_email_replies TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE customer_emails_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE customer_email_replies_id_seq TO your_app_user; 