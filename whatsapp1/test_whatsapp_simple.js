#!/usr/bin/env node
/**
 * Simple WhatsApp Testing Script
 * Tests the chat handler logic without requiring WhatsApp Web setup
 * Valid BL numbers: NYC220 to NYC247
 */

require('dotenv').config();

// Mock the WhatsApp client for testing
class MockWhatsAppClient {
    constructor() {
        this.messages = [];
    }
    
    async sendMessage(to, message) {
        this.messages.push({ to, message });
        console.log(`📱 [MOCK] Message sent to ${to}: ${message}`);
        return { key: { id: 'mock-message-id' } };
    }
}

// Import the chat handler logic
const { getIntentAndResponse } = require('./chatHandler');

class SimpleWhatsAppTester {
    constructor() {
        this.client = new MockWhatsAppClient();
        this.validBLs = [];
        
        // Generate valid BL numbers (NYC220 to NYC247)
        for (let i = 220; i <= 247; i++) {
            this.validBLs.push(`NYC${i}`);
        }
        
        console.log('🔧 Simple WhatsApp Tester Initialized');
        console.log('='.repeat(50));
        console.log(`📋 Valid BLs: ${this.validBLs.length} (NYC220-NYC247)`);
        console.log('='.repeat(50));
    }

    getSimpleTests() {
        return [
            {
                category: 'Simple Payment',
                message: 'I paid $200 for NYC220'
            },
            {
                category: 'CTN Request',
                message: 'What is the CTN number for NYC221?'
            },
            {
                category: 'Invoice Request',
                message: 'Can you send me the invoice for NYC222?'
            },
            {
                category: 'Payment Status',
                message: 'What is the payment status for NYC223?'
            },
            {
                category: 'General Question',
                message: 'Hello, how are you today?'
            }
        ];
    }

    getComplexTests() {
        return [
            {
                category: 'Multiple BLs',
                message: 'I need info for NYC224, NYC225, and NYC226'
            },
            {
                category: 'Mixed Languages',
                message: '请问NYC227的CTN号码是多少？Can you also send invoice?'
            },
            {
                category: 'Irrelevant + Valid',
                message: 'The weather is nice! What\'s the status of NYC228?'
            },
            {
                category: 'Complex Request',
                message: 'I paid $150 for NYC229, need CTN, invoice, and arrival date'
            },
            {
                category: 'Invalid BL',
                message: 'What\'s the status of NYC999?'
            },
            {
                category: 'Multiple Requests',
                message: 'I need CTN for NYC230, invoice for NYC231, and payment status for NYC232'
            },
            {
                category: 'Reserve Question',
                message: 'What is the reserve amount for NYC233?'
            },
            {
                category: 'Arrival Date',
                message: 'When will NYC234 arrive at the port?'
            },
            {
                category: 'Tracking Request',
                message: 'Can you track NYC235 for me?'
            },
            {
                category: 'Pricing Question',
                message: 'What is the total cost for NYC236?'
            }
        ];
    }

    async testChatHandler(message, validBLs, invalidBLs = []) {
        try {
            console.log(`\n🤖 Testing: "${message}"`);
            console.log(`   Valid BLs: ${validBLs.join(', ')}`);
            console.log(`   Invalid BLs: ${invalidBLs.join(', ')}`);
            
            // Create a mock conversation history
            const history = [
                { role: 'system', content: 'You are a helpful shipping assistant.' }
            ];
            
            // Test the chat handler logic
            const result = await getIntentAndResponse(message, history, validBLs, invalidBLs);
            
            console.log(`   ✅ Intent: ${result.intent}`);
            console.log(`   ✅ BL Number: ${result.bl_number || 'None'}`);
            console.log(`   ✅ Answer: ${result.answer.substring(0, 100)}...`);
            
            return result;
        } catch (error) {
            console.error(`   ❌ Error: ${error.message}`);
            return null;
        }
    }

