require('dotenv').config();
const { testEscalation, handleWhatsAppMessage } = require('./whatsappEscalation');

console.log('🧪 Testing WhatsApp Escalation System');
console.log('='.repeat(50));

// Test 1: Basic escalation detection
console.log('\n📋 Test 1: Escalation Detection');
testEscalation();

// Test 2: Integration test
console.log('\n📋 Test 2: Integration Test');
async function testIntegration() {
  const testCustomerData = {
    name: 'Test Customer',
    phone: '+852 1234 5678',
    email: 'test@example.com'
  };
  
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
  
  // Test escalation message
  console.log('\n🔍 Testing escalation message: "live chat"');
  const escalationResult = await handleWhatsAppMessage('live chat', testCustomerData, testConversationHistory);
  console.log('Escalation Result:', JSON.stringify(escalationResult, null, 2));
  
  // Test normal message
  console.log('\n🔍 Testing normal message: "What is my BL status?"');
  const normalResult = await handleWhatsAppMessage('What is my BL status?', testCustomerData, testConversationHistory);
  console.log('Normal Result:', JSON.stringify(normalResult, null, 2));
  
  console.log('\n✅ Integration test completed!');
}

testIntegration().catch(console.error);

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

console.log('\n🎉 All tests completed!');
console.log('\n📝 Next steps:');
console.log('1. Install dependencies: npm install');
console.log('2. Set up your .env file with email configuration');
console.log('3. Test with real WhatsApp messages');
console.log('4. Monitor escalation logs in the logs/ directory'); 