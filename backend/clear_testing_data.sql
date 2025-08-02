-- Clear Testing Data from bill_of_lading table
-- This will remove all records but keep the table structure intact

-- First, let's see what we're about to delete
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show a sample of records before deletion
SELECT 
    id, 
    customer_name, 
    bl_number, 
    status, 
    payment_method, 
    reserve_status,
    ctn_fee, 
    service_fee,
    (ctn_fee + service_fee) as total_amount
FROM bill_of_lading 
ORDER BY id DESC 
LIMIT 10;

-- Clear all data from bill_of_lading table
DELETE FROM bill_of_lading;

-- Reset the auto-increment sequence
ALTER SEQUENCE bill_of_lading_id_seq RESTART WITH 1;

-- Verify the table is empty
SELECT COUNT(*) as remaining_records FROM bill_of_lading;

-- Show table structure to confirm it's intact
\d bill_of_lading 