-- =====================================================
-- Lang Xeng Airlines GSA System - Core Database Schema
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
-- END OF CORE SCHEMA
-- ===================================================== 