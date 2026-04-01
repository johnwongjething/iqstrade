# System Testing Guide

## 🎯 **Overview**

This guide provides comprehensive testing scripts for both Email and WhatsApp systems in your IQS Trade application. All tests use valid BL numbers from NYC220 to NYC247.

## 📧 **Email System Testing**

### **Available Test Scripts**

1. **`backend/test_system_comprehensive.py`** - Complete testing suite
2. **`backend/test_email_simple.py`** - Simple email testing only

### **Test Categories**

#### **Simple Email Tests (5 emails)**
- **Simple Payment**: Basic payment confirmation
- **CTN Request**: Request for CTN number
- **Invoice Request**: Request for invoice
- **Payment Status**: Check payment status
- **General Enquiry**: General questions

#### **Complex Email Tests (5 emails)**
- **Multiple BLs**: Multiple shipments in one email
- **Mixed Languages**: Chinese and English mixed
- **Irrelevant + Valid**: Weather chat + valid request
- **Complex Payment**: Partial payments and reserves
- **Multiple Requests**: Various requests in one email

### **How to Run Email Tests**

#### **Option 1: Comprehensive Testing**
```bash
cd backend
python test_system_comprehensive.py
```

Choose from:
- `1` - Simple tests only
- `2` - Complex tests only  
- `3` - Both simple and complex
- `4` - WhatsApp tests
- `5` - All tests
- `6` - Generate test report

#### **Option 2: Simple Email Testing**
```bash
cd backend
python test_email_simple.py
```

This will send 10 test emails covering all categories.

### **Email Test Examples**

#### **Simple Payment**
```
Subject: Payment for NYC220
Body: I have paid $200 for NYC220. Please confirm receipt.
```

#### **Multiple BLs**
```
Subject: Multiple shipments - NYC224, NYC225, NYC226
Body: I need information for multiple shipments:
1. NYC224: Payment status and CTN number
2. NYC225: Invoice and tracking details
3. NYC226: Reserve settlement amount
```

#### **Mixed Languages**
```
Subject: Mixed language request - NYC227
Body: 请问NYC227的CTN号码是多少？
Can you also send me the invoice for this shipment?
另外，什么时候可以安排提货？
When will the container be available for pickup?
```

## 📱 **WhatsApp System Testing**

### **Available Test Scripts**

1. **`whatsapp1/test_whatsapp_system.js`** - Complete WhatsApp testing

### **Test Categories**

#### **Simple WhatsApp Tests (5 messages)**
- **Simple Payment**: "I paid $200 for NYC233"
- **CTN Request**: "What is the CTN number for NYC234?"
- **Invoice Request**: "Can you send me the invoice for NYC235?"
- **Payment Status**: "What is the payment status for NYC236?"
- **General Question**: "Hello, how are you today?"

#### **Complex WhatsApp Tests (10 messages)**
- **Multiple BLs**: "I need info for NYC237, NYC238, and NYC239"
- **Mixed Languages**: "请问NYC240的CTN号码是多少？Can you also send invoice?"
- **Irrelevant + Valid**: "The weather is nice! What's the status of NYC241?"
- **Complex Request**: "I paid $150 for NYC242, need CTN, invoice, and arrival date"
- **Invalid BL**: "What's the status of NYC999?"
- **Multiple Requests**: "I need CTN for NYC230, invoice for NYC231, and payment status for NYC232"
- **Reserve Question**: "What is the reserve amount for NYC233?"
- **Arrival Date**: "When will NYC234 arrive at the port?"
- **Tracking Request**: "Can you track NYC235 for me?"
- **Pricing Question**: "What is the total cost for NYC236?"

### **How to Run WhatsApp Tests**

#### **Prerequisites**
1. Install dependencies:
```bash
cd whatsapp1
npm install
```

2. Set up environment variables in `.env`:
```bash
OPENAI_API_KEY=your_openai_key
RAILWAY_DB_HOST=your_db_host
RAILWAY_DB_USER=your_db_user
RAILWAY_DB_PASSWORD=your_db_password
RAILWAY_DB_NAME=your_db_name
RAILWAY_DB_PORT=your_db_port
ADMIN_WA_ID=whatsapp:+your_phone_number
```

#### **Run WhatsApp Tests**
```bash
cd whatsapp1
node test_whatsapp_system.js [choice]
```

Options:
- `1` - Simple tests only
- `2` - Complex tests only
- `3` - All tests (default)
- `4` - Generate test report only

## 🔧 **Test Configuration**