    async testSimple() {
        console.log('\n📱 Testing Simple WhatsApp Messages');
        console.log('='.repeat(50));
        
        const tests = this.getSimpleTests();
        let successful = 0;
        let failed = 0;

        for (let i = 0; i < tests.length; i++) {
            const test = tests[i];
            console.log(`\n📱 Test ${i + 1}: ${test.category}`);
            console.log(`   Message: ${test.message}`);
            
            const result = await this.testChatHandler(test.message, this.validBLs);
            
            if (result) {
                console.log('   ✅ Test successful!');
                successful++;
            } else {
                console.log('   ❌ Test failed');
                failed++;
            }
            
            // Wait between tests
            if (i < tests.length - 1) {
                console.log('   ⏳ Waiting 1 second...');
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        console.log(`\n📊 Simple Test Results:`);
        console.log(`   ✅ Successful: ${successful}`);
        console.log(`   ❌ Failed: ${failed}`);
        console.log(`   📱 Total: ${tests.length}`);
    }

    async testComplex() {
        console.log('\n📱 Testing Complex WhatsApp Messages');
        console.log('='.repeat(50));
        
        const tests = this.getComplexTests();
        let successful = 0;
        let failed = 0;

        for (let i = 0; i < tests.length; i++) {
            const test = tests[i];
            console.log(`\n📱 Test ${i + 1}: ${test.category}`);
            console.log(`   Message: ${test.message}`);
            
            const result = await this.testChatHandler(test.message, this.validBLs);
            
            if (result) {
                console.log('   ✅ Test successful!');
                successful++;
            } else {
                console.log('   ❌ Test failed');
                failed++;
            }
            
            // Wait between tests
            if (i < tests.length - 1) {
                console.log('   ⏳ Waiting 1 second...');
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        console.log(`\n📊 Complex Test Results:`);
        console.log(`   ✅ Successful: ${successful}`);
        console.log(`   ❌ Failed: ${failed}`);
        console.log(`   📱 Total: ${tests.length}`);
    }

    async testAll() {
        console.log('\n📱 Testing All WhatsApp Messages');
        console.log('='.repeat(50));
        
        await this.testSimple();
        await this.testComplex();
    }

    generateTestReport() {
        console.log('\n📋 WhatsApp Test Report');
        console.log('='.repeat(50));
        console.log(`📅 Date: ${new Date().toLocaleString()}`);
        console.log(`🔧 System: IQS Trade WhatsApp (Simple Tester)`);
        console.log(`📋 Valid BL Numbers: ${this.validBLs.length} (NYC220-NYC247)`);
        
        const simpleTests = this.getSimpleTests();
        const complexTests = this.getComplexTests();
        
        console.log(`\n📱 Test Cases:`);
        console.log(`   Simple: ${simpleTests.length}`);
        console.log(`   Complex: ${complexTests.length}`);
        console.log(`   Total: ${simpleTests.length + complexTests.length}`);
        
        console.log(`\n🎯 Test Categories:`);
        const categories = new Set();
        [...simpleTests, ...complexTests].forEach(test => {
            categories.add(test.category);
        });
        
        Array.from(categories).sort().forEach(category => {
            console.log(`   - ${category}`);
        });
    }
}

async function main() {
    console.log('🚀 Simple WhatsApp System Testing');
    console.log('='.repeat(50));
    
    const tester = new SimpleWhatsAppTester();
    
    try {
        console.log('\nChoose test type:');
        console.log('1. Simple tests only');
        console.log('2. Complex tests only');
        console.log('3. All tests (Simple + Complex)');
        console.log('4. Generate test report only');
        
        const choice = process.argv[2] || '3';
        
        switch (choice) {
            case '1':
                await tester.testSimple();
                break;
            case '2':
                await tester.testComplex();
                break;
            case '3':
                await tester.testAll();
                break;
            case '4':
                tester.generateTestReport();
                break;
            default:
                console.log('Invalid choice. Running all tests...');
                await tester.testAll();
        }
        
        console.log('\n🎉 WhatsApp testing completed!');
        console.log('\n📋 Next Steps:');
        console.log('1. Check the test results above');
        console.log('2. Verify BL number extraction');
        console.log('3. Check intent classification');
        console.log('4. Review response generation');
        
    } catch (error) {
        console.error('❌ Testing failed:', error);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = SimpleWhatsAppTester; 