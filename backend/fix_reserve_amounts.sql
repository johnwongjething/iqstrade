-- Fix Reserve Amounts for Unsettled Allinpay Records
-- This will set the reserve_amount field to 15% of the total amount

-- Update reserve_amount for unsettled Allinpay records
UPDATE bill_of_lading 
SET reserve_amount = (ctn_fee + service_fee) * 0.15
WHERE payment_method = 'Allinpay' 
  AND reserve_status = 'Unsettled' 
  AND status = 'Paid and CTN Valid';

-- Verify the updates
SELECT 
    'RESERVE AMOUNT FIX' as section,
    id,
    bl_number,
    payment_method,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    reserve_amount,
    (ctn_fee + service_fee) * 0.15 as expected_reserve_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay' 
  AND reserve_status = 'Unsettled' 
  AND status = 'Paid and CTN Valid'
ORDER BY id;

-- Now test both calculation methods again
SELECT 
    'STAFF STATS CALCULATION' as method,
    SUM(
        CASE 
            WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid'
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'
                THEN (ctn_fee * 0.85) + (service_fee * 0.85)
            ELSE 0
        END
    ) as payment_received,
    (
        SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
        FROM bill_of_lading
        WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
    ) + (
        SELECT COALESCE(SUM(reserve_amount), 0) 
        FROM bill_of_lading 
        WHERE LOWER(TRIM(reserve_status)) = 'unsettled'
    ) as payment_outstanding
FROM bill_of_lading;

SELECT 
    'MANAGEMENT DASHBOARD CALCULATION' as method,
    SUM(
        CASE 
            WHEN LOWER(TRIM(payment_method)) != 'allinpay' AND status = 'Paid and CTN Valid'
                THEN ctn_fee + service_fee
            WHEN LOWER(TRIM(payment_method)) = 'allinpay' AND status = 'Paid and CTN Valid' AND LOWER(TRIM(reserve_status)) = 'reserve settled'
                THEN ctn_fee + service_fee
            WHEN LOWER(TRIM(payment_method)) = 'allinpay' AND status = 'Paid and CTN Valid' AND LOWER(TRIM(reserve_status)) = 'unsettled'
                THEN (ctn_fee * 0.85) + (service_fee * 0.85)
            ELSE 0
        END
    ) as payment_received,
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
                THEN ctn_fee + service_fee
            WHEN LOWER(TRIM(payment_method)) = 'allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled'
                THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as payment_outstanding
FROM bill_of_lading; 