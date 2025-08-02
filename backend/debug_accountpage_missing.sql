-- Debug AccountPage Missing Entries
-- Compare expected vs actual data

-- First, let's see all our test records
SELECT 
    'ALL TEST RECORDS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
ORDER BY id;

-- Now let's simulate what AccountPage should show based on its logic
-- AccountPage shows records where status = 'Paid and CTN Valid'
-- For Allinpay, it shows both 85% and 15% entries separately

SELECT 
    'ACCOUNTPAGE EXPECTED ENTRIES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN 'Bank Transfer Entry'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'Allinpay 100% Entry'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'Allinpay 85% Entry'
        ELSE 'Other'
    END as entry_type,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN ctn_fee + service_fee
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN ctn_fee + service_fee
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN (ctn_fee * 0.85) + (service_fee * 0.85)
        ELSE 0
    END as expected_amount,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN completed_at
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN completed_at
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN allinpay_85_received_at
        ELSE NULL
    END as expected_date
FROM bill_of_lading
WHERE status = 'Paid and CTN Valid'
ORDER BY 
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN completed_at
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN completed_at
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN allinpay_85_received_at
        ELSE NULL
    END DESC;

-- Count expected entries by type
SELECT 
    'EXPECTED ENTRY COUNTS' as section,
    payment_method,
    reserve_status,
    COUNT(*) as record_count,
    SUM(
        CASE 
            WHEN payment_method = 'Bank Transfer' THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN (ctn_fee * 0.85) + (service_fee * 0.85)
            ELSE 0
        END
    ) as total_amount
FROM bill_of_lading
WHERE status = 'Paid and CTN Valid'
GROUP BY payment_method, reserve_status
ORDER BY payment_method, reserve_status;

-- Check if there are any records that should show but aren't
SELECT 
    'MISSING RECORDS CHECK' as section,
    COUNT(*) as total_paid_records,
    COUNT(CASE WHEN payment_method = 'Bank Transfer' THEN 1 END) as bank_transfer_records,
    COUNT(CASE WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 1 END) as allinpay_settled_records,
    COUNT(CASE WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 1 END) as allinpay_unsettled_records,
    -- AccountPage should show: Bank Transfer (5) + Allinpay Settled (3) + Allinpay Unsettled (4) = 12 entries
    -- But you're seeing 13, so there might be a duplicate or extra entry
    5 + 3 + 4 as expected_entries,
    13 as actual_entries_showing
FROM bill_of_lading
WHERE status = 'Paid and CTN Valid'; 