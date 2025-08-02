-- Fix Missing allinpay_85_received_at Dates
-- Check which records are missing dates and fix them

-- Check current state of allinpay_85_received_at dates
SELECT 
    'CURRENT 85% DATES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Check which unsettled records are missing 85% dates
SELECT 
    'MISSING 85% DATES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND allinpay_85_received_at IS NULL;

-- Fix the missing dates for unsettled records
UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-19 14:00:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 13;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-21 09:30:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 14;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-24 16:15:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 15;

-- Verify the fixes
SELECT 
    'AFTER FIXING DATES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Check if all unsettled records now have dates
SELECT 
    'VERIFICATION' as section,
    COUNT(*) as total_unsettled_records,
    COUNT(CASE WHEN allinpay_85_received_at IS NOT NULL THEN 1 END) as records_with_85_date,
    COUNT(CASE WHEN allinpay_85_received_at IS NULL THEN 1 END) as records_missing_85_date
FROM bill_of_lading
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'; 