# 📋 **COMPREHENSIVE SYSTEM DOCUMENTATION**
## IQSTrade & WhatsApp App - Complete System Overview

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Frontend (React)**
- **Location**: `frontend/src/`
- **Framework**: React with Material-UI
- **Routing**: React Router v6
- **State Management**: React Hooks
- **Language Support**: Multi-language (English/Chinese)

### **Backend (Flask)**
- **Location**: `backend/`
- **Framework**: Flask with JWT authentication
- **Database**: PostgreSQL
- **File Storage**: Cloudinary
- **Email**: SMTP (Brevo)

### **WhatsApp Bot (Node.js)**
- **Location**: `whatsapp1/`
- **Framework**: Node.js with WhatsApp Web API
- **AI Integration**: OpenAI GPT
- **Database**: Same PostgreSQL as backend

---

## 🎯 **FRONTEND PAGES DOCUMENTATION**

### **1. PUBLIC PAGES**

#### **Home (`/`)**
- **File**: `frontend/src/pages/Home.js`
- **Purpose**: Landing page for customers
- **Features**:
  - Company introduction
  - Service overview
  - Contact information
  - Language switcher
- **Backend APIs**: None (static content)
- **Status**: ✅ **ACTIVE**

#### **About (`/about`)**
- **File**: `frontend/src/pages/About.js`
- **Purpose**: Company information page
- **Features**: Company history, mission, values
- **Backend APIs**: None (static content)
- **Status**: ✅ **ACTIVE**

#### **Services (`/services`)**
- **File**: `frontend/src/pages/Services.js`
- **Purpose**: Service offerings page
- **Features**: Shipping services, pricing, features
- **Backend APIs**: None (static content)
- **Status**: ✅ **ACTIVE**

#### **Contact (`/contact`)**
- **File**: `frontend/src/pages/Contact.js`
- **Purpose**: Contact form page
- **Features**:
  - Contact form
  - Email submission
  - Company contact details
- **Backend APIs**: 
  - `POST /api/contact` - Send contact email
- **Status**: ✅ **ACTIVE**

#### **FAQ (`/faq`)**
- **File**: `frontend/src/pages/FAQ.js`
- **Purpose**: Frequently asked questions
- **Features**: Q&A section, search functionality
- **Backend APIs**: None (static content)
- **Status**: ✅ **ACTIVE**

#### **Login (`/login`)**
- **File**: `frontend/src/pages/Login.js`
- **Purpose**: User authentication
- **Features**:
  - Username/password login
  - Geetest captcha
  - JWT token storage
  - Remember me functionality
- **Backend APIs**:
  - `POST /api/login` - User authentication
  - `POST /api/forgot-password` - Password reset
- **Status**: ✅ **ACTIVE**

#### **Register (`/register`)**
- **File**: `frontend/src/pages/Register.js`
- **Purpose**: New user registration
- **Features**:
  - User registration form
  - Email verification
  - Role selection (customer/staff)
- **Backend APIs**:
  - `POST /api/register` - User registration
- **Status**: ✅ **ACTIVE**

#### **Forgot Password (`/forgot-password`)**
- **File**: `frontend/src/pages/ForgotPassword.js`
- **Purpose**: Password recovery
- **Features**: Email-based password reset
- **Backend APIs**:
  - `POST /api/forgot-password` - Send reset email
- **Status**: ✅ **ACTIVE**

#### **Reset Password (`/reset-password/:token`)**
- **File**: `frontend/src/pages/ResetPassword.js`
- **Purpose**: Password reset with token
- **Features**: Token-based password reset
- **Backend APIs**:
  - `POST /api/reset-password` - Reset password
- **Status**: ✅ **ACTIVE**

#### **Forgot Username (`/forgot-username`)**
- **File**: `frontend/src/pages/ForgotUsername.js`
- **Purpose**: Username recovery
- **Features**: Email-based username recovery
- **Backend APIs**:
  - `POST /api/forgot-username` - Send username email
- **Status**: ✅ **ACTIVE**

### **2. AUTHENTICATED PAGES**

#### **Dashboard (`/dashboard`)**
- **File**: `frontend/src/pages/Dashboard.js`
- **Purpose**: Main user dashboard
- **Features**:
  - User welcome message
  - Role-based navigation
  - Quick access buttons
  - Staff-only features for 'ray40'
