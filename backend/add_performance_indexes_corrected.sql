-- Performance Indexes for 100 Concurrent Users (Corrected Version)
-- Run this on your Railway PostgreSQL database
-- This version handles missing tables gracefully

-- First, create the missing audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    operation VARCHAR(255) NOT NULL,
    details TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

-- Customer emails table indexes
CREATE INDEX IF NOT EXISTS idx_customer_emails_created_at ON customer_emails(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender ON customer_emails(sender);
CREATE INDEX IF NOT EXISTS idx_customer_emails_message_id ON customer_emails(message_id);
CREATE INDEX IF NOT EXISTS idx_customer_emails_processed_for_payments ON customer_emails(processed_for_payments);

-- Bill of lading table indexes
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_customer_email ON bill_of_lading(customer_email);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_status ON bill_of_lading(status);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_created_at ON bill_of_lading(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_updated_at ON bill_of_lading(updated_at DESC);

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_approved ON users(approved);

-- Audit logs table indexes (now that table exists)
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_operation ON audit_logs(operation);

-- Customer email replies table indexes
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_customer_email_id ON customer_email_replies(customer_email_id);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_created_at ON customer_email_replies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_confidence_score ON customer_email_replies(confidence_score);

-- Password reset tokens table indexes
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_customer_status ON bill_of_lading(customer_email, status);
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender_created ON customer_emails(sender, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_operation ON audit_logs(user_id, operation);

-- Analyze tables to update statistics
ANALYZE customer_emails;
ANALYZE bill_of_lading;
ANALYZE users;
ANALYZE audit_logs;
ANALYZE customer_email_replies;
ANALYZE password_reset_tokens;

-- Verify all indexes were created successfully
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname; 