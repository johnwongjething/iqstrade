-- =====================================================
-- Lang Xeng Airlines GSA System Database Schema
-- Enterprise-Grade Multi-Country GSA Network
-- =====================================================

-- Database: gsa_langxeng_airlines
-- Character Set: UTF8
-- Collation: utf8_unicode_ci

-- =====================================================
-- CORE TABLES - Essential GSA Operations
-- =====================================================

-- Users and Authentication
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role_id INTEGER NOT NULL,
    agency_id INTEGER,
    country_code VARCHAR(3),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

CREATE TABLE user_roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GSA Agencies
CREATE TABLE agencies (
    agency_id SERIAL PRIMARY KEY,
    agency_code VARCHAR(10) UNIQUE NOT NULL,
    agency_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(50) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    contact_person VARCHAR(100),
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aircraft Fleet Management
CREATE TABLE aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    aircraft_type VARCHAR(20) NOT NULL, -- A320, ATR72
    registration VARCHAR(10) UNIQUE NOT NULL,
    model VARCHAR(50) NOT NULL,
    total_seats INTEGER NOT NULL,
    economy_seats INTEGER NOT NULL,
    business_seats INTEGER DEFAULT 0,
    premium_economy_seats INTEGER DEFAULT 0,
    cargo_capacity_kg DECIMAL(10,2),
    max_range_km INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aircraft_configurations (
    config_id SERIAL PRIMARY KEY,
    aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
    seat_map JSONB NOT NULL,
    seat_pricing JSONB,
    special_seats JSONB, -- exit rows, bulkhead, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routes and Airports
CREATE TABLE airports (
    airport_id SERIAL PRIMARY KEY,
    iata_code VARCHAR(3) UNIQUE NOT NULL,
    icao_code VARCHAR(4) UNIQUE,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(50) NOT NULL,
    timezone VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    route_code VARCHAR(10) UNIQUE NOT NULL,
    origin_airport_id INTEGER REFERENCES airports(airport_id),
    destination_airport_id INTEGER REFERENCES airports(airport_id),
    route_type VARCHAR(20) DEFAULT 'domestic', -- domestic, international
    distance_km INTEGER,
    estimated_duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flight Schedules
CREATE TABLE flight_schedules (
    schedule_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    route_id INTEGER REFERENCES routes(route_id),
    aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    days_of_week INTEGER[], -- 1=Monday, 7=Sunday
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_charter BOOLEAN DEFAULT FALSE,
    charter_customer VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE flights (
    flight_id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES flight_schedules(schedule_id),
    flight_number VARCHAR(10) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
    origin_airport_id INTEGER REFERENCES airports(airport_id),
    destination_airport_id INTEGER REFERENCES airports(airport_id),
    flight_status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, boarding, departed, arrived, cancelled, delayed
    actual_departure_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    delay_minutes INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fare Classes and Pricing
CREATE TABLE fare_classes (
    fare_class_id SERIAL PRIMARY KEY,
    fare_class_code VARCHAR(3) UNIQUE NOT NULL, -- Y, B, M, K, Q, etc.
    fare_class_name VARCHAR(50) NOT NULL, -- Economy, Business, Premium Economy
    description TEXT,
    baggage_allowance_kg INTEGER DEFAULT 20,
    cabin_class VARCHAR(20) DEFAULT 'economy',
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE pricing_strategies (
    strategy_id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    route_id INTEGER REFERENCES routes(route_id),
    fare_class_id INTEGER REFERENCES fare_classes(fare_class_id),
    base_fare DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    effective_from DATE NOT NULL,
    effective_to DATE,
    seasonal_adjustment JSONB,
    demand_multiplier DECIMAL(5,2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings and Passengers
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    pnr VARCHAR(10) UNIQUE NOT NULL,
    flight_id INTEGER REFERENCES flights(flight_id),
    booking_source VARCHAR(20) NOT NULL, -- direct, gsa_agent, booking_com, expedia, skyscanner
    agent_id INTEGER REFERENCES users(user_id),
    customer_id INTEGER,
    total_passengers INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    booking_status VARCHAR(20) DEFAULT 'confirmed', -- confirmed, cancelled, modified, waitlisted
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, refunded, partial
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE passengers (
    passenger_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    passenger_number INTEGER NOT NULL,
    title VARCHAR(10),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    passport_number VARCHAR(20),
    passport_expiry DATE,
    nationality VARCHAR(3),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    special_assistance TEXT,
    seat_assignment VARCHAR(10),
    fare_class_id INTEGER REFERENCES fare_classes(fare_class_id),
    ticket_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cargo Management
CREATE TABLE cargo_bookings (
    cargo_id SERIAL PRIMARY KEY,
    awb_number VARCHAR(20) UNIQUE NOT NULL,
    flight_id INTEGER REFERENCES flights(flight_id),
    shipper_name VARCHAR(100) NOT NULL,
    consignee_name VARCHAR(100) NOT NULL,
    cargo_type VARCHAR(50) NOT NULL, -- general, express, dangerous_goods, temperature_controlled
    weight_kg DECIMAL(8,2) NOT NULL,
    volume_cbm DECIMAL(8,3),
    pieces INTEGER DEFAULT 1,
    declared_value DECIMAL(10,2),
    insurance_amount DECIMAL(10,2),
    special_handling TEXT,
    is_dangerous_goods BOOLEAN DEFAULT FALSE,
    dg_classification VARCHAR(20),
    booking_status VARCHAR(20) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments and Financial Management
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    payment_method VARCHAR(20) NOT NULL, -- credit_card, bank_transfer, cash, digital_wallet
    payment_gateway VARCHAR(50),
    transaction_id VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commissions (
    commission_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    agent_id INTEGER REFERENCES users(user_id),
    agency_id INTEGER REFERENCES agencies(agency_id),
    commission_rate DECIMAL(5,2) NOT NULL,
    commission_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    commission_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, cancelled
    payment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Financial Management
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

-- Training and Support
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

-- Operational Control
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
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Core performance indexes
CREATE INDEX idx_bookings_pnr ON bookings(pnr);
CREATE INDEX idx_bookings_flight_date ON bookings(flight_id, departure_date);
CREATE INDEX idx_passengers_booking ON passengers(booking_id);
CREATE INDEX idx_flights_date_status ON flights(departure_date, flight_status);
CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_commissions_agent ON commissions(agent_id);

-- Search and filtering indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_agencies_country ON agencies(country_code);
CREATE INDEX idx_airports_iata ON airports(iata_code);
CREATE INDEX idx_routes_origin_dest ON routes(origin_airport_id, destination_airport_id);

-- Analytics and reporting indexes
CREATE INDEX idx_revenue_analytics_date ON revenue_analytics(date);
CREATE INDEX idx_revenue_analytics_route ON revenue_analytics(route_id);
CREATE INDEX idx_business_intelligence_date ON business_intelligence(metric_date);
CREATE INDEX idx_audit_logs_user_date ON audit_logs(user_id, created_at);

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agencies_updated_at BEFORE UPDATE ON agencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON flights FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert default user roles
INSERT INTO user_roles (role_name, description, permissions) VALUES
('System Administrator', 'Full system access', '{"all": true}'),
('Operations Manager', 'Flight schedule and pricing management', '{"flights": true, "pricing": true, "reports": true}'),
('Schedule Coordinator', 'Weekly schedule input and management', '{"schedules": true, "flights": true}'),
('Pricing Analyst', 'Pricing strategy and fare management', '{"pricing": true, "analytics": true}'),
('Regional Manager', 'Country-specific oversight', '{"reports": true, "agents": true}'),
('GSA Agent', 'Local booking and customer management', '{"bookings": true, "customers": true}'),
('Cargo Specialist', 'Cargo booking and management', '{"cargo": true, "bookings": true}');

-- Insert sample aircraft
INSERT INTO aircraft (aircraft_type, registration, model, total_seats, economy_seats, business_seats, cargo_capacity_kg) VALUES
('A320', 'RDPL-12345', 'Airbus A320-200', 180, 150, 30, 20000),
('ATR72', 'RDPL-67890', 'ATR 72-600', 78, 78, 0, 8000);

-- Insert sample airports
INSERT INTO airports (iata_code, icao_code, airport_name, city, country_code, country_name) VALUES
('VTE', 'VLVT', 'Wattay International Airport', 'Vientiane', 'LAO', 'Laos'),
('BKK', 'VTBS', 'Suvarnabhumi Airport', 'Bangkok', 'THA', 'Thailand'),
('NRT', 'RJAA', 'Narita International Airport', 'Tokyo', 'JPN', 'Japan'),
('ICN', 'RKSI', 'Incheon International Airport', 'Seoul', 'KOR', 'South Korea'),
('HKG', 'VHHH', 'Hong Kong International Airport', 'Hong Kong', 'HKG', 'Hong Kong');

-- Insert sample fare classes
INSERT INTO fare_classes (fare_class_code, fare_class_name, description, baggage_allowance_kg, cabin_class) VALUES
('Y', 'Economy', 'Standard economy class', 20, 'economy'),
('B', 'Economy', 'Economy class with flexibility', 25, 'economy'),
('M', 'Economy', 'Economy class with restrictions', 15, 'economy'),
('C', 'Business', 'Business class', 30, 'business'),
('F', 'First', 'First class', 40, 'first');

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Flight availability view
CREATE VIEW flight_availability AS
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
    ROUND((COALESCE(COUNT(b.booking_id), 0)::DECIMAL / a.total_seats * 100), 2) as load_factor
FROM flights f
JOIN aircraft a ON f.aircraft_id = a.aircraft_id
LEFT JOIN bookings b ON f.flight_id = b.flight_id AND b.booking_status = 'confirmed'
WHERE f.is_active = true
GROUP BY f.flight_id, f.flight_number, f.departure_date, f.departure_time, f.arrival_time, 
         f.flight_status, a.aircraft_type, a.total_seats, a.economy_seats, a.business_seats;

-- Revenue summary view
CREATE VIEW revenue_summary AS
SELECT 
    DATE_TRUNC('month', b.booking_date) as month,
    r.route_code,
    COUNT(b.booking_id) as total_bookings,
    SUM(b.total_amount) as total_revenue,
    AVG(b.total_amount) as average_fare,
    COUNT(DISTINCT b.agent_id) as active_agents
FROM bookings b
JOIN flights f ON b.flight_id = f.flight_id
JOIN routes r ON f.route_id = r.route_id
WHERE b.booking_status = 'confirmed'
GROUP BY DATE_TRUNC('month', b.booking_date), r.route_code
ORDER BY month DESC, total_revenue DESC;

-- =====================================================
-- END OF SCHEMA
-- ===================================================== 