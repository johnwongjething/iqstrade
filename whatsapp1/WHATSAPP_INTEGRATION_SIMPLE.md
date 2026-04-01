# 🚨 WhatsApp Live Chat Integration - Simple Guide

## 📋 **Quick Setup for Separate WhatsApp Folder**

Since your WhatsApp system is in a separate folder, here's how to add the "live chat" escalation feature:

---

## 📁 **Files to Copy**

### **1. Copy the Escalation Handler**
Copy `whatsapp_escalation_standalone.py` to your WhatsApp bot folder.

### **2. Add Environment Variables**
Add these to your WhatsApp bot's `.env` file:

```bash
# WhatsApp Escalation Configuration
TEAM_EMAIL=your-team@iqstrade.com
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com
```

---

## 🔧 **Integration Steps**

### **Step 1: Test the Escalation Handler**
```bash
# In your WhatsApp bot folder
python whatsapp_escalation_standalone.py
```

Expected output:
```
🧪 Testing WhatsApp Escalation Handler
==================================================
'live chat' -> Escalation: True
'I want to speak to a human' -> Escalation: True
'Can I talk to someone?' -> Escalation: True
'人工客服' -> Escalation: True
'Hello, how are you?' -> Escalation: False
'What's the status of my shipment?' -> Escalation: False

📧 Escalation Response:
Hi John Doe! 👋

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

✅ Test completed!

📝 Next steps:
1. Copy this file to your WhatsApp bot folder
2. Set up environment variables (SMTP_SERVER, SMTP_USERNAME, etc.)
3. Integrate the handle_whatsapp_message function into your bot
4. Test with real WhatsApp messages
```

### **Step 2: Integrate with Your Bot**

#### **For Node.js WhatsApp Bot:**
```javascript
// In your main bot file
const { handle_whatsapp_message } = require('./whatsapp_escalation_standalone.py');

// In your message handler
async function handleMessage(message, sender) {
    try {
        // Get customer data
        const customerData = {
            name: sender.name || 'Unknown Customer',
            phone: sender.phone,
            email: sender.email || 'No email provided'
        };
        
        // Get conversation history (last 5 messages)
        const conversationHistory = await getConversationHistory(sender.phone);
        
        // Check for escalation first
        const escalationResult = await handle_whatsapp_message(
            message, 
            customerData, 
            conversationHistory
        );
        
        if (escalationResult.escalation_requested) {
            // Send escalation response
            await sendMessage(sender.phone, escalationResult.response);
            console.log(`🚨 Escalation triggered by ${sender.phone}`);
            return; // Stop further processing
        }
        
        // Continue with normal bot processing
        const botResponse = await processWithBot(message);
        await sendMessage(sender.phone, botResponse);
        
    } catch (error) {
        console.error('Error handling message:', error);
        await sendMessage(sender.phone, 'Sorry, there was an error. Please try again.');
    }
}
```

#### **For Python WhatsApp Bot:**
```python
# In your main bot file
from whatsapp_escalation_standalone import handle_whatsapp_message

def process_message(message, sender_info):
    try:
        # Prepare customer data
        customer_data = {
            'name': sender_info.get('name', 'Unknown Customer'),
            'phone': sender_info.get('phone'),
            'email': sender_info.get('email', 'No email provided')
        }
        
        # Get conversation history
        conversation_history = get_conversation_history(sender_info['phone'])
        
        # Check for escalation first
        escalation_result = handle_whatsapp_message(
            message, 
            customer_data, 
            conversation_history
        )
        
        if escalation_result['escalation_requested']:
            # Send escalation response
            send_whatsapp_message(
                sender_info['phone'], 
                escalation_result['response']
            )
            logger.info(f"🚨 Escalation triggered by {sender_info['phone']}")
            return  # Stop further processing
        
        # Continue with normal bot processing
        bot_response = process_with_bot(message)
        send_whatsapp_message(sender_info['phone'], bot_response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        send_whatsapp_message(
            sender_info['phone'], 
            'Sorry, there was an error. Please try again.'
        )
```

---

## 🎯 **How It Works**

### **Customer Types: "live chat"**
### **Bot Responds:**
```
Hi! 👋

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

### **Team Gets Email:**
```
Subject: 🚨 WhatsApp Escalation Request - [Customer Name]

🚨 **WHATSAPP ESCALATION REQUEST**

**Customer Details:**
• Name: John Doe
• Phone: +852 1234 5678
• Time: 2025-01-15 14:30:25

**Action Required:**
Please call this customer within 5-10 minutes to provide human assistance.

**Recent Conversation:**
1. **Customer** (14:25:10): What's the status of my shipment BL-12345?
2. **Bot** (14:25:15): I found your shipment. It's currently in transit...
3. **Customer** (14:30:20): live chat

**Quick Actions:**
📞 Call: +852 1234 5678
🔗 WhatsApp: https://wa.me/85212345678

Please respond promptly to maintain customer satisfaction! 🙏
```

---

## 🔧 **Customization**

### **Update Contact Information:**
Edit the `get_escalation_response` method in `whatsapp_escalation_standalone.py`:

```python
def get_escalation_response(self, customer_name: str = None, customer_phone: str = None) -> str:
    name_part = f" {customer_name}" if customer_name else ""
    
    response = f"""Hi{name_part}! 👋

I understand you'd like to speak with a human representative. 

✅ **Your request has been escalated to our team**
📞 **We'll contact you within 5-10 minutes**

**What happens next:**
• Our team will review your conversation history
• They'll call you on this WhatsApp number
• They'll have full context of your enquiry

**In the meantime, you can also:**
📧 Email: info@iqstrade.com
📱 Phone: +852 1234 5678  # Update this
🏢 Office: Your Office Address  # Update this

Thank you for your patience! 🙏"""
    
    return response
```

### **Add More Keywords:**
Edit the `escalation_keywords` list:

```python
def __init__(self):
    self.escalation_keywords = [
        'live chat',
        'human',
        'speak to someone',
        # Add your custom keywords here
        'urgent',
        'emergency',
        'manager',
        'supervisor',
        # Add more...
    ]
```

---

## ✅ **Deployment Checklist**

- [ ] **Copy file**: `whatsapp_escalation_standalone.py` to your WhatsApp folder
- [ ] **Environment variables**: Set SMTP settings in your `.env` file
- [ ] **Test escalation**: Run `python whatsapp_escalation_standalone.py`
- [ ] **Integrate code**: Add escalation check to your message handler
- [ ] **Test with bot**: Send "live chat" message to your bot
- [ ] **Verify email**: Check that team gets notification email
- [ ] **Update contacts**: Customize email/phone/office in response

---

## 🎯 **Benefits**

- ✅ **Quick setup**: Just copy one file
- ✅ **Non-intrusive**: Won't affect existing bot functionality
- ✅ **Professional**: Maintains customer experience
- ✅ **Immediate**: Team gets instant notifications
- ✅ **Trackable**: Logs all escalations for analysis

---

**Status**: ✅ **Ready to Copy**  
**Implementation Time**: 15-30 minutes  
**Risk Level**: 🟢 **Low** (standalone addition) 