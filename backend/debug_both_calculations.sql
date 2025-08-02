-- Debug Both Calculation Methods
-- Compare Staff Stats vs Management Dashboard calculations

-- First, let's verify our expected calculations again
SELECT 
    'EXPECTED SQL CALCULATIONS' as method,
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

-- Now let's test the Management Dashboard logic (Python loop style)
-- This simulates what the management_routes.py does
SELECT 
    'MANAGEMENT DASHBOARD LOGIC' as method,
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

-- Let's also check what the actual data looks like
SELECT 
    'DATA VERIFICATION' as section,
    payment_method,
    reserve_status,
    status,
    COUNT(*) as count,
    SUM(ctn_fee + service_fee) as total_amount,
    STRING_AGG(bl_number, ', ') as bl_numbers
FROM bill_of_lading
GROUP BY payment_method, reserve_status, status
ORDER BY payment_method, reserve_status, status;

-- Check for any case sensitivity or whitespace issues
SELECT 
    'CASE/WHITESPACE CHECK' as section,
    id,
    bl_number,
    payment_method,
    LENGTH(payment_method) as payment_method_length,
    LOWER(TRIM(payment_method)) as normalized_payment_method,
    reserve_status,
    LENGTH(reserve_status) as reserve_status_length,
    LOWER(TRIM(reserve_status)) as normalized_reserve_status,
    status,
    LENGTH(status) as status_length
FROM bill_of_lading
ORDER BY id; 