- **Backend APIs**:
  - `GET /api/user` - Get user info
- **Status**: ✅ **ACTIVE**

#### **Bill Search (`/search`)**
- **File**: `frontend/src/pages/BillSearch.js`
- **Purpose**: Search for bills of lading
- **Features**:
  - BL number search
  - Customer search
  - Date range filtering
  - Export functionality
- **Backend APIs**:
  - `GET /api/bills/search` - Search bills
  - `GET /api/bills/export` - Export results
- **Status**: ✅ **ACTIVE**

#### **Review Bills (`/review`)**
- **File**: `frontend/src/pages/Review.js`
- **Purpose**: Review and approve bills
- **Features**:
  - Pending bills list
  - Approval/rejection actions
  - Bulk operations
  - Status updates
- **Backend APIs**:
  - `GET /api/bills/pending` - Get pending bills
  - `POST /api/bills/approve` - Approve bill
  - `POST /api/bills/reject` - Reject bill
- **Status**: ✅ **ACTIVE**

#### **Upload Form (`/upload`)**
- **File**: `frontend/src/pages/UploadForm.js`
- **Purpose**: Upload bill documents
- **Features**:
  - PDF upload
  - OCR field extraction
  - Manual field editing
  - Invoice generation
- **Backend APIs**:
  - `POST /api/bills/upload` - Upload document
  - `POST /api/extract_fields` - Extract fields
  - `POST /api/bills/create` - Create bill
- **Status**: ✅ **ACTIVE**

#### **Edit Bill (`/edit-bill/:id`)**
- **File**: `frontend/src/pages/EditBill.js`
- **Purpose**: Edit existing bills
- **Features**:
  - Bill information editing
  - Field validation
  - Save changes
  - Invoice regeneration
- **Backend APIs**:
  - `GET /api/bills/:id` - Get bill details
  - `PUT /api/bills/:id` - Update bill
- **Status**: ✅ **ACTIVE**

#### **Edit/Delete Bills (`/edit-delete-bills`)**
- **File**: `frontend/src/pages/EditDeleteBills.js`
- **Purpose**: Bulk bill management
- **Features**:
  - List all bills
  - Bulk edit/delete
  - Search and filter
  - Status management
- **Backend APIs**:
  - `GET /api/bills` - Get all bills
  - `DELETE /api/bills/:id` - Delete bill
  - `PUT /api/bills/bulk` - Bulk update
- **Status**: ✅ **ACTIVE**

#### **Account Page (`/account-page`)**
- **File**: `frontend/src/pages/AccountPage.js`
- **Purpose**: User account management
- **Features**:
  - Profile information
  - Password change
  - Account settings
  - Activity history
- **Backend APIs**:
  - `GET /api/user/profile` - Get profile
  - `PUT /api/user/profile` - Update profile
  - `PUT /api/user/password` - Change password
- **Status**: ✅ **ACTIVE**

### **3. STAFF-ONLY PAGES**

#### **Staff Stats (`/staff-stats`)**
- **File**: `frontend/src/pages/StaffStats.js`
- **Purpose**: Staff performance statistics
- **Features**:
  - Processing statistics
  - Performance metrics
  - Charts and graphs
  - Export reports
- **Backend APIs**:
  - `GET /api/stats/staff` - Get staff stats
  - `GET /api/stats/export` - Export stats
- **Status**: ✅ **ACTIVE**

#### **User Approval (`/user-approval`)**
- **File**: `frontend/src/pages/UserApproval.js`
- **Purpose**: Approve new user registrations
- **Features**:
  - Pending users list
  - Approval/rejection
  - User details review
  - Role assignment
- **Backend APIs**:
  - `GET /api/admin/pending-users` - Get pending users
  - `POST /api/admin/approve-user` - Approve user
  - `POST /api/admin/reject-user` - Reject user
- **Status**: ✅ **ACTIVE**

#### **Management Dashboard (`/management-dashboard`)**
- **File**: `frontend/src/pages/ManagementDashboard.js`
- **Purpose**: High-level management overview
- **Features**:
  - System overview
  - Key metrics
  - Recent activities
  - Quick actions
