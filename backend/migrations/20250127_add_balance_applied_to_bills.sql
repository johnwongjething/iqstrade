-- Add balance_applied column to bill_of_lading table
-- Date: 2025-01-27
-- Purpose: Track balance applied to invoices

-- Add balance_applied column to track how much customer balance was applied to each invoice
ALTER TABLE bill_of_lading ADD COLUMN IF NOT EXISTS balance_applied NUMERIC(10,2) DEFAULT 0;

-- Add index for performance when querying by balance_applied
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_balance_applied ON bill_of_lading(balance_applied);

-- Update existing records to have 0 balance_applied
UPDATE bill_of_lading SET balance_applied = 0 WHERE balance_applied IS NULL; 