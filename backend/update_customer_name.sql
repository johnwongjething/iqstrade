-- Update customer_name for ray40 if it's empty
UPDATE users 
SET customer_name = 'ray40' 
WHERE username = 'ray40' 
AND (customer_name IS NULL OR customer_name = '');

-- Verify the update
SELECT username, customer_name, customer_email, customer_phone 
FROM users 
WHERE username = 'ray40'; 