- **Backend APIs**:
  - `GET /api/management/overview` - Get overview
  - `GET /api/management/metrics` - Get metrics
- **Status**: ✅ **ACTIVE**

#### **Bank Import (`/bank-import`)**
- **File**: `frontend/src/pages/BankImport.js`
- **Purpose**: Import bank statements
- **Features**:
  - CSV file upload
  - Payment matching
  - Transaction processing
  - Reconciliation
- **Backend APIs**:
  - `POST /api/bank/import` - Import statements
  - `GET /api/bank/transactions` - Get transactions
  - `POST /api/bank/match` - Match payments
- **Status**: ✅ **ACTIVE**

#### **Unmatched Bank Records (`/unmatched-bank-records`)**
- **File**: `frontend/src/pages/UnmatchedBankRecords.js`
- **Purpose**: Handle unmatched bank transactions
- **Features**:
  - Unmatched transactions list
  - Manual matching
  - Transaction details
  - Resolution tracking
- **Backend APIs**:
  - `GET /api/bank/unmatched` - Get unmatched
  - `POST /api/bank/manual-match` - Manual match
- **Status**: ✅ **ACTIVE**

#### **Customer Emails (`/customer-emails`)**
- **File**: `frontend/src/pages/CustomerEmails.js`
- **Purpose**: Manage customer email communications
- **Features**:
  - Email templates
  - Customer email history
  - Send emails
  - Email tracking
- **Backend APIs**:
  - `GET /api/emails/templates` - Get templates
  - `POST /api/emails/send` - Send email
  - `GET /api/emails/history` - Get history
- **Status**: ✅ **ACTIVE**

#### **Accounting Review (`/accounting-review`)**
- **File**: `frontend/src/pages/AccountingReview.js`
- **Purpose**: Review accounting records
- **Features**:
  - Payment records
  - Receipt management
  - Financial reports
  - Audit trail
- **Backend APIs**:
  - `GET /api/bills/awaiting_bank_in` - Get pending payments
  - `GET /api/accounting/reports` - Get reports
- **Status**: ✅ **ACTIVE**

### **4. TEST/DEVELOPMENT PAGES**

#### **Test Page (`/test`)**
- **File**: `frontend/src/pages/TestPage.js`
- **Purpose**: Development testing
- **Features**: Basic test functionality
- **Backend APIs**: None
- **Status**: ⚠️ **TEST ONLY**

#### **Test Page New (`/test-new`)**
- **File**: `frontend/src/pages/TestPageNew.js`
- **Purpose**: New test functionality
- **Features**: Advanced testing
- **Backend APIs**: None
- **Status**: ⚠️ **TEST ONLY**

#### **Notification Test3 (`/notification-test3`)**
- **File**: `frontend/src/pages/NotificationTest3.js`
- **Purpose**: FCM notification testing
- **Features**: Push notification testing
- **Backend APIs**:
  - `POST /api/fcm/test` - Test notifications
- **Status**: ⚠️ **TEST ONLY**

#### **FCM Setup (`/fcm-setup`)**
- **File**: `frontend/src/pages/FCMSetup.js`
- **Purpose**: Firebase Cloud Messaging setup
- **Features**:
  - FCM token management
  - Notification settings
  - Device registration
- **Backend APIs**:
  - `POST /api/fcm/register` - Register device
  - `GET /api/fcm/tokens` - Get tokens
- **Status**: ✅ **ACTIVE (Staff Only)**

#### **Test FCM Setup (`/test-fcm-setup`)**
- **File**: `frontend/src/pages/TestFCMSetup.js`
- **Purpose**: Test FCM functionality
- **Features**: FCM testing interface
- **Backend APIs**:
  - `POST /api/fcm/test` - Test notifications
- **Status**: ⚠️ **TEST ONLY**

#### **Minimal Test (`/minimal`)**
- **File**: `frontend/src/pages/MinimalTest.js`
- **Purpose**: Minimal test page
- **Features**: Basic functionality test
- **Backend APIs**: None
- **Status**: ⚠️ **TEST ONLY**

### **5. COMPONENTS**

