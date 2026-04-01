# 🚨 WhatsApp Escalation System Integration Guide

## 📋 **Overview**

This guide explains how the WhatsApp escalation system has been integrated into your existing WhatsApp bot. When customers type "live chat" or similar phrases, the system will:

1. **Detect the escalation request**
2. **Send a professional response to the customer**
3. **Notify your team via email**
4. **Log the escalation for tracking**

---

## 🔧 **What Was Added**

### **New Files:**
- `whatsappEscalation.js` - Main escalation handler (Node.js version)
- `testEscalation.js` - Test script to verify functionality
- `ESCALATION_INTEGRATION_GUIDE.md` - This guide

### **Modified Files:**
- `package.json` - Added nodemailer dependency
- `env.example` - Added escalation configuration
- `messageRouter.js` - Integrated escalation detection

---

## 🎯 **How It Works**

### **Message Flow:**
```
Customer Message → Escalation Check → Team Notification → Professional Response
```

1. **Customer sends message** to WhatsApp
2. **System checks** if message contains escalation keywords
3. **If escalation detected:**
   - Sends professional response to customer
   - Emails team with customer details and conversation history
   - Logs escalation for tracking
4. **If no escalation:** Continues with normal bot processing

### **Escalation Keywords:**
- `live chat`
- `human`
- `speak to someone`
- `talk to someone`
- `real person`
- `agent`
- `representative`
- `customer service`
- `support`
- `help me`
- `人工` (Chinese: human)
- `客服` (Chinese: customer service)
- `人工客服` (Chinese: human customer service)
- `真人` (Chinese: real person)
- `接线员` (Chinese: operator)

---

## 🚀 **Setup Instructions**

### **Step 1: Install Dependencies**
```bash
cd whatsapp
npm install
```

### **Step 2: Configure Environment Variables**
Create or update your `.env` file with these variables:

```bash
# Existing WhatsApp Bot Configuration
OPENAI_API_KEY=your_openai_api_key_here
RAILWAY_DB_HOST=your_db_host
RAILWAY_DB_USER=your_db_user
RAILWAY_DB_PASSWORD=your_db_password
RAILWAY_DB_NAME=your_db_name
RAILWAY_DB_PORT=5432
ADMIN_WA_ID=your_admin_whatsapp_id
PDF_EXTRACTION_URL=${FRONTEND_URL}/process_pdf

# WhatsApp Escalation Configuration
TEAM_EMAIL=your-team@iqstrade.com
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com
```

### **Step 3: Test the Integration**
```bash
node testEscalation.js
```

Expected output:
```
🧪 Testing WhatsApp Escalation System
==================================================
📋 Test 1: Escalation Detection
'live chat' -> Escalation: true
'I want to speak to a human' -> Escalation: true
'人工客服' -> Escalation: true
'Hello, how are you?' -> Escalation: false

📋 Test 2: Integration Test
✅ Integration test completed!

📋 Test 3: Environment Variables Check
✅ Email configuration looks good!

🎉 All tests completed!
```

### **Step 4: Start the Bot**
```bash
npm start
```

---

## 📧 **Email Notifications**

### **Team Notification Email:**
When escalation is triggered, your team receives an email with:

- **Subject:** `🚨 WhatsApp Escalation Request - [Customer Name]`
- **Content:**
  - Customer details (name, phone, email)
  - Escalation time
  - Recent conversation history (last 5 messages)
  - Quick action links (call, email, WhatsApp)
  - System information

### **Customer Response:**
Customers receive a professional message:
```
Hi [Name]! 👋

I understand you'd like to speak with a human representative. 

✅ **Your request has been escalated to our team**
📞 **We'll contact you within 5-10 minutes**

**What happens next:**
• Our team will review your conversation history
• They'll call you on this WhatsApp number
• They'll have full context of your enquiry

**In the meantime, you can also:**
📧 Email: info@iqstrade.com
📱 Phone: +852 XXXX XXXX
🏢 Office: [Your office address]

Thank you for your patience! 🙏
```

