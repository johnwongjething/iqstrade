-- Verify Settle Reserve Button Conditions
-- Check if our 7 unsettled entries fulfill the exact requirements:
-- payment_method exists AND
-- payment_method = 'allinpay' (case-insensitive) AND
-- reserve_status exists AND
-- reserve_status = 'unsettled' (case-insensitive)

-- Check all Allinpay records with their conditions
SELECT 
    'ALLINPAY RECORDS WITH CONDITIONS' as section,
    id,
    bl_number,
    payment_method,
    reserve_status,
    -- Check each condition
    CASE WHEN payment_method IS NOT NULL THEN 'YES' ELSE 'NO' END as payment_method_exists,
    CASE WHEN LOWER(payment_method) = 'allinpay' THEN 'YES' ELSE 'NO' END as payment_method_allinpay,
    CASE WHEN reserve_status IS NOT NULL THEN 'YES' ELSE 'NO' END as reserve_status_exists,
    CASE WHEN LOWER(reserve_status) = 'unsettled' THEN 'YES' ELSE 'NO' END as reserve_status_unsettled,
    -- Combined condition
    CASE 
        WHEN payment_method IS NOT NULL 
         AND LOWER(payment_method) = 'allinpay' 
         AND reserve_status IS NOT NULL 
         AND LOWER(reserve_status) = 'unsettled' 
        THEN 'SHOULD SHOW SETTLE RESERVE BUTTON'
        ELSE 'NO BUTTON'
    END as settle_reserve_button
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Summary of which records should show the button
SELECT 
    'SETTLE RESERVE BUTTON SUMMARY' as section,
    COUNT(*) as total_allinpay_records,
    COUNT(CASE 
        WHEN payment_method IS NOT NULL 
         AND LOWER(payment_method) = 'allinpay' 
         AND reserve_status IS NOT NULL 
         AND LOWER(reserve_status) = 'unsettled' 
        THEN 1 
    END) as should_show_settle_button,
    COUNT(CASE 
        WHEN payment_method IS NOT NULL 
         AND LOWER(payment_method) = 'allinpay' 
         AND reserve_status IS NOT NULL 
         AND LOWER(reserve_status) = 'reserve settled' 
        THEN 1 
    END) as fully_settled_no_button
FROM bill_of_lading
WHERE payment_method = 'Allinpay';

-- List the specific records that should show the button
SELECT 
    'RECORDS THAT SHOULD SHOW SETTLE RESERVE BUTTON' as section,
    id,
    bl_number,
    customer_name,
    payment_method,
    reserve_status,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
WHERE payment_method IS NOT NULL 
  AND LOWER(payment_method) = 'allinpay' 
  AND reserve_status IS NOT NULL 
  AND LOWER(reserve_status) = 'unsettled'
ORDER BY id; 