#### **Navigation Bar**
- **File**: `frontend/src/pages/NavBar.js`
- **Purpose**: Main navigation component
- **Features**:
  - Responsive navigation
  - Language switcher
  - User menu
  - Mobile menu
- **Status**: ✅ **ACTIVE**

#### **WhatsApp Button**
- **File**: `frontend/src/pages/WhatsAppButton.js`
- **Purpose**: WhatsApp contact button
- **Features**: Floating WhatsApp button
- **Status**: ✅ **ACTIVE**

#### **WeChat Button**
- **File**: `frontend/src/pages/WeChatButton.js`
- **Purpose**: WeChat contact button
- **Features**: Floating WeChat button
- **Status**: ✅ **ACTIVE**

#### **Navigation Buttons**
- **File**: `frontend/src/components/NavigationButtons.js`
- **Purpose**: Reusable navigation buttons
- **Features**: Common navigation actions
- **Status**: ✅ **ACTIVE**

---

## 🔧 **BACKEND ROUTES DOCUMENTATION**

### **1. AUTHENTICATION ROUTES (`/api`)**

#### **Login**
- **Route**: `POST /api/login`
- **File**: `backend/routes/auth_routes.py`
- **Purpose**: User authentication
- **Features**: JWT token generation, Geetest captcha
- **Status**: ✅ **ACTIVE**

#### **Register**
- **Route**: `POST /api/register`
- **File**: `backend/routes/auth_routes.py`
- **Purpose**: User registration
- **Features**: Email verification, role assignment
- **Status**: ✅ **ACTIVE**

#### **Forgot Password**
- **Route**: `POST /api/forgot-password`
- **File**: `backend/routes/auth_routes.py`
- **Purpose**: Password recovery
- **Features**: Email-based reset
- **Status**: ✅ **ACTIVE**

#### **Reset Password**
- **Route**: `POST /api/reset-password`
- **File**: `backend/routes/auth_routes.py`
- **Purpose**: Password reset with token
- **Features**: Token validation
- **Status**: ✅ **ACTIVE**

#### **Forgot Username**
- **Route**: `POST /api/forgot-username`
- **File**: `backend/routes/auth_routes.py`
- **Purpose**: Username recovery
- **Features**: Email-based recovery
- **Status**: ✅ **ACTIVE**

### **2. BILL ROUTES (`/api`)**

#### **Upload Bill**
- **Route**: `POST /api/bills/upload`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Upload bill documents
- **Features**: File upload, OCR processing
- **Status**: ✅ **ACTIVE**

#### **Extract Fields**
- **Route**: `POST /api/extract_fields`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Extract fields from PDF
- **Features**: OpenAI/Google Vision OCR
- **Status**: ✅ **ACTIVE**

#### **Create Bill**
- **Route**: `POST /api/bills/create`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Create new bill record
- **Features**: Database insertion
- **Status**: ✅ **ACTIVE**

#### **Get Bill**
- **Route**: `GET /api/bills/:id`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Get bill details
- **Features**: Bill information retrieval
- **Status**: ✅ **ACTIVE**

#### **Update Bill**
- **Route**: `PUT /api/bills/:id`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Update bill information
- **Features**: Field updates
- **Status**: ✅ **ACTIVE**

#### **Delete Bill**
- **Route**: `DELETE /api/bills/:id`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Delete bill record
- **Features**: Soft delete
- **Status**: ✅ **ACTIVE**

#### **Search Bills**
- **Route**: `GET /api/bills/search`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Search bills
- **Features**: Advanced search, filtering
- **Status**: ✅ **ACTIVE**

#### **Get Pending Bills**
- **Route**: `GET /api/bills/pending`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Get bills pending review
- **Features**: Review queue
- **Status**: ✅ **ACTIVE**

#### **Approve Bill**
- **Route**: `POST /api/bills/approve`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Approve bill
- **Features**: Status update, email notification
- **Status**: ✅ **ACTIVE**

#### **Reject Bill**
- **Route**: `POST /api/bills/reject`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Reject bill
- **Features**: Status update, email notification
- **Status**: ✅ **ACTIVE**

#### **Awaiting Bank In**
- **Route**: `GET /api/bills/awaiting_bank_in`
- **File**: `backend/routes/bill_routes.py`
- **Purpose**: Get bills awaiting payment
- **Features**: Payment tracking
- **Status**: ✅ **ACTIVE**

