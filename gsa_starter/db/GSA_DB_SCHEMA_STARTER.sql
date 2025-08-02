-- (moved from project root)
-- GSA System Starter Database Schema
-- For a single-airline (Lao Airlines) GSA network

-- USERS: All users (agents, admins, airline staff)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL, -- admin, manager, agent, airline_staff
    agency_id INTEGER REFERENCES agencies(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AGENCIES: GSA agencies per country
CREATE TABLE agencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    contact_email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FLIGHTS: Lao Airlines flight schedules
CREATE TABLE flights (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    origin VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    fare_class VARCHAR(20) NOT NULL, -- e.g. Economy, Business
    base_price NUMERIC(10,2) NOT NULL,
    seat_capacity INTEGER NOT NULL,
    seats_available INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BOOKINGS: Passenger bookings
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES users(id),
    flight_id INTEGER REFERENCES flights(id),
    booking_ref VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL, -- confirmed, cancelled, pending
    total_price NUMERIC(10,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL, -- paid, pending, overdue
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PASSENGERS: Passenger Name Record (PNR) data
CREATE TABLE passengers (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id),
    full_name VARCHAR(100) NOT NULL,
    passport_number VARCHAR(50),
    nationality VARCHAR(50),
    date_of_birth DATE,
    contact_phone VARCHAR(30),
    contact_email VARCHAR(100),
    seat_number VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PAYMENTS: Payment tracking
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id),
    amount NUMERIC(10,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL, -- bank_transfer, cash, agency_credit
    payment_date TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- paid, pending, failed
    reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- COMMISSIONS: Agent commission calculations
CREATE TABLE commissions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES users(id),
    booking_id INTEGER REFERENCES bookings(id),
    commission_rate NUMERIC(5,2) NOT NULL, -- percent
    commission_amount NUMERIC(10,2) NOT NULL,
    settled BOOLEAN DEFAULT FALSE,
    settled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT_LOGS: System activity tracking
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
); 