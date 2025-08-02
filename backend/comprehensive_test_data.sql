 -- Comprehensive Test Data with 20 Records
-- Covers all payment scenarios to test calculation logic thoroughly

-- Clear existing data first
DELETE FROM bill_of_lading;
ALTER SEQUENCE bill_of_lading_id_seq RESTART WITH 1;

-- Test Data Set 1: Bank Transfer - Full Paid (5 records)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method,
    created_at, updated_at
) VALUES 
('ABC Logistics', 'abc@example.com', 'BL-2024-001', 150.00, 75.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('XYZ Shipping', 'xyz@example.com', 'BL-2024-002', 200.00, 100.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('Global Freight', 'global@example.com', 'BL-2024-003', 300.00, 150.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('Ocean Express', 'ocean@example.com', 'BL-2024-004', 250.00, 125.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW()),
('Maritime Co', 'maritime@example.com', 'BL-2024-005', 180.00, 90.00, 'Paid and CTN Valid', 'Bank Transfer', NOW(), NOW());

-- Test Data Set 2: Allinpay - Reserve Settled (5 records)
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method, reserve_status,
    created_at, updated_at
) VALUES 
('Fast Track Ltd', 'fast@example.com', 'BL-2024-006', 400.00, 200.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW()),
('Quick Ship', 'quick@example.com', 'BL-2024-007', 350.00, 175.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW()),
('Express Cargo', 'express@example.com', 'BL-2024-008', 500.00, 250.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW()),
('Speed Freight', 'speed@example.com', 'BL-2024-009', 280.00, 140.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW()),
('Rapid Logistics', 'rapid@example.com', 'BL-2024-010', 320.00, 160.00, 'Paid and CTN Valid', 'Allinpay', 'Reserve Settled', NOW(), NOW());

-- Test Data Set 3: Allinpay - Unsettled (5 records) - 85% paid, 15% outstanding
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method, reserve_status,
    created_at, updated_at
) VALUES 
('Premium Cargo', 'premium@example.com', 'BL-2024-011', 600.00, 300.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('Elite Shipping', 'elite@example.com', 'BL-2024-012', 450.00, 225.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('VIP Logistics', 'vip@example.com', 'BL-2024-013', 700.00, 350.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('Royal Freight', 'royal@example.com', 'BL-2024-014', 380.00, 190.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW()),
('Luxury Cargo', 'luxury@example.com', 'BL-2024-015', 550.00, 275.00, 'Paid and CTN Valid', 'Allinpay', 'Unsettled', NOW(), NOW());

-- Test Data Set 4: Awaiting Bank In (3 records) - Full amount outstanding
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method,
    created_at, updated_at
) VALUES 
('Pending Co', 'pending@example.com', 'BL-2024-016', 800.00, 400.00, 'Awaiting Bank In', 'Bank Transfer', NOW(), NOW()),
('Waiting Ltd', 'waiting@example.com', 'BL-2024-017', 650.00, 325.00, 'Awaiting Bank In', 'Bank Transfer', NOW(), NOW()),
('Processing Inc', 'processing@example.com', 'BL-2024-018', 750.00, 375.00, 'Awaiting Bank In', 'Allinpay', NOW(), NOW());

-- Test Data Set 5: Invoice Sent (2 records) - Full amount outstanding
INSERT INTO bill_of_lading (
    customer_name, customer_email, bl_number, 
    ctn_fee, service_fee, status, payment_method,
    created_at, updated_at
) VALUES 
('Invoice Co', 'invoice@example.com', 'BL-2024-019', 900.00, 450.00, 'Invoice Sent', 'Bank Transfer', NOW(), NOW()),
('Billing Ltd', 'billing@example.com', 'BL-2024-020', 720.00, 360.00, 'Invoice Sent', 'Allinpay', NOW(), NOW());

-- Verify the comprehensive test data
SELECT 
    'COMPREHENSIVE TEST DATA SUMMARY' as info,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as completed_records,
    COUNT(CASE WHEN status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In') THEN 1 END) as pending_records,
    COALESCE(SUM(ctn_fee + service_fee), 0) as total_invoice_amount
FROM bill_of_lading;

-- Show detailed breakdown by payment method and status
SELECT 
    payment_method,
    reserve_status,
    status,
    COUNT(*) as record_count,
    SUM(ctn_fee + service_fee) as total_amount
FROM bill_of_lading
GROUP BY payment_method, reserve_status, status
ORDER BY payment_method, reserve_status, status;

-- Show expected calculations for verification
SELECT 
    'EXPECTED CALCULATIONS' as section,
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
    ) as expected_payment_received,
    SUM(
        CASE 
            WHEN status IN ('Awaiting Bank In', 'Invoice Sent')
                THEN ctn_fee + service_fee
            WHEN payment_method = 'Allinpay' AND reserve_status = 'Unsettled'
                THEN (ctn_fee * 0.15) + (service_fee * 0.15)
            ELSE 0
        END
    ) as expected_payment_outstanding
FROM bill_of_lading;