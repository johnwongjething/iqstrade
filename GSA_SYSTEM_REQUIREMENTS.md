# GSA (General Sales Agent) System Requirements — Aviation (Passenger Ticketing)

## Executive Summary
This document outlines the requirements for a secure, scalable, and modern GSA system focused on passenger seat ticketing for airlines. The system is designed to be modular, cloud-ready, and compliant with industry security and privacy standards. It leverages proven security patterns from the iqstrade logistics system.

---

## Core Features & Modules

### 1. User Management & Security
- Role-based access control (RBAC): airline staff, GSA agents, travel agents, customers
- Secure authentication (MFA, JWT, OAuth)
- Audit logs for all actions
- Encrypted sensitive data (PII, payment info)

### 2. Flight Inventory & Schedule Management
- Import/sync flight schedules from airline(s)
- Real-time seat inventory updates
- Fare classes, seat maps, and availability

### 3. Booking & Ticketing
- Search flights (route, date, fare class)
- Book, hold, confirm, cancel seats
- Issue e-tickets (IATA/ARC/BSP integration)
- Manage PNRs (Passenger Name Records)
- Waitlist and upgrade management

### 4. Payment & Invoicing
- Multiple payment methods (credit card, bank transfer, agency credit)
- Secure payment processing (PCI DSS compliance)
- Automated invoicing and receipts
- Refunds and chargeback handling

### 5. Reporting & Analytics
- Sales reports (by airline, route, agent, period)
- Commission tracking and settlement
- Passenger manifests and regulatory reports
- Real-time dashboards

### 6. Customer Service & Communication
- Automated email/SMS notifications (booking, payment, reminders, changes)
- WhatsApp/WeChat/Chatbot integration
- Support ticketing system

### 7. Integration & APIs
- Airline GDS/CRS (Amadeus, Sabre, Galileo) or direct airline APIs
- BSP/ARC for ticket settlement
- Travel agent and customer portals
- Webhooks for real-time updates

### 8. Compliance & Security
- GDPR/PDPA/CCPA compliance
- Data encryption at rest and in transit
- Regular security audits and penetration testing
- Role-based data access and masking

### 9. Admin & Configuration
- Manage airlines, routes, fare rules, commissions
- User and agent management
- System settings, localization (multi-language, multi-currency)

---

## Security & Compliance
- All secrets in environment variables (.env or Azure Key Vault)
- Encrypted sensitive fields in DB
- Audit logs for all user actions
- Regular vulnerability scans
- Data retention and deletion policies

---

## Sample UI Flow (Text Description)
1. **Login:** User (agent, airline staff, or customer) logs in with secure authentication (MFA if required).
2. **Dashboard:** User sees a dashboard tailored to their role (e.g., agent sees bookings, airline sees sales stats).
3. **Flight Search:** User searches for flights by route, date, fare class.
4. **Booking:** User selects flight, chooses seat(s), enters passenger details, and confirms booking.
5. **Payment:** User pays via preferred method (credit card, bank transfer, agency credit).
6. **Ticket Issuance:** System issues e-ticket, sends confirmation via email/SMS/WhatsApp.
7. **Manage Bookings:** User can view, modify, or cancel bookings; request refunds if eligible.
8. **Reporting:** Admins and agents can generate sales, commission, and manifest reports.
9. **Support:** User can open a support ticket or chat with AI/human agent.

---

## Architecture Diagram
```mermaid
graph TD
    subgraph Frontend
        A[User Portal (Web/App)]
        B[Agent Portal]
        C[Admin Dashboard]
    end
    subgraph Backend
        D[GSA API Server]
        E[Background Workers]
        F[Notification Service]
    end
    subgraph Integrations
        G[Airline GDS/API]
        H[Payment Gateway]
        I[Email/SMS/WhatsApp]
        J[BSP/ARC]
    end
    subgraph Data
        K[(PostgreSQL DB)]
        L[(Blob/File Storage)]
        M[(Logs/Monitoring)]
    end
    A-->|REST/GraphQL|D
    B-->|REST/GraphQL|D
    C-->|REST/GraphQL|D
    D-->|DB|K
    D-->|File|L
    D-->|Logs|M
    D-->|GDS/API|G
    D-->|Payments|H
    D-->|BSP/ARC|J
    E-->|Notifications|F
    F-->|Email/SMS/WhatsApp|I
```

---

## Monthly Cost Estimate (USD)

| Service                | Description                        | Unit Cost         | Monthly Usage         | Monthly Cost (USD) | Notes                                 |
|------------------------|------------------------------------|-------------------|----------------------|--------------------|---------------------------------------|
| Azure App Service      | Web/API/Worker hosting             | ~$75/month        | 1 instance           | $75                | Standard S1 (1.75GB RAM, 50GB storage) |
| Azure PostgreSQL       | Database hosting                   | ~$75/month        | 1 instance           | $75                | Basic tier (100GB, 2 vCores)           |
| Azure Blob Storage     | File storage (tickets/docs)        | $0.0184/GB        | 15GB                 | $0.28              | 1MB/file, 500 uploads/day              |
| Azure Bandwidth        | Outbound data                      | $0.087/GB         | 10GB (over free tier)| $0.87              | First 5GB free                         |
| Email (SendGrid)       | Transactional email                | $34.95/100,000    | 100,000 emails        | $34.95             | Essentials plan                        |
| Domain                 | Domain name                        | $15/year          | 1                    | $1.25              | Annual cost divided by 12              |
| SSL                    | SSL certificate                    | Free              | 1                    | 0                  | Included with Azure/Let's Encrypt       |
| OpenAI (AI/Chatbot)    | GPT-4o for support/auto-replies    | $5/million input  | 24,000 messages       | $12                | Input tokens (100/msg)                 |
| OpenAI (AI/Chatbot)    | GPT-4o for support/auto-replies    | $15/million output| 24,000 messages       | $36                | Output tokens (100/msg)                |
| Total                  |                                    |                   |                      | $235.10            | Estimated monthly total                |

---

## Leveraging IQSTRADE Security Model
- Use .env for all secrets, never hardcode
- RBAC and audit logs for all user actions
- Encrypted DB fields for PII/payment
- Modular code for easy feature addition
- Rotating logs and error monitoring
- Cloud-ready deployment (Azure, AWS, etc.)

---

## Recommendations for Scaling & Future Features
- Add mobile app for agents/customers
- Integrate with more airline APIs/GDS
- Add AI-powered customer support and analytics
- Build unified admin dashboard for all channels
- Implement advanced fraud detection and compliance tools

---

*For more details or to start implementation, contact your AI assistant!* 