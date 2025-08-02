-- Fix Customer Emails Table
-- Add missing from_addr column and fix column names

-- Check current table structure
SELECT 
    'CURRENT TABLE STRUCTURE' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customer_emails'
ORDER BY ordinal_position;

-- Check if from_addr column exists
SELECT 
    'CHECKING FROM_ADDR COLUMN' as section,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'from_addr'
    ) as from_addr_exists,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'from_address'
    ) as from_address_exists;

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
        
        -- If from_address exists, copy data from it
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'from_address'
        ) THEN
            UPDATE customer_emails SET from_addr = from_address WHERE from_addr IS NULL;
            RAISE NOTICE 'Copied data from from_address to from_addr';
        END IF;
        
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
    'id' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'id'
    ) as exists
UNION ALL
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    'subject' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'subject'
    ) as exists
UNION ALL
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    'body' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'body'
    ) as exists
UNION ALL
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    'from_addr' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'from_addr'
    ) as exists
UNION ALL
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    'attachments' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'attachments'
    ) as exists
UNION ALL
SELECT 
    'REQUIRED COLUMNS CHECK' as section,
    'processed_for_payments' as column_name,
    EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        AND column_name = 'processed_for_payments'
    ) as exists; 