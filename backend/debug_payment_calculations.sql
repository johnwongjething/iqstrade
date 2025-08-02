-- Debug Payment Calculations
-- This script will help us understand why the calculations are wrong

-- First, let's see all the data we have
SELECT 
    'ALL DATA' as section,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show all records with their payment method and status
SELECT 
    id,
    customer_name,
    bl_number,
    status,
    payment_method,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount
FROM bill_of_lading
ORDER BY id;

-- Test the exact logic from stats_summary endpoint
SELECT 
    'PAYMENT RECEIVED CALCULATION' as section,
    COUNT(*) as total_records,
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
    ) as calculated_payment_received
FROM bill_of_lading;

-- Test the exact logic from management_routes endpoint
SELECT 
    'MANAGEMENT DASHBOARD CALCULATION' as section,
    COUNT(*) as total_records,
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
    ) as calculated_payment_received
FROM bill_of_lading;

-- Check for case sensitivity issues
SELECT 
    'CASE SENSITIVITY CHECK' as section,
    payment_method,
    reserve_status,
    status,
    COUNT(*) as count
FROM bill_of_lading
GROUP BY payment_method, reserve_status, status
ORDER BY payment_method, reserve_status, status;

-- Check for whitespace issues
SELECT 
    'WHITESPACE CHECK' as section,
    id,
    customer_name,
    payment_method,
    LENGTH(payment_method) as payment_method_length,
    reserve_status,
    LENGTH(reserve_status) as reserve_status_length,
    status,
    LENGTH(status) as status_length
FROM bill_of_lading
ORDER BY id; 