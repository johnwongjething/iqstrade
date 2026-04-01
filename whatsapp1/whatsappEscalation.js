const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

class WhatsAppEscalationHandler {
    constructor() {
        this.escalation_keywords = [
            'live chat',
            'human',
            'speak to someone',
            'talk to someone',
            'real person',
            'agent',
            'representative',
            'customer service',
            'support',
            'help me',
            '人工',
            '客服',
            '人工客服',
            '真人',
            '接线员'
        ];
        
        // Email configuration for team notifications
        this.smtp_server = process.env.SMTP_SERVER || 'smtp-relay.brevo.com';
        this.smtp_username = process.env.SMTP_USERNAME;
        this.smtp_password = process.env.SMTP_PASSWORD;
        this.from_email = process.env.FROM_EMAIL;
        this.team_email = process.env.TEAM_EMAIL || this.from_email;
        
        // WhatsApp notification settings
        this.enable_whatsapp_notifications = process.env.ENABLE_WHATSAPP_NOTIFICATIONS !== 'false';
        
        // Initialize email transporter
        this.transporter = null;
        if (this.smtp_username && this.smtp_password) {
            this.transporter = nodemailer.createTransport({
                host: this.smtp_server,
                port: 587,
                secure: false,
                auth: {
                    user: this.smtp_username,
                    pass: this.smtp_password
                }
            });
        }
    }
    
    isEscalationRequest(message) {
        if (!message || typeof message !== 'string') return false;
        
        const messageLower = message.toLowerCase().trim();
        
        // Check for exact "live chat" match first
        if (messageLower === 'live chat') {
            return true;
        }
        
        // Check for other escalation keywords
        for (const keyword of this.escalation_keywords) {
            if (messageLower.includes(keyword)) {
                return true;
            }
        }
        
        return false;
    }
    
    isFirstMessage(message) {
        if (!message || typeof message !== 'string') return false;
        
        const messageLower = message.toLowerCase().trim();
        
        // Common first message patterns
        const firstMessagePatterns = [
            'hi',
            'hello',
            'hey',
            'good morning',
            'good afternoon',
            'good evening',
            'start',
            'begin',
            'help',
            'menu',
            'options',
            'what can you do',
            'how does this work',
            '你好',
            '您好',
            '嗨',
            '开始',
            '菜单',
            '帮助'
        ];
        
        // Check if message matches any first message pattern
        for (const pattern of firstMessagePatterns) {
            if (messageLower === pattern || messageLower.startsWith(pattern + ' ')) {
                return true;
            }
        }
        
        // Check if message is very short (likely a greeting) but exclude BL numbers, pricing questions, and escalation keywords
        if (messageLower.length <= 10 && 
            !messageLower.includes('bl') && 
            !messageLower.includes('invoice') && 
            !messageLower.includes('track') &&
            !messageLower.includes('ctn') &&
            !messageLower.includes('fee') &&
            !messageLower.includes('price') &&
            !messageLower.includes('cost') &&
            !messageLower.includes('pay') &&
            !messageLower.includes('payment') &&
            !messageLower.includes('live chat') &&
            !messageLower.includes('human') &&
            !messageLower.includes('agent') &&
            !messageLower.includes('representative') &&
            !messageLower.includes('support') &&
            !/^[a-z]{2,4}\d{2,}$/i.test(messageLower) && // Exclude BL-like patterns (e.g., NYC220)
            !/^\d{3,}$/i.test(messageLower) && // Exclude pure numbers
            !/^[a-z]{2,4}\d{3,}$/i.test(messageLower)) { // Exclude longer BL-like patterns
            return true;
        }
        
        return false;
    }
    
    getEscalationResponse(customerName = null, customerPhone = null) {
        const namePart = customerName ? ` ${customerName}` : "";
        
        return `Hi${namePart}! 👋

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

Thank you for your patience! 🙏`;
    }
    
    getWelcomeMessage(customerName = null) {
        const namePart = customerName ? ` ${customerName}` : "";
        
        return `👋 Hi${namePart}! Welcome to IQS Trade! 🚢

🤖 **I'm your AI Assistant** - here to help you with all your shipping and logistics needs.

**How I can help you:**
📦 Track shipments and containers
💰 Check payment status and invoices
📋 Get BL (Bill of Lading) information
🚢 Shipping schedules and updates
📞 Customer service inquiries

**💡 Please ask your questions very specifically:**
• "What's the status of BL number ABC123456?"
• "When will my container arrive at Hong Kong port?"
• "How much do I need to pay for invoice INV-2024-001?"
• "Track my shipment with container number ABCD1234567"

**Need human assistance?** Just type "live chat" and I'll connect you with our team.

What can I help you with today? 😊`;
    }
    
