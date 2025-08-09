-- Add "To" field to customer_emails table
-- Migration: 20250809_add_to_field.sql

-- Check if column exists and add it if it doesn't
DO $$
BEGIN
    -- Add "to" column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'to'
    ) THEN
        ALTER TABLE customer_emails ADD COLUMN "to" TEXT[];
        RAISE NOTICE 'Added "to" column to customer_emails table';
    ELSE
        RAISE NOTICE '"to" column already exists';
    END IF;
END $$;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_customer_emails_to ON customer_emails USING GIN("to");

-- Add comment for documentation
COMMENT ON COLUMN customer_emails."to" IS 'Array of "To" email addresses from original email';

-- Verify the changes
SELECT 
    'AFTER MIGRATION' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
AND column_name = 'to'
ORDER BY column_name;