---

## 📊 **Logging and Monitoring**

### **Escalation Logs:**
- **File:** `logs/escalations.log`
- **Format:** JSON with timestamp, customer data, conversation history
- **Purpose:** Track escalation patterns and customer interactions

### **Console Logs:**
- Escalation detection: `🚨 Escalation triggered by [phone]`
- Email notifications: `✅ Team notification sent for escalation from [phone]`
- Logging: `📝 Escalation logged for [phone]`

---

## 🔧 **Customization Options**

### **Modify Escalation Keywords:**
Edit `whatsappEscalation.js` and update the `escalation_keywords` array:

```javascript
this.escalation_keywords = [
    'live chat',
    'human',
    // Add your custom keywords here
    'urgent help',
    'emergency'
];
```

### **Customize Customer Response:**
Modify the `getEscalationResponse()` method in `whatsappEscalation.js`:

```javascript
getEscalationResponse(customerName = null, customerPhone = null) {
    // Customize the response message here
    return `Your custom escalation response...`;
}
```

### **Enhance Customer Data:**
In `messageRouter.js`, you can enhance the customer data collection:

```javascript
const customerData = {
    name: await getCustomerName(sender), // Get from database
    phone: sender,
    email: await getCustomerEmail(sender), // Get from database
    company: await getCustomerCompany(sender) // Additional data
};
```

---

## 🧪 **Testing Scenarios**

### **Test 1: Basic Escalation**
1. Send "live chat" to WhatsApp bot
2. Verify customer receives escalation response
3. Check team email notification
4. Verify escalation log entry

### **Test 2: Chinese Escalation**
1. Send "人工客服" to WhatsApp bot
2. Verify same escalation flow works

### **Test 3: Normal Message**
1. Send "What is my BL status?" to WhatsApp bot
2. Verify normal bot processing continues
3. Verify no escalation triggered

### **Test 4: Conversation History**
1. Send multiple messages
2. Trigger escalation with "live chat"
3. Verify conversation history in team email

---

## 🚨 **Troubleshooting**

### **Email Notifications Not Working:**
1. Check SMTP configuration in `.env`
2. Verify Brevo credentials
3. Test email sending manually
4. Check console for error messages

### **Escalation Not Detected:**
1. Verify keywords in `whatsappEscalation.js`
2. Check message processing in `messageRouter.js`
3. Test with `node testEscalation.js`

### **Conversation History Missing:**
1. Check `conversationHistory` Map in `messageRouter.js`
2. Verify `addToConversationHistory()` calls
3. Check for JavaScript errors

---

## 📈 **Performance Considerations**

### **Memory Usage:**
- Conversation history limited to 10 messages per customer
- Automatic cleanup of old entries
- Efficient Map-based storage

### **Email Rate Limits:**
- Brevo SMTP has rate limits
- Consider batching notifications for high volume
- Monitor email delivery status

### **Database Integration:**
- Current implementation uses in-memory storage
- Consider database storage for production
- Add conversation persistence for better tracking

---

## 🔄 **Future Enhancements**

### **Potential Improvements:**
1. **Database Integration** - Store conversations in PostgreSQL
2. **Customer Profile** - Link to existing customer database
3. **Escalation Analytics** - Track escalation patterns
4. **Auto-Response Templates** - Customizable responses
5. **Integration with Main System** - Connect to IQS Trade backend
6. **Multi-language Support** - More language keywords
7. **Escalation Priority** - Different urgency levels
8. **Team Assignment** - Route to specific team members

---

## ✅ **Integration Complete!**

Your WhatsApp bot now has a complete escalation system that:

- ✅ **Detects escalation requests** in multiple languages
- ✅ **Sends professional responses** to customers
- ✅ **Notifies your team** via email
- ✅ **Tracks conversation history** for context
- ✅ **Logs all escalations** for monitoring
- ✅ **Integrates seamlessly** with existing bot logic

**Ready to test with real customers!** 🎉 