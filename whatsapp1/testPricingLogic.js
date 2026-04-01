const { escalationHandler } = require('./whatsappEscalation');

console.log('🧪 Testing Welcome Message Detection');
console.log('='.repeat(50));

const testMessages = [
    'hi',
    'hello', 
    'NYC220',
    'how much is ctn fee for NYC220',
    'what is the cost',
    'help',
    'start',
    '123456',
    'ABC123',
    'good morning'
];

testMessages.forEach(msg => {
    const isFirstMessage = escalationHandler.isFirstMessage(msg);
    console.log(`'${msg}' -> Welcome Message: ${isFirstMessage}`);
});

console.log('\n✅ Test completed!'); 