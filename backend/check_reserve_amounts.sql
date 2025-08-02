-- Check Reserve Amounts for Outstanding Calculation
-- The issue: stats_summary uses reserve_amount column for unsettled reserves

-- Check current reserve_amount values
SELECT 
    'RESERVE AMOUNT CHECK' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount,
    reserve_amount,
    (ctn_fee + service_fee) * 0.15 as expected_reserve_amount,
    CASE
        WHEN reserve_amount = (ctn_fee + service_fee) * 0.15 THEN 'CORRECT'
        ELSE 'INCORRECT'
    END as status
FROM bill_of_lading
WHERE payment_method = 'Allinpay'
  AND reserve_status = 'Unsettled'
ORDER BY id;

-- Check what the stats_summary calculation is actually getting
SELECT 
    'STATS SUMMARY CALCULATION' as section,
    SUM(reserve_amount) as actual_reserve_amount_total,
    SUM((ctn_fee + service_fee) * 0.15) as expected_reserve_amount_total,
    SUM(reserve_amount) - SUM((ctn_fee + service_fee) * 0.15) as difference
FROM bill_of_lading
WHERE LOWER(TRIM(reserve_status)) = 'unsettled';

-- Check the full outstanding calculation breakdown
SELECT 
    'FULL OUTSTANDING CALCULATION' as section,
    -- Pending records
    (SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
     FROM bill_of_lading
     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')) as awaiting_payment,
    -- Unsettled reserves (using reserve_amount)
    (SELECT COALESCE(SUM(reserve_amount), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as unsettled_reserve,
    -- Unsettled reserves (calculated)
    (SELECT COALESCE(SUM((ctn_fee + service_fee) * 0.15), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as calculated_unsettled_reserve,
    -- Total
    (SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
     FROM bill_of_lading
     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')) +
    (SELECT COALESCE(SUM(reserve_amount), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as total_using_reserve_amount,
    -- Expected total
    (SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
     FROM bill_of_lading
     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')) +
    (SELECT COALESCE(SUM((ctn_fee + service_fee) * 0.15), 0) 
     FROM bill_of_lading 
     WHERE LOWER(TRIM(reserve_status)) = 'unsettled') as expected_total; 