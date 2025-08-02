-- Fix Allinpay Status Rules
-- Allinpay should only have:
-- 1. status = 'Invoice Sent' 
-- 2. status = 'Paid and CTN Valid' & reserve_status = 'Unsettled'
-- 3. status = 'Paid and CTN Valid' & reserve_status = 'Reserve Settled'

-- Check current Allinpay records and their status
SELECT 
    'CURRENT ALLINPAY STATUS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Find Allinpay records with incorrect status
SELECT 
    'INCORRECT ALLINPAY STATUS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    CASE 
        WHEN status = 'Awaiting Bank In' THEN 'SHOULD BE Invoice Sent or Paid and CTN Valid'
        WHEN status = 'Pending' THEN 'SHOULD BE Invoice Sent or Paid and CTN Valid'
        ELSE 'OK'
    END as issue
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
  AND status NOT IN ('Invoice Sent', 'Paid and CTN Valid');

-- Fix Allinpay records with incorrect status
-- Change 'Awaiting Bank In' to 'Invoice Sent' for Allinpay
UPDATE bill_of_lading 
SET status = 'Invoice Sent'
WHERE payment_method = 'Allinpay' 
  AND status = 'Awaiting Bank In';

-- Change 'Pending' to 'Invoice Sent' for Allinpay
UPDATE bill_of_lading 
SET status = 'Invoice Sent'
WHERE payment_method = 'Allinpay' 
  AND status = 'Pending';

-- Verify the fixes
SELECT 
    'AFTER FIXING ALLINPAY STATUS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    CASE 
        WHEN status = 'Invoice Sent' THEN 'CORRECT'
        WHEN status = 'Paid and CTN Valid' AND reserve_status IN ('Unsettled', 'Reserve Settled') THEN 'CORRECT'
        ELSE 'NEEDS REVIEW'
    END as validation
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Summary of Allinpay records by status
SELECT 
    'ALLINPAY STATUS SUMMARY' as section,
    status,
    reserve_status,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
GROUP BY status, reserve_status
ORDER BY status, reserve_status;

-- Check if any Allinpay records still have incorrect status
SELECT 
    'FINAL VALIDATION' as section,
    COUNT(*) as total_allinpay_records,
    COUNT(CASE WHEN status IN ('Invoice Sent', 'Paid and CTN Valid') THEN 1 END) as correct_status_count,
    COUNT(CASE WHEN status NOT IN ('Invoice Sent', 'Paid and CTN Valid') THEN 1 END) as incorrect_status_count,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' AND reserve_status IN ('Unsettled', 'Reserve Settled') THEN 1 END) as correct_reserve_status_count,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' AND reserve_status NOT IN ('Unsettled', 'Reserve Settled') THEN 1 END) as incorrect_reserve_status_count
FROM bill_of_lading
WHERE payment_method = 'Allinpay'; 