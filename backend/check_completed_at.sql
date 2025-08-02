-- Check completed_at dates and their impact on calculations

-- Check which records have completed_at set
SELECT 
    'COMPLETED_AT CHECK' as section,
    id,
    bl_number,
    status,
    payment_method,
    reserve_status,
    completed_at,
    CASE 
        WHEN completed_at IS NOT NULL THEN 'Has completed_at'
        ELSE 'No completed_at'
    END as completed_at_status
FROM bill_of_lading
ORDER BY id;

-- Check if completed_at affects any calculations
SELECT 
    'CALCULATION IMPACT' as section,
    COUNT(*) as total_records,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as records_with_completed_at,
    COUNT(CASE WHEN completed_at IS NULL THEN 1 END) as records_without_completed_at,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' AND completed_at IS NULL THEN 1 END) as paid_without_completed_at
FROM bill_of_lading;

-- Check if there are any business logic rules that depend on completed_at
-- For example, some systems only count payments as "received" if they have a completed_at date
SELECT 
    'BUSINESS LOGIC CHECK' as section,
    status,
    payment_method,
    reserve_status,
    COUNT(*) as record_count,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as with_completed_at,
    COUNT(CASE WHEN completed_at IS NULL THEN 1 END) as without_completed_at
FROM bill_of_lading
GROUP BY status, payment_method, reserve_status
ORDER BY status, payment_method, reserve_status; 