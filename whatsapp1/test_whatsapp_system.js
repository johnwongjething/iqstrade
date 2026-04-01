#!/usr/bin/env node
/**
 * WhatsApp System Testing Script
 * Tests the WhatsApp bot with various scenarios
 * Valid BL numbers: NYC220 to NYC247
 */

require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

class WhatsAppTester {
    constructor() {
        this.client = null;
        this.adminNumber = process.env.ADMIN_WA_ID || 'whatsapp:+85212345678';
        this.validBLs = [];
        
        // Generate valid BL numbers (NYC220 to NYC247)
        for (let i = 220; i <= 247; i++) {
            this.validBLs.push(`NYC${i}`);
        }
        
        console.log('🔧 WhatsApp Tester Initialized');
        console.log('='.repeat(50));
        console.log(`📱 Admin Number: ${this.adminNumber}`);
        console.log(`📋 Valid BLs: ${this.validBLs.length} (NYC220-NYC247)`);
        console.log('='.repeat(50));
    }

    async initialize() {
        return new Promise((resolve, reject) => {
            this.client = new Client({
                authStrategy: new LocalAuth(),
                puppeteer: {
                    headless: true,
                    args: ['--no-sandbox', '--disable-setuid-sandbox']
                }
            });

            this.client.on('qr', (qr) => {
                console.log('📱 QR Code received, scan it with WhatsApp:');
                qrcode.generate(qr, { small: true });
            });

            this.client.on('ready', () => {
                console.log('✅ WhatsApp client is ready!');
                resolve();
            });

            this.client.on('auth_failure', (msg) => {
                console.error('❌ Authentication failed:', msg);
                reject(new Error('Authentication failed'));
            });

            this.client.initialize().catch(reject);
        });
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

    async sendMessage(message) {
        try {
            await this.client.sendMessage(this.adminNumber, message);
            return true;
        } catch (error) {
            console.error('❌ Failed to send message:', error);
            return false;
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
            
            if (await this.sendMessage(test.message)) {
                console.log('   ✅ Sent successfully!');
                successful++;
            } else {
                console.log('   ❌ Failed to send');
                failed++;
            }
            
            // Wait between messages
            if (i < tests.length - 1) {
                console.log('   ⏳ Waiting 3 seconds...');
                await new Promise(resolve => setTimeout(resolve, 3000));
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
            
            if (await this.sendMessage(test.message)) {
                console.log('   ✅ Sent successfully!');
                successful++;
            } else {
                console.log('   ❌ Failed to send');
                failed++;
            }
            
            // Wait between messages
            if (i < tests.length - 1) {
                console.log('   ⏳ Waiting 3 seconds...');
                await new Promise(resolve => setTimeout(resolve, 3000));
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
        console.log(`🔧 System: IQS Trade WhatsApp`);
        console.log(`📱 Admin Number: ${this.adminNumber}`);
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

    async close() {
        if (this.client) {
            await this.client.destroy();
            console.log('📱 WhatsApp client closed');
        }
    }
}

async function main() {
    console.log('🚀 WhatsApp System Testing');
    console.log('='.repeat(50));
    
    const tester = new WhatsAppTester();
    
    try {
        console.log('\nChoose test type:');
        console.log('1. Simple tests only');
        console.log('2. Complex tests only');
        console.log('3. All tests (Simple + Complex)');
        console.log('4. Generate test report only');
        
        const choice = process.argv[2] || '3';
        
        await tester.initialize();
        
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
        console.log('1. Check WhatsApp for bot responses');
        console.log('2. Monitor the bot logs for processing');
        console.log('3. Check database for message records');
        
    } catch (error) {
        console.error('❌ Testing failed:', error);
    } finally {
        await tester.close();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = WhatsAppTester; 