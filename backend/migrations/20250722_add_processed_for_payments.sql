-- Add processed_for_payments column to customer_emails table
-- This column is used to track which emails have been processed for payment receipt handling

DO $$
BEGIN
    -- Add processed_for_payments column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customer_emails' AND column_name = 'processed_for_payments') THEN
        ALTER TABLE customer_emails ADD COLUMN processed_for_payments BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added processed_for_payments column to customer_emails';
    ELSE
        RAISE NOTICE 'processed_for_payments column already exists in customer_emails';
    END IF;
END $$;

-- Create index for better performance on payment processing queries
CREATE INDEX IF NOT EXISTS idx_customer_emails_processed_for_payments 
ON customer_emails(processed_for_payments);

-- Verify the column was added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
AND column_name = 'processed_for_payments'; 