### **3. STATS ROUTES (`/api`)**

#### **Staff Stats**
- **Route**: `GET /api/stats/staff`
- **File**: `backend/routes/stats_routes.py`
- **Purpose**: Get staff statistics
- **Features**: Performance metrics
- **Status**: ✅ **ACTIVE**

#### **Export Stats**
- **Route**: `GET /api/stats/export`
- **File**: `backend/routes/stats_routes.py`
- **Purpose**: Export statistics
- **Features**: CSV export
- **Status**: ✅ **ACTIVE**

### **4. ADMIN ROUTES (`/admin`)**

#### **Ingest Emails**
- **Route**: `POST /admin/ingest-emails`
- **File**: `backend/routes/admin_routes.py`
- **Purpose**: Manual email processing
- **Features**: Email ingestion
- **Status**: ✅ **ACTIVE**

#### **Pending Users**
- **Route**: `GET /api/admin/pending-users`
- **File**: `backend/routes/admin_routes.py`
- **Purpose**: Get pending user approvals
- **Features**: User management
- **Status**: ✅ **ACTIVE**

#### **Approve User**
- **Route**: `POST /api/admin/approve-user`
- **File**: `backend/routes/admin_routes.py`
- **Purpose**: Approve user registration
- **Features**: User activation
- **Status**: ✅ **ACTIVE**

#### **Reject User**
- **Route**: `POST /api/admin/reject-user`
- **File**: `backend/routes/admin_routes.py`
- **Purpose**: Reject user registration
- **Features**: User rejection
- **Status**: ✅ **ACTIVE**

### **5. MANAGEMENT ROUTES (`/api`)**

#### **Management Overview**
- **Route**: `GET /api/management/overview`
- **File**: `backend/routes/management_routes.py`
- **Purpose**: Get management overview
- **Features**: High-level metrics
- **Status**: ✅ **ACTIVE**

#### **Management Metrics**
- **Route**: `GET /api/management/metrics`
- **File**: `backend/routes/management_routes.py`
- **Purpose**: Get detailed metrics
- **Features**: Performance data
- **Status**: ✅ **ACTIVE**

### **6. FCM ROUTES (`/api`)**

#### **Register Device**
- **Route**: `POST /api/fcm/register`
- **File**: `backend/routes/fcm_routes.py`
- **Purpose**: Register FCM device
- **Features**: Token management
- **Status**: ✅ **ACTIVE**

#### **Get Tokens**
- **Route**: `GET /api/fcm/tokens`
- **File**: `backend/routes/fcm_routes.py`
- **Purpose**: Get FCM tokens
- **Features**: Token retrieval
- **Status**: ✅ **ACTIVE**

#### **Test Notifications**
- **Route**: `POST /api/fcm/test`
- **File**: `backend/routes/fcm_routes.py`
- **Purpose**: Test FCM notifications
- **Features**: Push notification testing
- **Status**: ✅ **ACTIVE**

### **7. BALANCE ROUTES (`/api`)**

#### **Get Balance**
- **Route**: `GET /api/balance/:username`
- **File**: `backend/routes/balance_routes.py`
- **Purpose**: Get customer balance
- **Features**: Balance retrieval
- **Status**: ✅ **ACTIVE**

#### **Update Balance**
- **Route**: `PUT /api/balance/:username`
- **File**: `backend/routes/balance_routes.py`
- **Purpose**: Update customer balance
- **Features**: Balance adjustment
- **Status**: ✅ **ACTIVE**

#### **Get Balance History**
- **Route**: `GET /api/balance/:username/history`
- **File**: `backend/routes/balance_routes.py`
- **Purpose**: Get balance history
- **Features**: Transaction history
- **Status**: ✅ **ACTIVE**

### **8. BANK ROUTES (`/api`)**

#### **Import Bank Statement**
- **Route**: `POST /api/bank/import`
- **File**: `backend/bank_routes.py`
- **Purpose**: Import bank statements
- **Features**: CSV processing
- **Status**: ✅ **ACTIVE**

