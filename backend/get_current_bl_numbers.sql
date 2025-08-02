-- Get Current BL Numbers for Email Templates
-- This will show all BL numbers currently in the database

SELECT 
    'CURRENT BL NUMBERS' as section,
    id,
    bl_number,
    customer_name,
    payment_method,
    status,
    reserve_status,
    ctn_fee,
    service_fee,
    (ctn_fee + service_fee) as total_amount
FROM bill_of_lading
ORDER BY id;

-- Summary of BL numbers by status
SELECT 
    'BL NUMBERS BY STATUS' as section,
    status,
    COUNT(*) as count,
    STRING_AGG(bl_number, ', ') as bl_numbers
FROM bill_of_lading
GROUP BY status
ORDER BY status;

-- Summary of BL numbers by payment method
SELECT 
    'BL NUMBERS BY PAYMENT METHOD' as section,
    payment_method,
    COUNT(*) as count,
    STRING_AGG(bl_number, ', ') as bl_numbers
FROM bill_of_lading
GROUP BY payment_method
ORDER BY payment_method; 