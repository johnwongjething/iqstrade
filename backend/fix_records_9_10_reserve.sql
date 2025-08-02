-- Fix Reserve Amount for Records 9 and 10
-- These records have reserve_amount = 0 but should be $30

-- Check current state
SELECT 
    'BEFORE FIX' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    reserve_amount,
    (ctn_fee + service_fee) * 0.15 as expected_reserve_amount
FROM bill_of_lading
WHERE id IN (9, 10)
ORDER BY id;

-- Fix the reserve_amount for records 9 and 10
UPDATE bill_of_lading
SET reserve_amount = (ctn_fee + service_fee) * 0.15
WHERE id IN (9, 10)
  AND payment_method = 'Allinpay'
  AND reserve_status = 'Unsettled';

-- Verify the fix
SELECT 
    'AFTER FIX' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    reserve_amount,
    (ctn_fee + service_fee) * 0.15 as expected_reserve_amount,
    CASE
        WHEN reserve_amount = (ctn_fee + service_fee) * 0.15 THEN 'CORRECT'
        ELSE 'INCORRECT'
    END as status
FROM bill_of_lading
WHERE id IN (9, 10)
ORDER BY id;

-- Check the total outstanding calculation after fix
SELECT 
    'TOTAL OUTSTANDING AFTER FIX' as section,
    -- Pending records
    (SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
     FROM bill_of_lading
     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')) as awaiting_payment,
    -- Unsettled reserves (using reserve_amount)
    (SELECT COALESCE(SUM(reserve_amount), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as unsettled_reserve,
    -- Total
    (SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
     FROM bill_of_lading
     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')) +
    (SELECT COALESCE(SUM(reserve_amount), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as total_outstanding;

-- Expected values after fix:
-- awaiting_payment: 5 × $200 = $1,000
-- unsettled_reserve: 7 × $30 = $210
-- total_outstanding: $1,000 + $210 = $1,210 