#### **Get Transactions**
- **Route**: `GET /api/bank/transactions`
- **File**: `backend/bank_routes.py`
- **Purpose**: Get bank transactions
- **Features**: Transaction list
- **Status**: ✅ **ACTIVE**

#### **Match Payments**
- **Route**: `POST /api/bank/match`
- **File**: `backend/bank_routes.py`
- **Purpose**: Match payments to bills
- **Features**: Payment matching
- **Status**: ✅ **ACTIVE**

#### **Get Unmatched**
- **Route**: `GET /api/bank/unmatched`
- **File**: `backend/bank_routes.py`
- **Purpose**: Get unmatched transactions
- **Features**: Unmatched list
- **Status**: ✅ **ACTIVE**

#### **Manual Match**
- **Route**: `POST /api/bank/manual-match`
- **File**: `backend/bank_routes.py`
- **Purpose**: Manual payment matching
- **Features**: Manual matching
- **Status**: ✅ **ACTIVE**

### **9. EMAIL ROUTES (`/admin/email`)**

#### **Get Templates**
- **Route**: `GET /admin/email/templates`
- **File**: `backend/routes/email_routes.py`
- **Purpose**: Get email templates
- **Features**: Template management
- **Status**: ✅ **ACTIVE**

#### **Send Email**
- **Route**: `POST /admin/email/send`
- **File**: `backend/routes/email_routes.py`
- **Purpose**: Send customer emails
- **Features**: Email sending
- **Status**: ✅ **ACTIVE**

#### **Get History**
- **Route**: `GET /admin/email/history`
- **File**: `backend/routes/email_routes.py`
- **Purpose**: Get email history
- **Features**: Email tracking
- **Status**: ✅ **ACTIVE**

### **10. PAYMENT ROUTES**

#### **Payment Webhook**
- **Route**: `POST /api/webhook/payment`
- **File**: `backend/payment_webhook.py`
- **Purpose**: Payment webhook processing
- **Features**: Payment confirmation
- **Status**: ✅ **ACTIVE**

#### **Payment Link**
- **Route**: `GET /api/payment/:id`
- **File**: `backend/payment_link.py`
- **Purpose**: Payment link generation
- **Features**: Payment processing
- **Status**: ✅ **ACTIVE**

### **11. MISC ROUTES (`/api`)**

#### **Contact**
- **Route**: `POST /api/contact`
- **File**: `backend/routes/misc_routes.py`
- **Purpose**: Contact form submission
- **Features**: Email sending
- **Status**: ✅ **ACTIVE**

#### **Ping**
- **Route**: `GET /api/ping`
- **File**: `backend/routes/misc_routes.py`
- **Purpose**: Health check
- **Features**: System status
- **Status**: ✅ **ACTIVE**

#### **Root**
- **Route**: `GET /api/`
- **File**: `backend/routes/misc_routes.py`
- **Purpose**: API information
- **Features**: API overview
- **Status**: ✅ **ACTIVE**

---

## 📱 **WHATSAPP APP DOCUMENTATION**

### **Main Files**

#### **Chat Handler (`chatHandler.js`)**
- **File**: `whatsapp1/chatHandler.js`
- **Purpose**: Main message processing logic
- **Features**:
  - Message intent classification
  - Payment processing
  - Duplicate payment detection
  - Email verification
  - Balance management
  - Receipt generation
- **Status**: ✅ **ACTIVE**

#### **Database Utilities (`db.js`)**
- **File**: `whatsapp1/db.js`
- **Purpose**: Database operations
- **Features**:
  - Invoice information retrieval
  - BL validation
  - Payment status checking
- **Status**: ✅ **ACTIVE**

#### **Balance Utilities (`balance_utils_node.js`)**
- **File**: `whatsapp1/utils/balance_utils_node.js`
- **Purpose**: Balance management
- **Features**:
  - Payment processing
  - Duplicate detection
  - Balance adjustments
  - Transaction recording
- **Status**: ✅ **ACTIVE**

#### **Receipt Utilities (`receipt_utils.js`)**
- **File**: `whatsapp1/receipt_utils.js`
- **Purpose**: Receipt generation
- **Features**:
  - PDF generation
  - Cloudinary upload
  - Status updates
- **Status**: ✅ **ACTIVE**

