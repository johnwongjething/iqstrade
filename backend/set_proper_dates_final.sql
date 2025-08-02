-- Set Proper Dates for Payment Records (FINAL - Using Correct Field Names)
-- created_at = When customer uploads file
-- allinpay_85_received_at = When 85% payment received (Allinpay only)
-- completed_at = When final payment received (100% for Bank Transfer, 15% for Allinpay)

-- First, let's see what we have before setting dates
SELECT 
    'BEFORE SETTING DATES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    created_at,
    allinpay_85_received_at,
    completed_at
FROM bill_of_lading
ORDER BY id;

-- Set completed_at for Bank Transfer records (100% received)
UPDATE bill_of_lading 
SET completed_at = '2025-07-15 14:30:00'
WHERE payment_method = 'Bank Transfer' 
  AND status = 'Paid and CTN Valid'
  AND id = 1;

UPDATE bill_of_lading 
SET completed_at = '2025-07-18 09:15:00'
WHERE payment_method = 'Bank Transfer' 
  AND status = 'Paid and CTN Valid'
  AND id = 2;

UPDATE bill_of_lading 
SET completed_at = '2025-07-22 16:45:00'
WHERE payment_method = 'Bank Transfer' 
  AND status = 'Paid and CTN Valid'
  AND id = 3;

UPDATE bill_of_lading 
SET completed_at = '2025-07-25 11:20:00'
WHERE payment_method = 'Bank Transfer' 
  AND status = 'Paid and CTN Valid'
  AND id = 4;

UPDATE bill_of_lading 
SET completed_at = '2025-07-28 13:55:00'
WHERE payment_method = 'Bank Transfer' 
  AND status = 'Paid and CTN Valid'
  AND id = 5;

-- For Allinpay records, set both 85% payment date and completed_at

-- Allinpay "Reserve Settled" records (85% + 15% both received)
UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-13 10:00:00',
    completed_at = '2025-07-16 10:30:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Reserve Settled'
  AND id = 6;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-16 14:30:00',
    completed_at = '2025-07-19 15:45:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Reserve Settled'
  AND id = 7;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-20 08:45:00',
    completed_at = '2025-07-23 08:20:00'
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Reserve Settled'
  AND id = 8;

-- Allinpay "Unsettled" records (85% received, 15% pending)
UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-10 14:00:00',
    completed_at = NULL
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 9;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-12 09:30:00',
    completed_at = NULL
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 10;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-14 16:15:00',
    completed_at = NULL
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 11;

UPDATE bill_of_lading 
SET allinpay_85_received_at = '2025-07-17 11:45:00',
    completed_at = NULL
WHERE payment_method = 'Allinpay' 
  AND status = 'Paid and CTN Valid'
  AND reserve_status = 'Unsettled'
  AND id = 12;

-- Show the results after setting dates
SELECT 
    'AFTER SETTING DATES' as section,
    id,
    bl_number,
    payment_method,
    status,
    reserve_status,
    created_at as file_upload_date,
    allinpay_85_received_at,
    completed_at as final_payment_date,
    CASE 
        WHEN payment_method = 'Bank Transfer' THEN '100% received on completed_at'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Reserve Settled' THEN '85% on allinpay_85_received_at, 15% on completed_at'
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN '85% on allinpay_85_received_at, 15% pending'
        ELSE 'Other'
    END as payment_status
FROM bill_of_lading
ORDER BY id; 