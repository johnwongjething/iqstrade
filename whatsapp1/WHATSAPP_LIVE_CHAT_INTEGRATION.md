# 🚨 WhatsApp Live Chat Escalation Integration Guide

## 📋 **Overview**

This guide shows how to integrate the "live chat" escalation feature into your existing WhatsApp bot. When customers type "live chat" or similar phrases, the system will:

1. **Detect the escalation request**
2. **Send a professional response to the customer**
3. **Notify your team via email**
4. **Log the escalation for tracking**

---

## 🎯 **How It Works**

### **Customer Experience:**
1. Customer chats with WhatsApp bot
2. If bot can't help or customer is frustrated
3. Customer types: **"live chat"**
4. Bot responds: *"Your request has been escalated to our team. We'll contact you within 5-10 minutes."*
5. Team gets immediate email notification
6. Team calls customer within 5-10 minutes

### **Team Notification:**
- **Email Subject**: `🚨 WhatsApp Escalation Request - [Customer Name]`
- **Email Content**: Customer details, conversation history, contact info
- **Action Required**: Call customer within 5-10 minutes

---

## 🔧 **Integration Steps**

### **Step 1: Add Environment Variables**

Add these to your `.env.local` file:

```bash
# WhatsApp Escalation Configuration
TEAM_EMAIL=your-team@iqstrade.com
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com
```

### **Step 2: Integrate with Your WhatsApp Bot**

#### **Option A: Node.js WhatsApp Bot (Baileys)**

Update your existing WhatsApp bot file:

```javascript
// In your WhatsApp bot file (e.g., whatsapp_bot.js)
const { handle_whatsapp_message } = require('./backend/utils/whatsapp_escalation.py');

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
            
            // Log escalation
            console.log(`🚨 Escalation triggered by ${sender.phone}`);
            
            // Stop further processing
            return;
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

#### **Option B: Python WhatsApp Bot**

Update your existing Python WhatsApp bot:

```python
# In your WhatsApp bot file
from utils.whatsapp_escalation import handle_whatsapp_message

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
            
            # Log escalation
            logger.info(f"🚨 Escalation triggered by {sender_info['phone']}")
            
            # Stop further processing
            return
        
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

### **Step 3: Test the Integration**

Run the test script:

```bash
cd backend
python utils/whatsapp_escalation.py
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
```

---

## 🎯 **Escalation Keywords**

The system detects these phrases as escalation requests:

### **English:**
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

### **Chinese:**
- `人工`
- `客服`
- `人工客服`
- `真人`
- `接线员`

---

## 📧 **Team Notification Email**

When escalation is triggered, your team receives an email like this:

```
Subject: 🚨 WhatsApp Escalation Request - John Doe

🚨 **WHATSAPP ESCALATION REQUEST**

**Customer Details:**
• Name: John Doe
• Phone: +852 1234 5678
• Time: 2025-01-15 14:30:25

**Action Required:**
Please call this customer within 5-10 minutes to provide human assistance.

**Recent Conversation:**
1. **Customer** (14:25:10):
   What's the status of my shipment BL-12345?

2. **Bot** (14:25:15):
   I found your shipment. It's currently in transit...

3. **Customer** (14:30:20):
   live chat

**Quick Actions:**
📞 Call: +852 1234 5678
📧 Email: john@example.com
🔗 WhatsApp: https://wa.me/85212345678

**System Info:**
• Escalation triggered by: "live chat" request
• Bot was unable to satisfy customer needs
• Customer explicitly requested human assistance

Please respond promptly to maintain customer satisfaction! 🙏
```

---

## 🔧 **Customization Options**

### **1. Customize Escalation Keywords**

Edit `backend/utils/whatsapp_escalation.py`:

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
        # Add more...
    ]
```

### **2. Customize Customer Response**

Edit the `get_escalation_response` method:

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
📱 Phone: +852 XXXX XXXX
🏢 Office: [Your office address]

Thank you for your patience! 🙏"""
    
    return response
```

### **3. Customize Team Email**

Edit the `_build_notification_email` method to include your specific contact information and branding.

---

## 📊 **Monitoring & Analytics**

### **Track Escalations**

Add database logging to track escalation patterns:

```python
def log_escalation(self, customer_data: Dict, conversation_history: list = None) -> None:
    try:
        # Connect to database
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Log escalation
        cursor.execute("""
            INSERT INTO whatsapp_escalations (
                customer_name, customer_phone, customer_email,
                escalation_time, conversation_history, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            customer_data.get('name'),
            customer_data.get('phone'),
            customer_data.get('email'),
            datetime.now(),
            json.dumps(conversation_history) if conversation_history else None,
            'pending'
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"📝 Escalation logged to database for {customer_data.get('phone', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Error logging escalation to database: {e}")
```

### **Database Schema**

Create the escalation tracking table:

```sql
CREATE TABLE whatsapp_escalations (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_email VARCHAR(255),
    escalation_time TIMESTAMP DEFAULT NOW(),
    conversation_history JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    team_response_time TIMESTAMP,
    resolution_time TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_whatsapp_escalations_phone ON whatsapp_escalations(customer_phone);
CREATE INDEX idx_whatsapp_escalations_status ON whatsapp_escalations(status);
CREATE INDEX idx_whatsapp_escalations_time ON whatsapp_escalations(escalation_time);
```

---

## 🚀 **Deployment Checklist**

### **Before Going Live:**

- [ ] **Environment Variables**: Set `TEAM_EMAIL`, `SMTP_*` variables
- [ ] **Email Testing**: Test team notification emails
- [ ] **Bot Integration**: Integrate escalation check in message handler
- [ ] **Database**: Create escalation tracking table (optional)
- [ ] **Team Training**: Train team on escalation process
- [ ] **Response Time**: Set expectations for 5-10 minute response time
- [ ] **Fallback**: Ensure team has backup contact methods

### **Post-Deployment Monitoring:**

- [ ] **Escalation Rate**: Monitor how often customers escalate
- [ ] **Response Time**: Track actual team response times
- [ ] **Customer Satisfaction**: Follow up with escalated customers
- [ ] **Bot Improvement**: Use escalation data to improve bot responses
- [ ] **Team Workload**: Monitor team capacity for escalations

---

## 🎯 **Benefits**

### **For Customers:**
- ✅ **Quick escalation** when bot can't help
- ✅ **Clear expectations** about response time
- ✅ **Multiple contact options** provided
- ✅ **Professional experience** maintained

### **For Your Team:**
- ✅ **Immediate notifications** when help needed
- ✅ **Full context** with conversation history
- ✅ **Structured process** for handling escalations
- ✅ **Tracking capabilities** for improvement

### **For Business:**
- ✅ **Reduced customer frustration**
- ✅ **Maintained customer satisfaction**
- ✅ **Data for bot improvement**
- ✅ **Professional customer service**

---

**Status**: ✅ **Ready for Integration**  
**Implementation Time**: 30-60 minutes  
**Testing Time**: 15 minutes  
**Risk Level**: 🟢 **Low** (non-intrusive addition) 