-- Railway Database Fix for Email System
-- Run this in Railway Dashboard > Database > Query

-- Check current table structure
SELECT 
    'CURRENT TABLE STRUCTURE' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customer_emails'
ORDER BY ordinal_position;

-- Add from_addr column if it doesn't exist
DO $$
BEGIN
    -- Check if from_addr column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'from_addr'
    ) THEN
        -- Add the column
        ALTER TABLE customer_emails ADD COLUMN from_addr VARCHAR(255);
        RAISE NOTICE 'Added from_addr column to customer_emails table';
    ELSE
        RAISE NOTICE 'from_addr column already exists';
    END IF;
END $$;

-- Verify the fix
SELECT 
    'AFTER FIX' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customer_emails'
ORDER BY ordinal_position;

-- Check if all required columns exist
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    column_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = required_cols.column_name
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
FROM (
    VALUES 
        ('id'),
        ('subject'),
        ('body'),
        ('from_addr'),
        ('attachments'),
        ('processed_for_payments')
) AS required_cols(column_name);

-- Show table summary
SELECT 
    'TABLE SUMMARY' as section,
    COUNT(*) as total_columns,
    COUNT(CASE WHEN column_name IN ('id', 'subject', 'body', 'from_addr', 'attachments', 'processed_for_payments') THEN 1 END) as required_columns_present
FROM information_schema.columns
WHERE table_name = 'customer_emails'; 