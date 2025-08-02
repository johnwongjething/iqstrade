-- Add Clean Test Data to bill_of_lading table
-- This will create test records with known values to verify calculations

-- Test Data Set 1: Bank Transfer Payments (Full amounts)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method,
    created_at, updated_at
) VALUES 
('Test Customer 1', 'test1@example.com', 'BL-001', 100.00, 50.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('Test Customer 2', 'test2@example.com', 'BL-002', 200.00, 100.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('Test Customer 3', 'test3@example.com', 'BL-003', 150.00, 75.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW());

-- Test Data Set 2: Allinpay Settled (Full amounts)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method, reserve_status,
    created_at, updated_at
) VALUES 
('Test Customer 4', 'test4@example.com', 'BL-004', 300.00, 150.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW()),
('Test Customer 5', 'test5@example.com', 'BL-005', 250.00, 125.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW());

-- Test Data Set 3: Allinpay Unsettled (85% of amounts)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method, reserve_status,
    created_at, updated_at
) VALUES 
('Test Customer 6', 'test6@example.com', 'BL-006', 400.00, 200.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('Test Customer 7', 'test7@example.com', 'BL-007', 350.00, 175.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW());

-- Test Data Set 4: Pending Payments (Full amounts outstanding)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method,
    created_at, updated_at
) VALUES 
('Test Customer 8', 'test8@example.com', 'BL-008', 500.00, 250.00, 'Awaiting Bank In', 'Bank Transfer', NOW(), NOW()),
('Test Customer 9', 'test9@example.com', 'BL-009', 450.00, 225.00, 'Invoice Sent', 'Bank Transfer', NOW(), NOW()),
('Test Customer 10', 'test10@example.com', 'BL-010', 600.00, 300.00, 'Pending', 'Bank Transfer', NOW(), NOW());

-- Test Data Set 5: Allinpay Unsettled Outstanding (15% of amounts)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method, reserve_status,
    created_at, updated_at
) VALUES 
('Test Customer 11', 'test11@example.com', 'BL-011', 700.00, 350.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('Test Customer 12', 'test12@example.com', 'BL-012', 650.00, 325.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW());

-- Verify the test data
SELECT 
    'SUMMARY' as info,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show all test records with calculations
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
        WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid' THEN (ctn_fee + service_fee)
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled' THEN (ctn_fee + service_fee)
        WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled' THEN (ctn_fee * 0.85 + service_fee * 0.85)
        ELSE 0
    END as calculated_paid_amount,
    CASE 
        WHEN status IN ('Awaiting Bank In', 'Invoice Sent') THEN (ctn_fee + service_fee)
        WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled' THEN (ctn_fee * 0.15 + service_fee * 0.15)
        ELSE 0
    END as calculated_outstanding_amount
FROM bill_of_lading 
ORDER BY id; 