#### **Logger (`logger.js`)**
- **File**: `whatsapp1/logger.js`
- **Purpose**: Logging functionality
- **Features**: Message logging
- **Status**: ✅ **ACTIVE**

#### **Duplicate Payment Notifications (`duplicate_payment_notifications.js`)**
- **File**: `whatsapp1/utils/duplicate_payment_notifications.js`
- **Purpose**: Handle duplicate payment alerts
- **Features**: Email notifications
- **Status**: ✅ **ACTIVE**

### **WhatsApp Features**

#### **Message Processing**
- **Intent Classification**: Uses OpenAI to classify message intent
- **BL Extraction**: Extracts bill of lading numbers from messages
- **Payment Detection**: Detects payment amounts and references
- **Email Verification**: Requires email verification for sensitive data

#### **Payment Processing**
- **Duplicate Detection**: Prevents duplicate payment processing
- **Balance Management**: Updates customer balances
- **Receipt Generation**: Creates and sends receipts
- **Overpayment Handling**: Manages overpayments and credits

#### **Customer Support**
- **Invoice Requests**: Handles invoice requests with email verification
- **CTN Number Requests**: Provides container numbers
- **Payment Status**: Checks payment status
- **Pricing Information**: Provides pricing details

#### **Security Features**
- **Email Verification**: Required for sensitive data access
- **Session Management**: Maintains conversation context
- **Rate Limiting**: Prevents spam
- **Input Validation**: Validates all inputs

---

## 🗑️ **POTENTIALLY UNUSED FILES**

### **Frontend Files to Review**

#### **Test Files (Consider for removal)**
- `frontend/src/pages/TestPage.js` - Basic test page
- `frontend/src/pages/TestPageNew.js` - New test page
- `frontend/src/pages/NotificationTest3.js` - FCM test
- `frontend/src/pages/TestFCMSetup.js` - FCM test setup
- `frontend/src/pages/MinimalTest.js` - Minimal test

#### **Commented Out Files**
- `frontend/src/pages/NotificationTestSimple.js` - Commented out
- `frontend/src/pages/NotificationTest2.js` - Commented out
- `frontend/src/pages/SimpleNotificationTest.js` - Commented out

#### **Backup Files**
- `frontend/src/pages/chat_backup.js` - WhatsApp backup
- `whatsapp1/chat_backup.js` - WhatsApp backup

### **Backend Files to Review**

#### **Test/Diagnostic Files**
- `diagnose_backend_routes.py` - Route diagnostic
- `backend_route_diagnostic_*.json` - Diagnostic results

#### **Old/Backup Files**
- `backend/chatHandler.js` - Old WhatsApp handler
- `backend/db.js` - Old database file

#### **Starter Files**
- `gsa_starter/` - GSA starter files (unused)

---

## 📊 **SYSTEM STATUS SUMMARY**

### **✅ ACTIVE COMPONENTS**
- **Frontend Pages**: 25 active pages
- **Backend Routes**: 40+ active routes
- **WhatsApp Features**: Complete payment processing system
- **Database**: PostgreSQL with all tables
- **File Storage**: Cloudinary integration
- **Email System**: SMTP with Brevo
- **Authentication**: JWT with Geetest captcha

### **⚠️ TEST/DEVELOPMENT COMPONENTS**
- **Test Pages**: 5 test pages
- **Diagnostic Tools**: 2 diagnostic files
- **Backup Files**: 2 backup files

### **🗑️ POTENTIAL CLEANUP**
- **Test Files**: 5 files
- **Backup Files**: 2 files
- **Diagnostic Files**: 2 files
- **Starter Files**: 1 directory

---

## 🔧 **RECOMMENDATIONS**

### **1. Safe to Remove**
- All test pages (`TestPage.js`, `TestPageNew.js`, etc.)
- Diagnostic files (`diagnose_backend_routes.py`)
- Backup files (`chat_backup.js`)
- GSA starter directory

### **2. Keep for Development**
- FCM setup pages (used by staff)
- Notification test pages (for debugging)

### **3. Review Before Removal**
- Any files with recent modifications
- Files referenced in comments
- Configuration files

This documentation provides a complete overview of the IQSTrade system and WhatsApp app, helping you identify which files are actively used and which can be safely removed. 