### **Environment Variables Required**

#### **Email Testing (.env.local)**
```bash
SMTP_SERVER=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=your_from_email
EMAIL_USERNAME=your_to_email
```

#### **WhatsApp Testing (.env)**
```bash
OPENAI_API_KEY=your_openai_key
RAILWAY_DB_HOST=your_db_host
RAILWAY_DB_USER=your_db_user
RAILWAY_DB_PASSWORD=your_db_password
RAILWAY_DB_NAME=your_db_name
RAILWAY_DB_PORT=your_db_port
ADMIN_WA_ID=whatsapp:+your_phone_number
```

## 📊 **Test Results Monitoring**

### **Email System**
1. **Check Email Inbox**: Verify test emails were received
2. **Monitor Email Scheduler**: `python email_scheduler.py`
3. **Check Database**: Review `customer_emails` table
4. **Check Logs**: Monitor `email_scheduler.log`

### **WhatsApp System**
1. **Check WhatsApp**: Verify bot responses
2. **Monitor Bot Logs**: Check console output
3. **Check Database**: Review message records
4. **Check OpenAI Usage**: Monitor API calls

## 🎯 **Test Scenarios Covered**

### **Simple Scenarios**
- ✅ Basic payment confirmations
- ✅ CTN number requests
- ✅ Invoice requests
- ✅ Payment status checks
- ✅ General enquiries

### **Complex Scenarios**
- ✅ Multiple BL numbers in one message
- ✅ Mixed language requests (Chinese/English)
- ✅ Irrelevant content + valid requests
- ✅ Partial payments and reserves
- ✅ Multiple requests in one message
- ✅ Invalid BL number handling
- ✅ Complex multi-part requests

### **Edge Cases**
- ✅ Invalid BL numbers (NYC999)
- ✅ Mixed irrelevant and relevant content
- ✅ Multiple languages
- ✅ Multiple requests
- ✅ Payment variations

## 📋 **Expected System Responses**

### **Email System**
- **Classification**: Should classify emails into categories
- **Auto-Reply**: Should generate appropriate draft replies
- **Database Storage**: Should store emails in `customer_emails` table
- **BL Extraction**: Should extract BL numbers from emails

### **WhatsApp System**
- **Response Generation**: Should generate appropriate responses
- **BL Recognition**: Should recognize valid BL numbers
- **Multi-language**: Should handle Chinese and English
- **Invalid Handling**: Should handle invalid BL numbers gracefully

## 🚀 **Quick Start Commands**

### **Email Testing**
```bash
# Quick email test (10 emails)
cd backend
python test_email_simple.py

# Comprehensive test
python test_system_comprehensive.py
```

### **WhatsApp Testing**
```bash
# Quick WhatsApp test (15 messages)
cd whatsapp1
node test_whatsapp_system.js

# Simple tests only
node test_whatsapp_system.js 1

# Complex tests only
node test_whatsapp_system.js 2
```

## 🔍 **Troubleshooting**

### **Email Issues**
- **SMTP Errors**: Check SMTP credentials in `.env.local`
- **Rate Limiting**: Wait between emails (3-second delay)
- **Missing Emails**: Check spam folder

### **WhatsApp Issues**
- **QR Code**: Scan QR code with WhatsApp
- **Authentication**: Check `ADMIN_WA_ID` format
- **Database**: Verify database connection
- **OpenAI**: Check API key and quota

## 📈 **Performance Expectations**

### **Email Processing**
- **Sending**: ~3 seconds per email
- **Processing**: ~1-2 minutes for email ingestion
- **Classification**: Should be accurate for valid requests

### **WhatsApp Processing**
- **Response Time**: ~2-5 seconds per message
- **Accuracy**: Should handle valid BL numbers correctly
- **Multi-language**: Should respond appropriately

## 🎉 **Success Criteria**

### **Email System**
- ✅ All test emails sent successfully
- ✅ Emails processed by ingestion system
- ✅ Appropriate classifications generated
- ✅ Draft replies created for valid requests

### **WhatsApp System**
- ✅ All test messages sent successfully
- ✅ Bot responds to valid BL numbers
- ✅ Handles invalid BL numbers gracefully
- ✅ Supports both Chinese and English
- ✅ Generates appropriate responses

---

**Valid BL Numbers for Testing**: NYC220 to NYC247 (28 total)
**Total Test Cases**: 25 (10 email + 15 WhatsApp)
**Coverage**: Simple, complex, edge cases, multi-language 