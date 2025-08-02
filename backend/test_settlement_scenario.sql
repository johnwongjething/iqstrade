-- Test Settlement Scenario
-- This will simulate what happens when payments get settled

-- First, let's see current state
SELECT 
    'CURRENT STATE' as scenario,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show current payment calculations
SELECT 
    'CURRENT CALCULATIONS' as scenario,
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

-- Now let's simulate settling one payment
UPDATE bill_of_lading 
SET reserve_status = 'Reserve Settled', status = 'Paid and CTN Valid'
WHERE id = 1;

-- Show what happens after settlement
SELECT 
    'AFTER SETTLEMENT' as scenario,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show updated payment calculations
SELECT 
    'UPDATED CALCULATIONS' as scenario,
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

-- Show detailed breakdown by record
SELECT 
    id,
    customer_name,
    bl_number,
    status,
    payment_method,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    CASE 
        WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid'
            THEN ctn_fee + service_fee
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'
            THEN ctn_fee + service_fee
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'
            THEN (ctn_fee * 0.85) + (service_fee * 0.85)
        ELSE 0
    END as calculated_paid,
    CASE 
        WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
            THEN ctn_fee + service_fee
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled'
            THEN (ctn_fee * 0.15) + (service_fee * 0.15)
        ELSE 0
    END as calculated_outstanding
FROM bill_of_lading
ORDER BY id; 