-- Show All 20 Test Data Entries
-- Complete overview of all records in the database

SELECT 
    'ALL 20 TEST ENTRIES' as section,
    id,
    bl_number,
    customer_name,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    created_at,
    allinpay_85_received_at,
    completed_at,
    CASE 
        WHEN payment_method = 'Bank Transfer' AND status = 'Paid and CTN Valid' THEN 'Bank Transfer - 100% Paid'
        WHEN payment_method = 'Bank Transfer' AND status = 'Awaiting Bank In' THEN 'Bank Transfer - Awaiting Payment'
        WHEN payment_method = 'Bank Transfer' AND status = 'Invoice Sent' THEN 'Bank Transfer - Invoice Sent'
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled' THEN 'Allinpay - 100% Paid'
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled' THEN 'Allinpay - 85% Paid, 15% Pending'
        WHEN payment_method = 'Allinpay' AND status = 'Invoice Sent' THEN 'Allinpay - Invoice Sent'
        ELSE 'Other'
    END as payment_status
FROM bill_of_lading
ORDER BY id;

-- Summary by payment method and status
SELECT 
    'SUMMARY BY PAYMENT METHOD' as section,
    payment_method,
    status,
    reserve_status,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN 'Bank Transfer Records'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'Allinpay - Fully Settled'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'Allinpay - 85% Paid'
        WHEN payment_method = 'Allinpay' AND status = 'Invoice Sent' THEN 'Allinpay - Invoice Sent'
        ELSE 'Other'
    END as description
FROM bill_of_lading
GROUP BY payment_method, status, reserve_status
ORDER BY payment_method, status, reserve_status;

-- Total summary
SELECT 
    'TOTAL SUMMARY' as section,
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
    ) as total_payment_received,
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled'
                THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as total_payment_outstanding
FROM bill_of_lading; 