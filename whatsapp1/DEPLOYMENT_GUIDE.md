# 🚀 WhatsApp Escalation Deployment Guide

## 📋 **Overview**

This guide shows you how to deploy the escalation system to your actual WhatsApp bot folder (where you have the node_modules and auth logs).

---

## 📁 **Files to Copy**

Copy these files from `iqstrade/whatsapp/` to your actual WhatsApp bot folder:

### **Required Files:**
1. `whatsappEscalation.js` - Main escalation handler
2. `escalationWrapper.js` - Wrapper for integration
3. `testEscalationStandalone.js` - Standalone test script

### **Modified Files:**
1. `package.json` - Add nodemailer dependency
2. `env.example` - Add escalation configuration

---

## 🔧 **Step-by-Step Deployment**

### **Step 1: Copy Files**
```bash
# Copy these files to your WhatsApp bot folder
cp whatsappEscalation.js /path/to/your/whatsapp-bot/
cp escalationWrapper.js /path/to/your/whatsapp-bot/
cp testEscalationStandalone.js /path/to/your/whatsapp-bot/
```

### **Step 2: Update package.json**
In your WhatsApp bot folder, add this to your `package.json` dependencies:
```json
{
  "dependencies": {
    // ... your existing dependencies
    "nodemailer": "^6.9.7"
  }
}
```

### **Step 3: Install Dependencies**
```bash
cd /path/to/your/whatsapp-bot/
npm install
```

### **Step 4: Update Environment Variables**
Add these to your `.env` file:
```bash
# WhatsApp Escalation Configuration
TEAM_EMAIL=your-team@iqstrade.com
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com
```

### **Step 5: Test the Integration**
```bash
cd /path/to/your/whatsapp-bot/
node testEscalationStandalone.js
```

Expected output:
```
🧪 Testing WhatsApp Escalation System (Standalone)
============================================================
📋 Test 1: Escalation Detection
'live chat' -> Escalation: true
'I want to speak to a human' -> Escalation: true
'人工客服' -> Escalation: true
'Hello, how are you?' -> Escalation: false

📋 Test 2: Escalation Response Generation
✅ Email configuration looks good!

✅ Standalone test completed!
```

### **Step 6: Integrate with messageRouter.js**
In your `messageRouter.js`, make these **2 minimal changes**:

**Change 1: Add import at the top**
```javascript
const { escalationWrapper } = require('./escalationWrapper');
```

**Change 2: Wrap chatHandler calls**
```javascript
// Find this line:
let reply = localFilePath && (!text || text.trim() === '')
  ? pdfFields && Object.keys(pdfFields).length > 0
    ? await chatHandler('', sender, pdfFields)
    : 'We received your receipt. Please provide your BL number or payment details so we can process your payment.'
  : await chatHandler(text, sender, pdfFields || {});

// Replace with:
let reply = localFilePath && (!text || text.trim() === '')
  ? pdfFields && Object.keys(pdfFields).length > 0
    ? await escalationWrapper(chatHandler, '', sender, pdfFields)
    : 'We received your receipt. Please provide your BL number or payment details so we can process your payment.'
  : await escalationWrapper(chatHandler, text, sender, pdfFields || {});
```

### **Step 7: Test with Real WhatsApp**
```bash
cd /path/to/your/whatsapp-bot/
npm start
```

Then test with these messages:
- Send "live chat" → Should trigger escalation
- Send "人工客服" → Should trigger escalation
- Send "What is my BL status?" → Should use normal bot logic

---

## 🧪 **Testing Scenarios**

### **Test 1: Escalation Detection**
1. Send "live chat" to your WhatsApp bot
2. Verify customer receives escalation response
3. Check team email notification
4. Verify escalation log entry

### **Test 2: Chinese Escalation**
1. Send "人工客服" to your WhatsApp bot
2. Verify same escalation flow works

### **Test 3: Normal Message**
1. Send "What is my BL status?" to your WhatsApp bot
2. Verify normal bot processing continues
3. Verify no escalation triggered

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
3. Test with `node testEscalationStandalone.js`

### **Module Not Found Errors:**
1. Make sure you copied all files
2. Run `npm install` to install nodemailer
3. Check file paths in require statements

---

## 📧 **Email Configuration**

### **Brevo SMTP Settings:**
- **Server:** smtp-relay.brevo.com
- **Port:** 587
- **Security:** STARTTLS
- **Authentication:** Username/Password

### **Environment Variables:**
```bash
TEAM_EMAIL=your-team@iqstrade.com
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com
```

---

## ✅ **Verification Checklist**

- [ ] Files copied to WhatsApp bot folder
- [ ] nodemailer dependency installed
- [ ] Environment variables configured
- [ ] Standalone test passes
- [ ] messageRouter.js updated
- [ ] WhatsApp bot starts without errors
- [ ] Escalation triggers on "live chat"
- [ ] Team receives email notifications
- [ ] Normal messages work as before

---

## 🎉 **Deployment Complete!**

Your WhatsApp bot now has professional escalation handling:

- ✅ **Detects escalation requests** in multiple languages
- ✅ **Sends professional responses** to customers
- ✅ **Notifies your team** via email
- ✅ **Tracks conversation history** for context
- ✅ **Logs all escalations** for monitoring
- ✅ **Preserves all existing functionality**

**Ready for production use!** 🚀 