    async notifyTeam(customerData, conversationHistory = [], whatsappClient = null) {
        try {
            let notificationsSent = 0;
            
            // 1. Send email notification (PRIMARY - more reliable)
            if (this.transporter) {
                try {
                    const subject = `🚨 WhatsApp Escalation Request - ${customerData.name || 'Unknown Customer'}`;
                    const body = this.buildNotificationEmail(customerData, conversationHistory);
                    
                    const mailOptions = {
                        from: this.from_email,
                        to: this.team_email,
                        subject: subject,
                        text: body
                    };
                    
                    await this.transporter.sendMail(mailOptions);
                    console.log(`✅ Email notification sent for escalation from ${customerData.phone || 'Unknown'}`);
                    notificationsSent++;
                } catch (error) {
                    console.error('❌ Error sending email notification:', error);
                }
            }
            
            // 2. Send WhatsApp notification to escalation number (OPTIONAL - may be blocked)
            if (this.enable_whatsapp_notifications && whatsappClient && process.env.ESCALATION_WA_ID) {
                try {
                    // Add delay to avoid rate limiting
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    // Send detailed escalation message
                    const whatsappMessage = this.buildWhatsAppNotification(customerData, conversationHistory);
                    await whatsappClient.sendMessage(process.env.ESCALATION_WA_ID, { text: whatsappMessage });
                    console.log(`✅ WhatsApp notification sent to escalation number for escalation from ${customerData.phone || 'Unknown'}`);
                    
                    // Add delay between messages
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Send dummy call alert (attention grabber)
                    const dummyCallMessage = this.buildDummyCallNotification(customerData);
                    await whatsappClient.sendMessage(process.env.ESCALATION_WA_ID, { text: dummyCallMessage });
                    console.log(`📞 Dummy call alert sent to escalation number`);
                    
                    notificationsSent++;
                } catch (error) {
                    console.error('❌ Error sending WhatsApp notification (normal for private numbers):', error.message);
                    console.log('💡 Tip: Email notifications are more reliable for escalations');
                    console.log('💡 Tip: Consider using WhatsApp Business API for reliable notifications');
                }
            }
            
            return notificationsSent > 0;
            
        } catch (error) {
            console.error('❌ Error in team notification:', error);
            return false;
        }
    }
    
