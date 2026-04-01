-- =====================================================
-- Lang Xeng Airlines GSA System - Advanced Database Schema
-- Enterprise-Grade Advanced Features
-- =====================================================

-- This file contains advanced features that build upon the core schema
-- Run this after GSA_CORE_SCHEMA.sql

-- =====================================================
-- ADVANCED FEATURE TABLES
-- =====================================================

-- Customer Relationship Management (CRM)
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    date_of_birth DATE,
    nationality VARCHAR(3),
    address TEXT,
    city VARCHAR(50),
    country_code VARCHAR(3),
    customer_type VARCHAR(20) DEFAULT 'individual', -- individual, corporate, group
    loyalty_tier VARCHAR(20) DEFAULT 'bronze', -- bronze, silver, gold, platinum
    total_bookings INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_segments (
    segment_id SERIAL PRIMARY KEY,
    segment_name VARCHAR(50) NOT NULL,
    description TEXT,
    criteria JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loyalty_programs (
    loyalty_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    program_name VARCHAR(50) NOT NULL,
    points_balance INTEGER DEFAULT 0,
    tier_level VARCHAR(20) DEFAULT 'bronze',
    tier_expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_feedback (
    feedback_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    booking_id INTEGER REFERENCES bookings(booking_id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    category VARCHAR(50), -- service, booking, flight, etc.
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue Management and Analytics
CREATE TABLE revenue_analytics (
    analytics_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    route_id INTEGER REFERENCES routes(route_id),
    date DATE NOT NULL,
    total_bookings INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.00,
    load_factor DECIMAL(5,2) DEFAULT 0.00,
    rasm DECIMAL(8,2) DEFAULT 0.00, -- Revenue per Available Seat Mile
    yield_per_km DECIMAL(8,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE yield_management (
    yield_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    fare_class_id INTEGER REFERENCES fare_classes(fare_class_id),
    available_seats INTEGER NOT NULL,
    booked_seats INTEGER DEFAULT 0,
    load_factor DECIMAL(5,2) DEFAULT 0.00,
    current_fare DECIMAL(10,2) NOT NULL,
    base_fare DECIMAL(10,2) NOT NULL,
    yield_multiplier DECIMAL(5,2) DEFAULT 1.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market Intelligence
CREATE TABLE market_intelligence (
    intelligence_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id),
    competitor_airline VARCHAR(50),
    competitor_fare DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    data_date DATE NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advanced Financial Management
CREATE TABLE financial_accounts (
    account_id SERIAL PRIMARY KEY,
    account_code VARCHAR(20) UNIQUE NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- asset, liability, equity, revenue, expense
    currency VARCHAR(3) DEFAULT 'USD',
    parent_account_id INTEGER REFERENCES financial_accounts(account_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tax_management (
    tax_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    tax_type VARCHAR(20) NOT NULL, -- VAT, GST, departure_tax, arrival_tax
    tax_rate DECIMAL(5,2) NOT NULL,
    tax_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    jurisdiction VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_centers (
    cost_center_id SERIAL PRIMARY KEY,
    cost_center_code VARCHAR(20) UNIQUE NOT NULL,
    cost_center_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_cost_center_id INTEGER REFERENCES cost_centers(cost_center_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mobile Application Tracking
CREATE TABLE mobile_app_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    device_type VARCHAR(20), -- ios, android, web
    device_id VARCHAR(100),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    actions_performed JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Intelligence
CREATE TABLE business_intelligence (
    bi_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,2) NOT NULL,
    metric_date DATE NOT NULL,
    dimension_1 VARCHAR(50),
    dimension_2 VARCHAR(50),
    dimension_3 VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Integration Hub
CREATE TABLE gds_integrations (
    gds_id SERIAL PRIMARY KEY,
    gds_name VARCHAR(20) NOT NULL, -- amadeus, sabre, travelport
    connection_status VARCHAR(20) DEFAULT 'active',
    last_sync_time TIMESTAMP,
    sync_frequency_minutes INTEGER DEFAULT 5,
    api_endpoint VARCHAR(200),
    credentials_encrypted TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE airport_systems (
    system_id SERIAL PRIMARY KEY,
    airport_id INTEGER REFERENCES airports(airport_id),
    system_type VARCHAR(50) NOT NULL, -- AODB, baggage, passenger_processing
    system_name VARCHAR(100) NOT NULL,
    connection_status VARCHAR(20) DEFAULT 'active',
    api_endpoint VARCHAR(200),
    last_sync_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE third_party_apis (
    api_id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL, -- hotel_booking, car_rental, insurance
    provider_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(200),
    api_key_encrypted TEXT,
    connection_status VARCHAR(20) DEFAULT 'active',
    last_sync_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training and Support System
CREATE TABLE training_modules (
    module_id SERIAL PRIMARY KEY,
    module_name VARCHAR(100) NOT NULL,
    module_type VARCHAR(20) NOT NULL, -- video, interactive, documentation
    target_role_id INTEGER REFERENCES user_roles(role_id),
    content_url VARCHAR(200),
    duration_minutes INTEGER,
    is_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_training_progress (
    progress_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    module_id INTEGER REFERENCES training_modules(module_id),
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE knowledge_base (
    kb_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],
    author_id INTEGER REFERENCES users(user_id),
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    status VARCHAR(20) DEFAULT 'open', -- open, in_progress, resolved, closed
    assigned_to INTEGER REFERENCES users(user_id),
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Operational Control Center
CREATE TABLE operational_control (
    control_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    control_type VARCHAR(50) NOT NULL, -- dispatch, maintenance, crew
    status VARCHAR(20) DEFAULT 'normal', -- normal, alert, critical
    message TEXT,
    action_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE crew_management (
    crew_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    crew_member_name VARCHAR(100) NOT NULL,
    crew_position VARCHAR(50) NOT NULL, -- pilot, co_pilot, flight_attendant
    employee_id VARCHAR(20),
    duty_start_time TIMESTAMP,
    duty_end_time TIMESTAMP,
    qualification_expiry DATE,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_schedule (
    maintenance_id SERIAL PRIMARY KEY,
    aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
    maintenance_type VARCHAR(50) NOT NULL, -- routine, inspection, repair
    scheduled_date DATE NOT NULL,
    completed_date DATE,
    description TEXT,
    technician VARCHAR(100),
    cost DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE emergency_contacts (
    contact_id SERIAL PRIMARY KEY,
    contact_type VARCHAR(50) NOT NULL, -- operations, maintenance, customer_service
    contact_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advanced Cargo Management
CREATE TABLE cargo_optimization (
    optimization_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    cargo_type VARCHAR(50) NOT NULL,
    capacity_kg DECIMAL(10,2) NOT NULL,
    utilized_kg DECIMAL(10,2) DEFAULT 0.00,
    utilization_rate DECIMAL(5,2) DEFAULT 0.00,
    revenue_per_kg DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dangerous_goods (
    dg_id SERIAL PRIMARY KEY,
    cargo_id INTEGER REFERENCES cargo_bookings(cargo_id),
    un_number VARCHAR(10),
    dg_class VARCHAR(20) NOT NULL,
    packing_group VARCHAR(5),
    proper_shipping_name TEXT,
    quantity DECIMAL(8,2),
    unit VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE special_cargo (
    special_cargo_id SERIAL PRIMARY KEY,
    cargo_id INTEGER REFERENCES cargo_bookings(cargo_id),
    cargo_type VARCHAR(50) NOT NULL, -- temperature_controlled, live_animals, valuable
    temperature_range VARCHAR(20),
    humidity_requirements VARCHAR(50),
    special_instructions TEXT,
    monitoring_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advanced Booking Management
CREATE TABLE waitlist_management (
    waitlist_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(flight_id),
    passenger_id INTEGER REFERENCES passengers(passenger_id),
    waitlist_position INTEGER NOT NULL,
    waitlist_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority_level VARCHAR(20) DEFAULT 'normal', -- normal, high, elite
    status VARCHAR(20) DEFAULT 'waiting', -- waiting, confirmed, cancelled
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE upgrade_management (
    upgrade_id SERIAL PRIMARY KEY,
    passenger_id INTEGER REFERENCES passengers(passenger_id),
    current_fare_class_id INTEGER REFERENCES fare_classes(fare_class_id),
    target_fare_class_id INTEGER REFERENCES fare_classes(fare_class_id),
    upgrade_type VARCHAR(20) NOT NULL, -- automatic, paid, bid
    upgrade_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, rejected
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE booking_modifications (
    modification_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    modification_type VARCHAR(20) NOT NULL, -- change, cancellation, refund
    original_data JSONB,
    modified_data JSONB,
    change_fee DECIMAL(10,2) DEFAULT 0.00,
    refund_amount DECIMAL(10,2) DEFAULT 0.00,
    reason TEXT,
    processed_by INTEGER REFERENCES users(user_id),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTA Integration Management
CREATE TABLE ota_integrations (
    ota_id SERIAL PRIMARY KEY,
    ota_name VARCHAR(20) NOT NULL, -- booking_com, expedia, skyscanner
    connection_status VARCHAR(20) DEFAULT 'active',
    api_endpoint VARCHAR(200),
    api_key_encrypted TEXT,
    commission_rate DECIMAL(5,2) DEFAULT 15.00,
    last_sync_time TIMESTAMP,
    sync_frequency_minutes INTEGER DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- AUDIT AND LOGGING TABLES
-- =====================================================

CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_logs (
    log_id SERIAL PRIMARY KEY,
    log_level VARCHAR(10) NOT NULL, -- info, warning, error, critical
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ADDITIONAL INDEXES FOR ADVANCED FEATURES
-- =====================================================

-- CRM indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_loyalty_tier ON customers(loyalty_tier);
CREATE INDEX idx_loyalty_programs_customer ON loyalty_programs(customer_id);
CREATE INDEX idx_customer_feedback_booking ON customer_feedback(booking_id);

-- Revenue analytics indexes
CREATE INDEX idx_revenue_analytics_date ON revenue_analytics(date);
CREATE INDEX idx_revenue_analytics_route ON revenue_analytics(route_id);
CREATE INDEX idx_yield_management_flight ON yield_management(flight_id);
CREATE INDEX idx_market_intelligence_route ON market_intelligence(route_id);

-- Business intelligence indexes
CREATE INDEX idx_business_intelligence_date ON business_intelligence(metric_date);
CREATE INDEX idx_business_intelligence_metric ON business_intelligence(metric_name);

-- Training and support indexes
CREATE INDEX idx_training_progress_user ON user_training_progress(user_id);
CREATE INDEX idx_support_tickets_user ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);

-- Operational control indexes
CREATE INDEX idx_operational_control_flight ON operational_control(flight_id);
CREATE INDEX idx_crew_management_flight ON crew_management(flight_id);
CREATE INDEX idx_maintenance_schedule_aircraft ON maintenance_schedule(aircraft_id);

-- Advanced booking indexes
CREATE INDEX idx_waitlist_flight ON waitlist_management(flight_id);
CREATE INDEX idx_upgrade_management_passenger ON upgrade_management(passenger_id);
CREATE INDEX idx_booking_modifications_booking ON booking_modifications(booking_id);

-- Audit and logging indexes
CREATE INDEX idx_audit_logs_user_date ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_system_logs_level_date ON system_logs(log_level, created_at);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Flight availability view with advanced metrics
CREATE VIEW flight_availability_advanced AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.departure_date,
    f.departure_time,
    f.arrival_time,
    f.flight_status,
    a.aircraft_type,
    a.total_seats,
    a.economy_seats,
    a.business_seats,
    (a.total_seats - COALESCE(COUNT(b.booking_id), 0)) as available_seats,
    COALESCE(COUNT(b.booking_id), 0) as booked_seats,
    ROUND((COALESCE(COUNT(b.booking_id), 0)::DECIMAL / a.total_seats * 100), 2) as load_factor,
    COALESCE(SUM(b.total_amount), 0) as total_revenue,
    COALESCE(AVG(b.total_amount), 0) as average_fare
FROM flights f
JOIN aircraft a ON f.aircraft_id = a.aircraft_id
LEFT JOIN bookings b ON f.flight_id = b.flight_id AND b.booking_status = 'confirmed'
WHERE f.is_active = true
GROUP BY f.flight_id, f.flight_number, f.departure_date, f.departure_time, f.arrival_time, 
         f.flight_status, a.aircraft_type, a.total_seats, a.economy_seats, a.business_seats;

-- Customer analytics view
CREATE VIEW customer_analytics AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.loyalty_tier,
    c.total_bookings,
    c.total_spent,
    ROUND(c.total_spent / NULLIF(c.total_bookings, 0), 2) as average_booking_value,
    COUNT(f.feedback_id) as feedback_count,
    ROUND(AVG(f.rating), 2) as average_rating,
    MAX(b.booking_date) as last_booking_date
FROM customers c
LEFT JOIN bookings b ON c.customer_id = b.customer_id
LEFT JOIN customer_feedback f ON c.customer_id = f.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_tier, c.total_bookings, c.total_spent;

-- Revenue summary by route and month
CREATE VIEW revenue_summary_advanced AS
SELECT 
    DATE_TRUNC('month', b.booking_date) as month,
    r.route_code,
    COUNT(b.booking_id) as total_bookings,
    SUM(b.total_amount) as total_revenue,
    AVG(b.total_amount) as average_fare,
    COUNT(DISTINCT b.agent_id) as active_agents,
    COUNT(DISTINCT b.customer_id) as unique_customers,
    ROUND(SUM(b.total_amount) / COUNT(b.booking_id), 2) as revenue_per_booking
FROM bookings b
JOIN flights f ON b.flight_id = f.flight_id
JOIN routes r ON f.route_id = r.route_id
WHERE b.booking_status = 'confirmed'
GROUP BY DATE_TRUNC('month', b.booking_date), r.route_code
ORDER BY month DESC, total_revenue DESC;

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Auto-update timestamps for advanced tables
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_loyalty_programs_updated_at BEFORE UPDATE ON loyalty_programs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gds_integrations_updated_at BEFORE UPDATE ON gds_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ota_integrations_updated_at BEFORE UPDATE ON ota_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON support_tickets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA FOR ADVANCED FEATURES
-- =====================================================

-- Insert sample customers
INSERT INTO customers (customer_code, first_name, last_name, email, phone, nationality, customer_type, loyalty_tier) VALUES
('CUST001', 'John', 'Smith', 'john.smith@email.com', '+66-81-234-5678', 'THA', 'individual', 'gold'),
('CUST002', 'Yuki', 'Tanaka', 'yuki.tanaka@email.com', '+81-90-1234-5678', 'JPN', 'individual', 'silver'),
('CUST003', 'Min', 'Kim', 'min.kim@email.com', '+82-10-1234-5678', 'KOR', 'individual', 'bronze'),
('CUST004', 'Wong', 'Chan', 'wong.chan@email.com', '+852-9123-4567', 'HKG', 'corporate', 'platinum');

-- Insert sample GDS integrations
INSERT INTO gds_integrations (gds_name, connection_status, sync_frequency_minutes) VALUES
('Amadeus', 'active', 5),
('Sabre', 'active', 5),
('Travelport', 'active', 5);

-- Insert sample OTA integrations
INSERT INTO ota_integrations (ota_name, connection_status, commission_rate) VALUES
('booking_com', 'active', 15.00),
('expedia', 'active', 18.00),
('skyscanner', 'active', 12.00);

-- Insert sample knowledge base articles
INSERT INTO knowledge_base (title, content, category, author_id) VALUES
('How to Create a New Booking', 'Step-by-step guide for creating passenger bookings...', 'Booking', 1),
('Cargo Booking Procedures', 'Complete guide for cargo booking and documentation...', 'Cargo', 1),
('Payment Processing Guide', 'How to process different payment methods...', 'Payments', 1);

-- =====================================================
-- END OF ADVANCED SCHEMA
-- ===================================================== 