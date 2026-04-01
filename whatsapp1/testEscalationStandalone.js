require('dotenv').config();

// Test the escalation system without WhatsApp dependencies
console.log('🧪 Testing WhatsApp Escalation System (Standalone)');
console.log('='.repeat(60));

// Test 1: Basic escalation detection
console.log('\n📋 Test 1: Escalation Detection');
const { escalationHandler } = require('./whatsappEscalation');

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

// Test 2: Escalation response generation
console.log('\n📋 Test 2: Escalation Response Generation');
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

// Test 3: Environment variables check
console.log('\n📋 Test 3: Environment Variables Check');
console.log('SMTP_SERVER:', process.env.SMTP_SERVER || 'Not set');
console.log('SMTP_USERNAME:', process.env.SMTP_USERNAME ? 'Set' : 'Not set');
console.log('SMTP_PASSWORD:', process.env.SMTP_PASSWORD ? 'Set' : 'Not set');
console.log('FROM_EMAIL:', process.env.FROM_EMAIL || 'Not set');
console.log('TEAM_EMAIL:', process.env.TEAM_EMAIL || 'Not set');

if (!process.env.SMTP_USERNAME || !process.env.SMTP_PASSWORD) {
  console.log('\n⚠️  Email notifications will not work without SMTP configuration');
  console.log('Please set up the following environment variables:');
  console.log('- SMTP_SERVER (default: smtp-relay.brevo.com)');
  console.log('- SMTP_USERNAME');
  console.log('- SMTP_PASSWORD');
  console.log('- FROM_EMAIL');
  console.log('- TEAM_EMAIL');
} else {
  console.log('\n✅ Email configuration looks good!');
}

// Test 4: Integration test (without actual email sending)
console.log('\n📋 Test 4: Integration Test (Simulated)');
const testConversationHistory = [
  {
    content: 'Hello, I need help with my shipment',
    fromCustomer: true,
    timestamp: new Date().toISOString()
  },
  {
    content: 'I can help you with that. What is your BL number?',
    fromCustomer: false,
    timestamp: new Date().toISOString()
  }
];

console.log('\n🔍 Testing escalation message: "live chat"');
console.log('Customer Data:', JSON.stringify(customerData, null, 2));
console.log('Conversation History:', JSON.stringify(testConversationHistory, null, 2));

console.log('\n✅ Standalone test completed!');
console.log('\n📝 Next steps:');
console.log('1. Copy these files to your actual WhatsApp bot folder:');
console.log('   - whatsappEscalation.js');
console.log('   - escalationWrapper.js');
console.log('   - package.json (add nodemailer dependency)');
console.log('2. Set up your .env file with email configuration');
console.log('3. Make the minimal changes to your messageRouter.js');
console.log('4. Test with real WhatsApp messages'); 