    buildWhatsAppNotification(customerData, conversationHistory = []) {
        const customerName = customerData.name || 'Unknown Customer';
        const customerPhone = customerData.phone || 'Unknown';
        const escalationTime = new Date().toLocaleString('en-US', {
            timeZone: 'Asia/Hong_Kong',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        let whatsappMessage = `🚨 *ESCALATION REQUEST*

*Customer:* ${customerName}
*Phone:* ${customerPhone}
*Time:* ${escalationTime}

*Action Required:* Call within 5-10 minutes

*Recent Conversation:*`;
        
        if (conversationHistory && conversationHistory.length > 0) {
            const recentMessages = conversationHistory.slice(-3); // Last 3 messages for WhatsApp
            recentMessages.forEach((msg, index) => {
                const sender = msg.fromCustomer ? 'Customer' : 'Bot';
                const content = msg.content || 'No content';
                
                whatsappMessage += `

${index + 1}. *${sender}:*
${content}`;
            });
        } else {
            whatsappMessage += `
No conversation history`;
        }
        
        whatsappMessage += `

*Quick Actions:*
📞 Call: ${customerPhone}
🔗 WhatsApp: https://wa.me/${customerPhone.replace('+', '')}

*Urgent - Customer requested human assistance!*`;
        
        return whatsappMessage;
    }
    
    buildDummyCallNotification(customerData) {
        const customerName = customerData.name || 'Unknown Customer';
        const customerPhone = customerData.phone || 'Unknown';
        const escalationTime = new Date().toLocaleString('en-US', {
            timeZone: 'Asia/Hong_Kong',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // This looks like a call notification to grab attention
        return `📞 *INCOMING CALL ALERT*

*Customer:* ${customerName}
*Number:* ${customerPhone}
*Time:* ${escalationTime}

🚨 *URGENT: Customer needs human assistance*

*This is NOT a real call - it's an escalation alert*

*Action Required:*
• Call customer within 5-10 minutes
• Customer typed "live chat" or similar
• They need immediate human support

*Quick Response:*
📞 Call: ${customerPhone}
🔗 WhatsApp: https://wa.me/${customerPhone.replace('+', '')}

*This alert will repeat every 2 minutes until you respond*`;
    }
    
    buildNotificationEmail(customerData, conversationHistory = []) {
        const customerName = customerData.name || 'Unknown Customer';
        const customerPhone = customerData.phone || 'Unknown';
        const escalationTime = new Date().toLocaleString('en-US', {
            timeZone: 'Asia/Hong_Kong',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        let emailBody = `
🚨 **WHATSAPP ESCALATION REQUEST**

**Customer Details:**
• Name: ${customerName}
• Phone: ${customerPhone}
• Time: ${escalationTime}

**Action Required:**
Please call this customer within 5-10 minutes to provide human assistance.

**Recent Conversation:**
`;
        
        if (conversationHistory && conversationHistory.length > 0) {
            const recentMessages = conversationHistory.slice(-5); // Last 5 messages
            recentMessages.forEach((msg, index) => {
                const sender = msg.fromCustomer ? 'Customer' : 'Bot';
                const timestamp = msg.timestamp || 'Unknown time';
                const content = msg.content || 'No content';
                
                emailBody += `
${index + 1}. **${sender}** (${timestamp}):
${content}
`;
            });
        } else {
            emailBody += 'No conversation history available.';
        }
        
        emailBody += `

**Quick Actions:**
📞 Call: ${customerPhone}
📧 Email: ${customerData.email || 'No email provided'}
🔗 WhatsApp: https://wa.me/${customerPhone.replace('+', '')}

**System Info:**
• Escalation triggered by: "live chat" request
• Bot was unable to satisfy customer needs
• Customer explicitly requested human assistance

Please respond promptly to maintain customer satisfaction! 🙏
`;
        
        return emailBody;
    }
    
    logEscalation(customerData, conversationHistory = []) {
        try {
            const escalationLog = {
                timestamp: new Date().toISOString(),
                customerData: customerData,
                conversationHistory: conversationHistory,
                status: 'pending'
            };
            
            console.log(`📝 Escalation logged for ${customerData.phone || 'Unknown'}`);
            console.log(`📝 Escalation details:`, JSON.stringify(escalationLog, null, 2));
            
            // You can extend this to save to a file or database
            const logDir = path.join(__dirname, 'logs');
            if (!fs.existsSync(logDir)) {
                fs.mkdirSync(logDir, { recursive: true });
            }
            
            const logFile = path.join(logDir, 'escalations.log');
            fs.appendFileSync(logFile, JSON.stringify(escalationLog) + '\n');
            
        } catch (error) {
            console.error('❌ Error logging escalation:', error);
        }
    }
}

// Global instance
const escalationHandler = new WhatsAppEscalationHandler();

async function handleWhatsAppMessage(message, customerData, conversationHistory = [], whatsappClient = null) {
    try {
        // Check if this is an escalation request
        const isEscalation = escalationHandler.isEscalationRequest(message);
        
        if (isEscalation) {
            // Generate escalation response
            const response = escalationHandler.getEscalationResponse(
                customerData.name,
                customerData.phone
            );
            
            // Notify team (both WhatsApp and email)
            const teamNotified = await escalationHandler.notifyTeam(customerData, conversationHistory, whatsappClient);
            
            // Log escalation
            escalationHandler.logEscalation(customerData, conversationHistory);
            
            return {
                escalation_requested: true,
                response: response,
                notify_team: teamNotified,
                customer_data: customerData
            };
        } else {
            // Not an escalation request, continue with normal bot processing
            return {
                escalation_requested: false,
                response: null,
                notify_team: false
            };
        }
        
    } catch (error) {
        console.error('❌ Error in WhatsApp escalation handler:', error);
        return {
            escalation_requested: false,
            response: null,
            notify_team: false,
            error: error.message
        };
    }
}

async function handleWelcomeMessage(message, customerData, conversationHistory = [], whatsappClient = null) {
    try {
        // Check if this is a first message/welcome scenario
        const isFirstMessage = escalationHandler.isFirstMessage(message);
        
        if (isFirstMessage) {
            // Generate welcome response
            const response = escalationHandler.getWelcomeMessage(
                customerData.name
            );
            
            return {
                welcome_sent: true,
                response: response,
                customer_data: customerData
            };
        } else {
            // Not a first message, continue with normal processing
            return {
                welcome_sent: false,
                response: null
            };
        }
        
    } catch (error) {
        console.error('❌ Error in welcome message handler:', error);
        return {
            welcome_sent: false,
            response: null,
            error: error.message
        };
    }
}

// Test function
function testEscalation() {
    console.log('🧪 Testing WhatsApp Escalation Handler');
    console.log('='.repeat(50));
    
    // Test escalation detection
    const testMessages = [
        'live chat',
        'I want to speak to a human',
        'Can I talk to someone?',
        '人工客服',
        'Hello, how are you?',
        'What\'s the status of my shipment?'
    ];
    
    testMessages.forEach(msg => {
        const isEscalation = escalationHandler.isEscalationRequest(msg);
        console.log(`'${msg}' -> Escalation: ${isEscalation}`);
    });
    
    // Test escalation response
    const customerData = {
        name: 'John Doe',
        phone: '+852 1234 5678',
        email: 'john@example.com'
    };
    
    const response = escalationHandler.getEscalationResponse(
        customerData.name,
        customerData.phone
    );
    
    console.log('\n📧 Escalation Response:');
    console.log(response);
    
    console.log('\n✅ Test completed!');
    console.log('\n📝 Next steps:');
    console.log('1. Add nodemailer to package.json dependencies');
    console.log('2. Set up environment variables (SMTP_SERVER, SMTP_USERNAME, etc.)');
    console.log('3. Integrate the handleWhatsAppMessage function into your bot');
    console.log('4. Test with real WhatsApp messages');
}

module.exports = {
    WhatsAppEscalationHandler,
    escalationHandler,
    handleWhatsAppMessage,
    handleWelcomeMessage,
    testEscalation
};

// Run test if this file is executed directly
if (require.main === module) {
    testEscalation();
} 