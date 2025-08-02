# 📧 Automated Email Testing Guide

## 🎯 **Overview**
This guide will help you set up automated email testing for your email ingestor system. Instead of manually sending 8 test emails one by one, you can now send them all automatically!

## 🚀 **Quick Start**

### **Step 1: Set Up Email Configuration**

#### **Option A: Same Email for Sending and Receiving (Simplest)**
Create or update your `.env` file in the backend directory:

```bash
# Email Configuration (same email for sending and receiving)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_HOST=smtp.gmail.com

# Other configurations...
OPENAI_API_KEY=your-openai-key
```

#### **Option B: Different Emails for Sending and Receiving (More Realistic)**
```bash
# Sender Configuration
SENDER_EMAIL=your-sender@gmail.com
SENDER_PASSWORD=your-sender-app-password
SENDER_SMTP_HOST=smtp.gmail.com
SENDER_SMTP_PORT=587

# Target Configuration (where ingestor monitors)
TARGET_EMAIL=your-monitored-email@gmail.com

# Ingestor Configuration
EMAIL_USERNAME=your-monitored-email@gmail.com
EMAIL_PASSWORD=your-monitored-email-app-password
EMAIL_HOST=smtp.gmail.com

# Other configurations...
OPENAI_API_KEY=your-openai-key
```

### **Step 2: Gmail App Password Setup**
For Gmail, you need to use an App Password:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in your `.env` file

### **Step 3: Send Test Emails**

#### **Option A: Simple Email Sender (Same Email)**
```bash
python simple_email_sender.py
```

#### **Option B: Flexible Email Sender (Different Emails)**
```bash
python flexible_email_sender.py
```

### **Step 4: Process Emails**
After emails are sent, run the email ingestor:

```bash
python email_ingestor.py
```

## 📋 **Available Scripts**

### **1. Simple Email Sender** (`simple_email_sender.py`)
- ✅ **Recommended for beginners**
- ✅ Uses same email for sending and receiving
- ✅ No dependencies beyond standard Python
- ✅ Sends all 8 test emails automatically
- ✅ 2-second delay between emails to avoid rate limiting

### **2. Flexible Email Sender** (`flexible_email_sender.py`)
- ✅ **Recommended for realistic testing**
- ✅ Allows different sender and receiver emails
- ✅ More realistic email flow simulation
- ✅ Configurable SMTP settings
- ✅ Same 8 test emails with 2-second delays

### **3. Full Email Sender** (`auto_email_sender.py`)
- ✅ Includes PDF attachment support
- ✅ Requires `reportlab` library
- ✅ More comprehensive testing

### **4. Automated Test** (`test_email_automation.py`)
- ✅ Simulates email processing without sending real emails
- ✅ Uses mock data for testing
- ✅ Generates detailed reports

## 📧 **Test Email Details**

The system will send these 8 test emails:

| Email | Subject | Purpose | Key Features |
|-------|---------|---------|--------------|
| 1 | Fwd: 1 - CTN Request + Business Hours | Chinese email, CTN request | Chinese translation, BL validation |
| 2 | Fwd: 2 - Fee Inquiry + Payment Status | Fee inquiry | Invalid BL handling |
| 3 | Fwd: 3 - Payment Receipt (Overpayment) | Payment receipt | Missing attachment detection |
| 4 | Fwd: 4 - Multiple BL Fee Inquiry | Multiple BLs | Valid BL processing |
| 5 | Fwd: 5 - Payment Receipt (Bank Reference Test) | Bank reference test | **TEST987 filtering** |
| 6 | Fwd: 6 - PDF Payment Receipt | Empty email | Empty email handling |
| 7 | Fwd: 7 - Complex Payment with Multiple BLs | Complex payment | Multiple payment amounts |
| 8 | Fwd: 8 - Invoice + CTN Request (Invalid BL Test) | Invalid BL test | **445566 validation** |

## 🔧 **Troubleshooting**

### **Authentication Issues**
```
❌ Authentication failed. Please check your email credentials.
```
**Solution**: 
- Use App Password instead of regular password
- Enable 2-factor authentication
- Check email and password in `.env` file

### **SMTP Connection Issues**
```
❌ SMTP error: [Errno 11001] getaddrinfo failed
```
**Solution**:
- Check `EMAIL_HOST` in `.env` file
- For Gmail: use `smtp.gmail.com`
- Check internet connection

### **Rate Limiting**
```
❌ SMTP error: 421 4.7.0 Too many connections
```
**Solution**:
- The script already includes 2-second delays
- Wait a few minutes before running again
- Check Gmail sending limits

## 📊 **Expected Results**

After running the email ingestor, you should see:

### **Email 5 (Bank Reference Test)**
- ✅ **TEST987 filtered out** (not captured as BL)
- ✅ Only 001-123 and NYC220 processed
- ✅ Outstanding balance calculated correctly

### **Email 8 (Invalid BL Test)**
- ✅ **445566 identified as invalid**
- ✅ Only 001-123 and NYC220 processed
- ✅ Appropriate error message for invalid BL

### **All Other Emails**
- ✅ Appropriate classifications
- ✅ Contextual responses
- ✅ Professional tone maintained

## 🎯 **Testing Workflow**

### **Option 1: Real Email Testing**
```bash
# 1. Send test emails
python simple_email_sender.py

# 2. Process emails with ingestor
python email_ingestor.py

# 3. Check results in database
```

### **Option 2: Simulated Testing**
```bash
# Run automated test (no real emails sent)
python test_email_automation.py
```

## 📈 **Benefits of Automated Testing**

1. **Time Saving**: No need to manually send 8 emails
2. **Consistency**: Same test data every time
3. **Comprehensive**: Tests all scenarios automatically
4. **Repeatable**: Can run tests multiple times
5. **Documentation**: Generated reports for analysis

## 🚀 **Production Ready**

Your email ingestor system is now ready for:
- ✅ **Automated testing** with real emails
- ✅ **Bank reference filtering** (TEST987 excluded)
- ✅ **BL validation** (only valid BLs processed)
- ✅ **Professional responses** (auto-generated)
- ✅ **Multi-language support** (Chinese emails)

**Happy testing!** 🎉 