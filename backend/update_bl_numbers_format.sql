-- Update BL numbers from BL-2024-XXX format to BL2024XXX format
-- This will make them work with the current regex pattern

UPDATE bill_of_lading 
SET bl_number = REPLACE(bl_number, '-', '')
WHERE bl_number LIKE 'BL-2024-%';

-- Verify the changes
SELECT 
    id,
    bl_number,
    customer_name,
    payment_method,
    status
FROM bill_of_lading 
ORDER BY id; 