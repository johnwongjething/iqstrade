-- Debug Calculation with 100 Fees
-- Let's see exactly what's happening with each record

-- Show all records with their current status
SELECT 
    'ALL RECORDS DETAIL' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    CASE 
        WHEN payment_method = 'Bank Transfer' AND status = 'Paid and CTN Valid' THEN 'Bank Transfer - Paid: 200'
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled' THEN 'Allinpay Settled: 200'
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled' THEN 'Allinpay Unsettled: 170 (85%)'
        WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN 'Pending: 200'
        ELSE 'Other'
    END as calculation_type
FROM bill_of_lading
ORDER BY id;

-- Count by payment method and status
SELECT 
    'RECORD COUNTS' as section,
    payment_method,
    status,
    reserve_status,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
GROUP BY payment_method, status, reserve_status
ORDER BY payment_method, status, reserve_status;

-- Manual calculation breakdown
SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Bank Transfer Paid' as category,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Bank Transfer' AND status = 'Paid and CTN Valid'

UNION ALL

SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Allinpay Reserve Settled' as category,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'

UNION ALL

SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Allinpay Unsettled (85%)' as category,
    COUNT(*) as record_count,
    SUM((ctn_fee * 0.85) + (service_fee * 0.85)) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'

UNION ALL

SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Awaiting Bank In' as category,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE status = 'Awaiting Bank In'

UNION ALL

SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Invoice Sent' as category,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
WHERE status = 'Invoice Sent'

UNION ALL

SELECT 
    'MANUAL CALCULATION BREAKDOWN' as section,
    'Allinpay Unsettled (15% outstanding)' as category,
    COUNT(*) as record_count,
    SUM((ctn_fee * 0.15) + (service_fee * 0.15)) as total_amount
FROM bill_of_lading
WHERE payment_method = 'Allinpay' AND reserve_status = 'Unsettled';

-- Verify the SQL calculation logic
SELECT 
    'VERIFY SQL CALCULATION' as section,
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
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled'
                THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as payment_outstanding
FROM bill_of_lading; 