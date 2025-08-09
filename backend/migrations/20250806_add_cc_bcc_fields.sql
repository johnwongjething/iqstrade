-- Add CC, BCC, and Reply-To fields to customer_emails table
-- Migration: 20250806_add_cc_bcc_fields.sql

-- Check if columns exist and add them if they don't
DO $$
BEGIN
    -- Add CC column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'cc'
    ) THEN
        ALTER TABLE customer_emails ADD COLUMN cc TEXT[];
        RAISE NOTICE 'Added cc column to customer_emails table';
    ELSE
        RAISE NOTICE 'cc column already exists';
    END IF;

    -- Add BCC column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'bcc'
    ) THEN
        ALTER TABLE customer_emails ADD COLUMN bcc TEXT[];
        RAISE NOTICE 'Added bcc column to customer_emails table';
    ELSE
        RAISE NOTICE 'bcc column already exists';
    END IF;

    -- Add Reply-To column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'reply_to'
    ) THEN
        ALTER TABLE customer_emails ADD COLUMN reply_to TEXT[];
        RAISE NOTICE 'Added reply_to column to customer_emails table';
    ELSE
        RAISE NOTICE 'reply_to column already exists';
    END IF;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_cc ON customer_emails USING GIN(cc);
CREATE INDEX IF NOT EXISTS idx_customer_emails_bcc ON customer_emails USING GIN(bcc);
CREATE INDEX IF NOT EXISTS idx_customer_emails_reply_to ON customer_emails USING GIN(reply_to);

-- Add comments for documentation
COMMENT ON COLUMN customer_emails.cc IS 'Array of CC email addresses from original email';
COMMENT ON COLUMN customer_emails.bcc IS 'Array of BCC email addresses from original email';
COMMENT ON COLUMN customer_emails.reply_to IS 'Array of Reply-To email addresses from original email';

-- Verify the changes
SELECT 
    'AFTER MIGRATION' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customer_emails'
AND column_name IN ('cc', 'bcc', 'reply_to')
ORDER BY column_name;
