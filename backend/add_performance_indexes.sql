-- Performance Indexes for Customer Emails
-- Run this file to add indexes for faster email loading

-- Index for sorting by creation date (most important for pagination)
CREATE INDEX IF NOT EXISTS idx_customer_emails_created_at ON customer_emails(created_at DESC);

-- Index for sender filtering
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender ON customer_emails(sender);

-- Index for subject filtering
CREATE INDEX IF NOT EXISTS idx_customer_emails_subject ON customer_emails(subject);

-- Index for message_id (duplicate detection)
CREATE INDEX IF NOT EXISTS idx_customer_emails_message_id ON customer_emails(message_id);

-- Index for payment processing status
CREATE INDEX IF NOT EXISTS idx_customer_emails_processed ON customer_emails(processed_for_payments);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_customer_emails_sender_created ON customer_emails(sender, created_at DESC);

-- Index for email replies (for counting replies)
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_email_id ON customer_email_replies(customer_email_id);

-- Additional performance indexes
CREATE INDEX IF NOT EXISTS idx_customer_emails_created_at_desc ON customer_emails(created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_customer_email_replies_count ON customer_email_replies(customer_email_id, id);

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('customer_emails', 'customer_email_replies')
ORDER BY tablename, indexname; 