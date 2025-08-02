-- Correct Allinpay Test Data Based on Real Business Logic
-- From payment_webhook.py and AccountingReview.js analysis:

-- REAL ALLINPAY LOGIC:
-- 1. Initial 85% payment: status = 'Paid and CTN Valid', reserve_status = 'Unsettled', allinpay_85_received_at = date
-- 2. Final 15% payment: status = 'Paid and CTN Valid', reserve_status = 'Reserve Settled', completed_at = date
-- 3. Settle Reserve button shows when: payment_method = 'Allinpay' AND reserve_status = 'Unsettled'

-- Check current Allinpay records
SELECT 
    'CURRENT ALLINPAY RECORDS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    allinpay_85_received_at,
    completed_at,
    CASE 
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'SHOULD SHOW SETTLE RESERVE BUTTON'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'FULLY SETTLED'
        ELSE 'OTHER'
    END as accounting_review_status
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Fix Allinpay records to follow real business logic
-- Records 6-8: Should be "Reserve Settled" (100% paid)
-- Records 9-10: Should be "Unsettled" (85% paid, 15% pending) - these should show Settle Reserve button
-- Records 11-15: Should be "Unsettled" (85% paid, 15% pending) - these should show Settle Reserve button

-- Update records 9-10 to be Unsettled (they were incorrectly set as Reserve Settled)
UPDATE bill_of_lading 
SET reserve_status = 'Unsettled',
    allinpay_85_received_at = '2025-07-22 10:00:00',
    completed_at = NULL
WHERE payment_method = 'Allinpay' 
  AND id IN (9, 10);

-- Verify the corrected Allinpay records
SELECT 
    'CORRECTED ALLINPAY RECORDS' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    allinpay_85_received_at,
    completed_at,
    CASE 
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN 'SHOULD SHOW SETTLE RESERVE BUTTON'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN 'FULLY SETTLED'
        ELSE 'OTHER'
    END as accounting_review_status
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
ORDER BY id;

-- Summary of Allinpay records by reserve_status
SELECT 
    'ALLINPAY SUMMARY' as section,
    reserve_status,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount,
    CASE 
        WHEN reserve_status = 'Unsettled' THEN 'These will show Settle Reserve button in AccountingReview'
        WHEN reserve_status = 'Reserve Settled' THEN 'These are fully settled'
        ELSE 'Other'
    END as description
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
GROUP BY reserve_status
ORDER BY reserve_status;

-- Check which records should show Settle Reserve button in AccountingReview
SELECT 
    'SETTLE RESERVE BUTTON CHECK' as section,
    COUNT(*) as total_allinpay_records,
    COUNT(CASE WHEN reserve_status = 'Unsettled' THEN 1 END) as should_show_settle_button,
    COUNT(CASE WHEN reserve_status = 'Reserve Settled' THEN 1 END) as fully_settled
FROM bill_of_lading
WHERE payment_method = 'Allinpay'; 