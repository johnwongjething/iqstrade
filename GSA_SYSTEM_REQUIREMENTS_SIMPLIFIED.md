# GSA (General Sales Agent) System Requirements — Simplified
## Single Airline (Lao Airlines) GSA Network

---

## Executive Summary
This document outlines the requirements for a streamlined GSA system focused on Lao Airlines ticket sales through a network of GSA agents across Asia (Japan, Thailand, Taiwan, Hong Kong, etc.). The system leverages proven security patterns from the iqstrade logistics system and is designed to be modular, scalable, and easy to maintain.

---

## Business Model
- **Single Airline**: Lao Airlines only
- **GSA Network**: Company-owned agents across Asian countries
- **Sales Focus**: Passenger tickets for Lao Airlines routes
- **Settlement**: Internal commission tracking and settlement
- **No GDS Required**: Manual flight management or simple airline data import

---

## Core Features & Modules

### 1. User Management & Security
- **Role-based access control (RBAC)**:
  - Company Admin (your friend's company)
  - Country/Regional Managers
  - GSA Agents (per country)
  - Lao Airlines Staff (read-only access)
- **Secure authentication**: JWT tokens, password reset, session management
- **Audit logs**: Track all booking, payment, and user actions
- **Encrypted sensitive data**: Passenger PII, payment information
- **Multi-language support**: English, Chinese, Thai, Japanese, etc.

### 2. Flight & Schedule Management
- **Flight schedule management**: Add/edit Lao Airlines routes and schedules
- **Seat inventory control**: Manage seat availability per flight
- **Fare management**: Set different fare classes and prices
- **Route management**: Define Lao Airlines routes (e.g., Vientiane-Bangkok, Vientiane-Tokyo)
- **Data import**: CSV/Excel import for flight schedules from Lao Airlines

### 3. Booking & Ticketing System
- **Flight search**: By route, date, passenger count
- **Seat selection**: Visual seat map or simple seat assignment
- **Passenger information**: Collect PNR data (name, passport, contact)
- **Booking workflow**: Search → Select → Passenger Info → Confirm → Payment → Ticket
- **E-ticket generation**: PDF ticket creation with Lao Airlines branding
- **Booking management**: View, modify, cancel bookings
- **PNR management**: Passenger Name Record tracking

### 4. Payment & Commission Tracking
- **Payment methods**: Bank transfer, cash, agency credit
- **Payment tracking**: Record payments against bookings
- **Commission calculation**: Automatic commission calculation per agent/agency
- **Settlement reports**: Monthly commission settlement reports
- **Payment status**: Pending, paid, overdue tracking

### 5. Reporting & Analytics
- **Sales reports**: By agent, country, route, date range
- **Commission reports**: Agent earnings and settlement
- **Passenger manifests**: For Lao Airlines compliance
- **Revenue tracking**: Total sales, payments received, outstanding
- **Agent performance**: Booking volume, revenue per agent
- **Export functionality**: PDF, Excel exports for reports

### 6. Communication & Notifications
- **Email notifications**: Booking confirmations, payment reminders, ticket delivery
- **WhatsApp integration**: Booking confirmations and updates
- **SMS notifications**: Payment reminders and flight updates
- **Multi-language templates**: Notifications in local languages

### 7. Admin & Configuration
- **Agency management**: Add/edit GSA agencies and agents
- **Commission rates**: Set different commission rates per agent/agency
- **System settings**: Email templates, notification preferences
- **User management**: Add/edit users, reset passwords, manage roles
- **Backup & maintenance**: Database backups, system monitoring

---

## Technical Architecture

### Frontend (React + Material-UI)
- **Admin Dashboard**: Flight management, user management, reporting
- **Agent Portal**: Booking interface, customer management, commission tracking
- **Customer Portal**: Flight search, booking, profile management
- **Responsive Design**: Mobile-friendly for agents on the go

### Backend (Flask + PostgreSQL)
- **RESTful APIs**: All core functionality
- **Database**: PostgreSQL with encrypted sensitive fields
- **File Storage**: PDF tickets, documents (Azure Blob/Cloudinary)
- **Background Jobs**: Email notifications, report generation

### Security & Compliance
- **Data encryption**: Sensitive fields encrypted in database
- **Audit logging**: All user actions logged
- **Role-based access**: Granular permissions per user role
- **Session management**: Secure JWT tokens with refresh
- **Data backup**: Regular automated backups

---

## Database Schema (High-Level)

### Core Tables
- `users` (agents, admins, airline staff)
- `agencies` (GSA agencies per country)
- `flights` (Lao Airlines flight schedules)
- `bookings` (passenger bookings)
- `passengers` (PNR data)
- `payments` (payment tracking)
- `commissions` (agent commission calculations)
- `audit_logs` (system activity tracking)

### Relationships
- Agencies have multiple agents
- Agents create multiple bookings
- Bookings have multiple passengers
- Payments are linked to bookings
- Commissions calculated from bookings

---

## User Interface Flow

### 1. Agent Login & Dashboard
- Agent logs in → sees dashboard with recent bookings, pending payments
- Quick stats: today's bookings, monthly revenue, commission earned

### 2. Flight Search & Booking
- Search flights: Route, date, passengers
- Select flight → choose seats → enter passenger details
- Confirm booking → payment tracking → generate ticket

### 3. Booking Management
- View all bookings (own and agency)
- Modify passenger details (if allowed)
- Cancel bookings (with policy enforcement)
- Generate/re-send tickets

### 4. Payment Tracking
- Record payments received
- Track outstanding payments
- Generate payment reports

### 5. Commission & Reports
- View commission earned
- Generate sales reports
- Export data for accounting

---

## Development Phases

### Phase 1: Core System (Weeks 1-3)
- User authentication and role management
- Flight and schedule management
- Basic booking system
- Payment tracking

### Phase 2: Enhanced Features (Weeks 4-5)
- E-ticket generation
- Commission calculation
- Basic reporting
- Email notifications

### Phase 3: Polish & Deploy (Week 6)
- WhatsApp integration
- Advanced reporting
- UI/UX improvements
- Testing and deployment

---

## Monthly Cost Estimate (USD)

| Service                | Description                        | Monthly Cost (USD) | Notes                                 |
|------------------------|------------------------------------|-------------------|---------------------------------------|
| Azure App Service      | Web/API hosting                    | $75               | Standard S1 (1.75GB RAM)              |
| Azure PostgreSQL       | Database hosting                   | $75               | Basic tier (100GB, 2 vCores)          |
| Azure Blob Storage     | File storage (tickets/docs)        | $5                | 50GB storage                          |
| Email (SendGrid)       | Transactional email                | $35               | 100,000 emails/month                  |
| WhatsApp Business API  | WhatsApp notifications             | $20               | 1,000 messages/month                  |
| Domain & SSL           | Domain name and certificate        | $2                | Annual cost divided by 12             |
| **Total**              |                                    | **$212**          | Estimated monthly operational cost    |

---

## Leveraging IQSTRADE Security Model

### Reusable Components
- **Authentication system**: JWT, password reset, session management
- **Database structure**: PostgreSQL with encrypted fields
- **Frontend framework**: React with Material-UI
- **Security patterns**: Audit logs, role-based access, data encryption
- **Deployment setup**: Azure/Render deployment configuration
- **Multi-language support**: Translation system

### Adaptations Needed
- **Booking workflow**: New booking-specific logic
- **Commission tracking**: New financial calculations
- **E-ticket generation**: PDF creation and delivery
- **Flight management**: Schedule and inventory management

---

## Success Metrics

### Technical Metrics
- **System uptime**: 99.5%+
- **Response time**: <2 seconds for booking operations
- **Data accuracy**: 100% booking and payment tracking
- **Security**: Zero data breaches, encrypted sensitive data

### Business Metrics
- **Agent adoption**: 90%+ of agents using system within 3 months
- **Booking volume**: Track monthly booking growth
- **Commission accuracy**: 100% accurate commission calculations
- **Customer satisfaction**: Reduced booking errors and faster ticket delivery

---

## Risk Mitigation

### Technical Risks
- **Data loss**: Regular backups, encrypted storage
- **System downtime**: Azure redundancy, monitoring
- **Security breaches**: Regular security audits, encrypted data

### Business Risks
- **Agent resistance**: Training, user-friendly interface
- **Data accuracy**: Validation rules, audit trails
- **Scalability**: Modular architecture, cloud hosting

---

## Future Enhancements (Post-MVP)

### Phase 2 Features (Months 2-3)
- **Mobile app**: Native mobile app for agents
- **Advanced analytics**: Business intelligence dashboard
- **API integration**: Direct connection to Lao Airlines systems
- **Multi-currency**: Support for different local currencies

### Phase 3 Features (Months 4-6)
- **AI chatbot**: Automated customer support
- **Advanced reporting**: Custom report builder
- **Integration APIs**: Third-party travel agent connections
- **Advanced security**: Biometric authentication, advanced fraud detection

---

## Getting Started

### Immediate Next Steps
1. **Database design**: Create detailed schema
2. **API specification**: Define all REST endpoints
3. **UI wireframes**: Design user interface flows
4. **Security plan**: Implement authentication and authorization
5. **Development timeline**: Set milestones and deliverables

### Development Approach
- **Agile methodology**: 2-week sprints with regular demos
- **Test-driven development**: Unit tests for all critical functions
- **Continuous integration**: Automated testing and deployment
- **Regular feedback**: Weekly demos and stakeholder input

---

*This simplified GSA system focuses on core functionality while maintaining scalability for future enhancements. The modular architecture ensures easy addition of features as the business grows.* 