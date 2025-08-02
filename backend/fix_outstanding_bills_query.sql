-- Fix Outstanding Bills Query Issue
-- The problem: outstanding_bills includes completed records with unsettled reserves

-- Check what the current outstanding_bills query returns
SELECT 
    'CURRENT OUTSTANDING BILLS QUERY RESULTS' as section,
    id,
    bl_number,
    customer_name,
    status,
    payment_method,
    reserve_status,
    ctn_fee,
    service_fee,
    CASE 
        WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN 'CORRECT - Pending'
        WHEN payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled' THEN 'INCORRECT - Completed but showing as outstanding'
        ELSE 'OTHER'
    END as issue
FROM bill_of_lading
WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
   OR (payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled')
ORDER BY id;

-- Show the correct outstanding calculation
SELECT 
    'CORRECT OUTSTANDING CALCULATION' as section,
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled' THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as total_outstanding,
    SUM(CASE WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN ctn_fee + service_fee ELSE 0 END) as pending_outstanding,
    SUM(CASE WHEN payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled' THEN (ctn_fee * 0.15) + (service_fee * 0.15) ELSE 0 END) as unsettled_reserve_outstanding
FROM bill_of_lading
WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
   OR (payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled');

-- The issue: Records 9-15 should NOT appear in outstanding bills because they're completed
-- They should only contribute to the outstanding calculation via their 15% reserve amount

-- Verify the expected outstanding amount
SELECT 
    'EXPECTED OUTSTANDING BREAKDOWN' as section,
    'Pending Records (16-20)' as category,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE status IN ('Awaiting Bank In', 'Invoice Sent')

UNION ALL

SELECT 
    'EXPECTED OUTSTANDING BREAKDOWN' as section,
    'Unsettled Reserve (9-15)' as category,
    COUNT(*) as record_count,
    SUM((ctn_fee * 0.15) + (service_fee * 0.15)) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay' 
  AND LOWER(TRIM(reserve_status)) = 'unsettled'
  AND status = 'Paid and CTN Valid'; 