-- Set All Fees to 100 for Easy Debugging
-- This makes calculations much easier to track and verify

-- First, let's see current fees
SELECT 
    'CURRENT FEES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount
FROM bill_of_lading
ORDER BY id;

-- Set all CTN fees and service fees to 100
UPDATE bill_of_lading 
SET ctn_fee = 100.00,
    service_fee = 100.00
WHERE id BETWEEN 1 AND 20;

-- Update reserve_amount for unsettled Allinpay records (15% of total)
UPDATE bill_of_lading 
SET reserve_amount = (ctn_fee + service_fee) * 0.15
WHERE payment_method = 'Allinpay'
  AND reserve_status = 'Unsettled'
  AND status = 'Paid and CTN Valid';

-- Show the updated fees
SELECT 
    'UPDATED FEES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    reserve_amount,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN 'Total: 200'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'Total: 200'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN '85%: 170, 15%: 30'
        ELSE 'Other'
    END as expected_calculation
FROM bill_of_lading
ORDER BY id;

-- Calculate expected totals with 100 fees
SELECT 
    'EXPECTED CALCULATIONS WITH 100 FEES' as section,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN 1 END) as pending_records,
    SUM(ctn_fee + service_fee) as total_invoice_amount,
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
    ) as expected_payment_received,
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled'
                THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as expected_payment_outstanding
FROM bill_of_lading; 