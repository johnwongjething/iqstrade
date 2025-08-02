-- Add Payment Dates Field for Allinpay Records
-- This adds a field to track when 85% payment was received

-- First, let's check if the field already exists
SELECT 
    'CHECKING EXISTING FIELDS' as section,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'bill_of_lading' 
  AND column_name IN ('payment_85_percent_date', 'first_payment_date', 'initial_payment_date')
ORDER BY column_name;

-- Add the field for 85% payment date if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bill_of_lading' 
        AND column_name = 'payment_85_percent_date'
    ) THEN
        ALTER TABLE bill_of_lading 
        ADD COLUMN payment_85_percent_date TIMESTAMP;
        
        COMMENT ON COLUMN bill_of_lading.payment_85_percent_date IS 'Date when 85% payment was received for Allinpay records';
        
        RAISE NOTICE 'Added payment_85_percent_date column';
    ELSE
        RAISE NOTICE 'payment_85_percent_date column already exists';
    END IF;
END $$;

-- Show the updated table structure
SELECT 
    'UPDATED TABLE STRUCTURE' as section,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'bill_of_lading' 
  AND column_name IN ('created_at', 'updated_at', 'completed_at', 'payment_85_percent_date')
ORDER BY column_name; 