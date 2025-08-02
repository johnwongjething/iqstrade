-- Check Payment Status for Allinpay Records
-- AccountingReview.js filters for payment_status = 'Paid 85%'

-- Check all Allinpay records and their payment_status
SELECT 
    'ALLINPAY PAYMENT STATUS CHECK' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    payment_status,
    allinpay_85_received_at,
    completed_at,
    CASE 
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'SHOULD BE: Paid 85%'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'SHOULD BE: Paid 100%'
        ELSE 'OTHER'
    END as expected_payment_status
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Check which records would pass AccountingReview.js filter
SELECT 
    'ACCOUNTINGREVIEW FILTER CHECK' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    payment_status,
    CASE 
        WHEN bill.status = 'Awaiting Bank In' THEN 'PASSES FILTER (Awaiting Bank In)'
        WHEN bill.payment_method AND LOWER(bill.payment_method) = 'allinpay' AND bill.payment_status = 'Paid 85%' THEN 'PASSES FILTER (Allinpay + Paid 85%)'
        ELSE 'FAILS FILTER'
    END as filter_result
FROM bill_of_lading bill
WHERE bill.status = 'Awaiting Bank In' 
   OR (bill.payment_method AND LOWER(bill.payment_method) = 'allinpay' AND bill.payment_status = 'Paid 85%')
ORDER BY id;

-- Fix payment_status for Allinpay records
UPDATE bill_of_lading 
SET payment_status = 'Paid 85%'
WHERE payment_method = 'Allinpay' 
  AND reserve_status = 'Unsettled'
  AND status = 'Paid and CTN Valid';

UPDATE bill_of_lading 
SET payment_status = 'Paid 100%'
WHERE payment_method = 'Allinpay' 
  AND reserve_status = 'Reserve Settled'
  AND status = 'Paid and CTN Valid';

-- Verify the fixes
SELECT 
    'AFTER FIXING PAYMENT STATUS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    payment_status,
    CASE 
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'SHOULD SHOW IN ACCOUNTINGREVIEW'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'FULLY SETTLED'
        ELSE 'OTHER'
    END as accounting_review_status
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id; 