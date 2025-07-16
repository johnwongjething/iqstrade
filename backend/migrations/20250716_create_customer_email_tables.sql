-- Migration: Create customer_emails and customer_email_replies tables

CREATE TABLE IF NOT EXISTS customer_emails (
    id SERIAL PRIMARY KEY,
    sender TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    attachments JSONB,
    bl_numbers TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_email_replies (
    id SERIAL PRIMARY KEY,
    customer_email_id INTEGER REFERENCES customer_emails(id) ON DELETE CASCADE,
    sender TEXT NOT NULL,
    body TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster lookup by B/L number (optional)
CREATE INDEX IF NOT EXISTS idx_customer_emails_bl_numbers ON customer_emails USING GIN (bl_numbers);
