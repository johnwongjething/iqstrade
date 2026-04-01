const { handleWelcomeMessage } = require('./whatsappEscalation');

async function testWelcomeMessages() {
    console.log('🧪 Testing Welcome Message Handler');
    console.log('='.repeat(50));
    
    // Test welcome message detection
    const testMessages = [
        'hi',
        'hello',
        'hey there',
        'good morning',
        'start',
        'help',
        'menu',
        '你好',
        '开始',
        'NYC220', // BL number - should NOT trigger welcome
        'how much is ctn fee and service fee for NYC220', // Pricing with BL - should NOT trigger welcome
        'what is the cost', // Generic pricing - should NOT trigger welcome
        '123456', // Pure number - should NOT trigger welcome
        'ABC123', // BL-like pattern - should NOT trigger welcome
        'What is the status of BL123456?', // Should NOT trigger welcome
        'Track my shipment', // Should NOT trigger welcome
        'Invoice payment', // Should NOT trigger welcome
        'live chat' // Should NOT trigger welcome (escalation)
    ];
    
    const customerData = {
        name: 'John Doe',
        phone: '+852 1234 5678',
        email: 'john@example.com'
    };
    
    for (const message of testMessages) {
        const result = await handleWelcomeMessage(message, customerData, []);
        console.log(`'${message}' -> Welcome: ${result.welcome_sent ? 'YES' : 'NO'}`);
        
        if (result.welcome_sent) {
            console.log('📧 Welcome Response:');
            console.log(result.response);
            console.log('---');
        }
    }
    
    console.log('\n✅ Welcome message test completed!');
    console.log('\n📝 How it works:');
    console.log('1. Detects common greeting patterns (hi, hello, help, etc.)');
    console.log('2. Detects Chinese greetings (你好, 开始, etc.)');
    console.log('3. Detects short messages that are likely greetings');
    console.log('4. Ignores business-specific queries (BL, invoice, track, etc.)');
    console.log('5. Sends professional welcome message with AI assistant info');
}

// Run test if this file is executed directly
if (require.main === module) {
    testWelcomeMessages().catch(console.error);
} 