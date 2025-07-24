-- ========================================
-- SAFE OPENAI INTEGRATION UPDATE
-- This script safely adds missing columns to existing tables
-- WITHOUT affecting any existing data
-- ========================================

-- 1. Add missing columns to customer_emails table
DO $$
BEGIN
    -- Add processed_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_emails' AND column_name = 'processed_at') THEN
        ALTER TABLE customer_emails ADD COLUMN processed_at TIMESTAMP;
        RAISE NOTICE 'Added processed_at column to customer_emails';
    END IF;
    
    -- Add classification column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_emails' AND column_name = 'classification') THEN
        ALTER TABLE customer_emails ADD COLUMN classification VARCHAR(50);
        RAISE NOTICE 'Added classification column to customer_emails';
    END IF;
    
    -- Add openai_processed column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_emails' AND column_name = 'openai_processed') THEN
        ALTER TABLE customer_emails ADD COLUMN openai_processed BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added openai_processed column to customer_emails';
    END IF;
END $$;

-- 2. Add missing columns to customer_email_replies table
DO $$
BEGIN
    -- Add sent_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'sent_at') THEN
        ALTER TABLE customer_email_replies ADD COLUMN sent_at TIMESTAMP;
        RAISE NOTICE 'Added sent_at column to customer_email_replies';
    END IF;
    
    -- Add sent_via column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'sent_via') THEN
        ALTER TABLE customer_email_replies ADD COLUMN sent_via VARCHAR(50);
        RAISE NOTICE 'Added sent_via column to customer_email_replies';
    END IF;
    
    -- Add confidence_score column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'confidence_score') THEN
        ALTER TABLE customer_email_replies ADD COLUMN confidence_score FLOAT;
        RAISE NOTICE 'Added confidence_score column to customer_email_replies';
    END IF;
    
    -- Add confidence_reasoning column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'confidence_reasoning') THEN
        ALTER TABLE customer_email_replies ADD COLUMN confidence_reasoning JSONB;
        RAISE NOTICE 'Added confidence_reasoning column to customer_email_replies';
    END IF;
    
    -- Add auto_send_recommended column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_send_recommended') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_send_recommended BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added auto_send_recommended column to customer_email_replies';
    END IF;
    
    -- Add auto_sent column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_sent') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_sent BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added auto_sent column to customer_email_replies';
    END IF;
    
    -- Add auto_sent_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_email_replies' AND column_name = 'auto_sent_at') THEN
        ALTER TABLE customer_email_replies ADD COLUMN auto_sent_at TIMESTAMP;
        RAISE NOTICE 'Added auto_sent_at column to customer_email_replies';
    END IF;
END $$;

-- 3. Add missing indexes for better performance
DO $$
BEGIN
    -- Add indexes to customer_emails if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_emails_sender') THEN
        CREATE INDEX idx_customer_emails_sender ON customer_emails(sender);
        RAISE NOTICE 'Added idx_customer_emails_sender index';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_emails_created_at') THEN
        CREATE INDEX idx_customer_emails_created_at ON customer_emails(created_at);
        RAISE NOTICE 'Added idx_customer_emails_created_at index';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_emails_classification') THEN
        CREATE INDEX idx_customer_emails_classification ON customer_emails(classification);
        RAISE NOTICE 'Added idx_customer_emails_classification index';
    END IF;
    
    -- Add indexes to customer_email_replies if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_email_replies_email_id') THEN
        CREATE INDEX idx_customer_email_replies_email_id ON customer_email_replies(customer_email_id);
        RAISE NOTICE 'Added idx_customer_email_replies_email_id index';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_email_replies_is_draft') THEN
        CREATE INDEX idx_customer_email_replies_is_draft ON customer_email_replies(is_draft);
        RAISE NOTICE 'Added idx_customer_email_replies_is_draft index';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_email_replies_confidence') THEN
        CREATE INDEX idx_customer_email_replies_confidence ON customer_email_replies(confidence_score);
        RAISE NOTICE 'Added idx_customer_email_replies_confidence index';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_email_replies_auto_send') THEN
        CREATE INDEX idx_customer_email_replies_auto_send ON customer_email_replies(auto_send_recommended);
        RAISE NOTICE 'Added idx_customer_email_replies_auto_send index';
    END IF;
END $$;

-- 4. Create a view for easy querying of email status
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

-- 5. Verify the update
SELECT 
    'customer_emails' as table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
ORDER BY ordinal_position;

SELECT 
    'customer_email_replies' as table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name = 'customer_email_replies' 
ORDER BY ordinal_position;

-- 6. Show summary of what was added
SELECT 'Migration completed successfully!' as status; 