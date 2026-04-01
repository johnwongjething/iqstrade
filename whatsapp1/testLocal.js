require('dotenv').config();

console.log('🧪 Local Escalation System Test');
console.log('='.repeat(50));

// Test 1: Check if escalation files exist
console.log('\n📋 Test 1: File Check');
const fs = require('fs');
const files = [
  'whatsappEscalation.js',
  'escalationWrapper.js',
  'messageRouter.js'
];

files.forEach(file => {
  const exists = fs.existsSync(file);
  console.log(`${file}: ${exists ? '✅ Found' : '❌ Missing'}`);
});

// Test 2: Test escalation detection
console.log('\n📋 Test 2: Escalation Detection');
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
  console.log(`'${msg}' -> Escalation: ${isEscalation ? '🚨 YES' : '✅ NO'}`);
});

// Test 3: Test escalation response
console.log('\n📋 Test 3: Escalation Response');
const customerData = {
  name: 'John Doe',
  phone: '+852 1234 5678',
  email: 'john@example.com'
};

const response = escalationHandler.getEscalationResponse(
  customerData.name,
  customerData.phone
);

console.log('\n📧 Customer Response:');
console.log(response);

// Test 4: Test WhatsApp notification format
console.log('\n📋 Test 4: WhatsApp Notification Format');
const whatsappMessage = escalationHandler.buildWhatsAppNotification(customerData, [
  { content: 'Hello, I need help', fromCustomer: true },
  { content: 'I can help you. What do you need?', fromCustomer: false },
  { content: 'live chat', fromCustomer: true }
]);

console.log('\n📱 WhatsApp Alert (what you\'ll receive):');
console.log(whatsappMessage);

// Test 5: Test dummy call alert
console.log('\n📋 Test 5: Dummy Call Alert');
const dummyCallMessage = escalationHandler.buildDummyCallNotification(customerData);

console.log('\n📞 Dummy Call Alert (attention grabber):');
console.log(dummyCallMessage);

// Test 6: Environment check
console.log('\n📋 Test 6: Environment Variables');
console.log('ESCALATION_WA_ID:', process.env.ESCALATION_WA_ID || '❌ Not set');
console.log('ADMIN_WA_ID:', process.env.ADMIN_WA_ID || '❌ Not set');
console.log('SMTP_SERVER:', process.env.SMTP_SERVER || '❌ Not set');
console.log('TEAM_EMAIL:', process.env.TEAM_EMAIL || '❌ Not set');

console.log('\n✅ Local test completed!');
console.log('\n📝 To complete setup:');
console.log('1. Add to your .env file:');
console.log('   ESCALATION_WA_ID=85265381629@s.whatsapp.net');
console.log('   TEAM_EMAIL=johnwongjething@gmail.com');
console.log('   SMTP_SERVER=smtp-relay.brevo.com');
console.log('   SMTP_USERNAME=your_brevo_username');
console.log('   SMTP_PASSWORD=your_brevo_password');
console.log('   FROM_EMAIL=ray6330099@gmail.com');
console.log('2. Install nodemailer: npm install');
console.log('3. Copy files to your actual WhatsApp bot folder');
console.log('4. Test with real WhatsApp messages'); 