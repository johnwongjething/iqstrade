-- Create customer_emails table for OpenAI email integration
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

-- Create customer_email_replies table for AI-generated draft replies
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender ON customer_emails(sender);
CREATE INDEX IF NOT EXISTS idx_customer_emails_created_at ON customer_emails(created_at);
CREATE INDEX IF NOT EXISTS idx_customer_emails_classification ON customer_emails(classification);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_email_id ON customer_email_replies(customer_email_id);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_is_draft ON customer_email_replies(is_draft);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_confidence ON customer_email_replies(confidence_score);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_auto_send ON customer_email_replies(auto_send_recommended);
