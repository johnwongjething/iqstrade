-- Add status column to customer_emails table
-- Migration: 20250801_add_status_to_customer_emails.sql

-- Check if status column exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'status'
    ) THEN
        -- Add status column
        ALTER TABLE customer_emails ADD COLUMN status VARCHAR(50) DEFAULT 'New';
        
        -- Add updated_at column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE customer_emails ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        RAISE NOTICE 'Added status and updated_at columns to customer_emails table';
    ELSE
        RAISE NOTICE 'status column already exists';
    END IF;
END $$;

-- Create index on status column for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_status ON customer_emails(status);

-- Update existing records to have a default status
UPDATE customer_emails SET status = 'New' WHERE status IS NULL;

-- Verify the changes
SELECT 
    'AFTER MIGRATION' as section,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'customer_emails'
ORDER BY ordinal_position; 