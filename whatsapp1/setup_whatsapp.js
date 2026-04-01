#!/usr/bin/env node
/**
 * WhatsApp Setup Script
 * Helps install dependencies and configure the testing environment
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔧 WhatsApp Setup Script');
console.log('='.repeat(50));

// Check if package.json exists
if (!fs.existsSync('package.json')) {
    console.log('❌ package.json not found. Please run this script from the WhatsApp directory.');
    process.exit(1);
}

// Check if node_modules exists
if (!fs.existsSync('node_modules')) {
    console.log('📦 Installing dependencies...');
    try {
        execSync('npm install', { stdio: 'inherit' });
        console.log('✅ Dependencies installed successfully!');
    } catch (error) {
        console.error('❌ Failed to install dependencies:', error.message);
        process.exit(1);
    }
} else {
    console.log('✅ Dependencies already installed');
}

// Check if .env file exists
if (!fs.existsSync('.env')) {
    console.log('📝 Creating .env file from template...');
    
    const envTemplate = `# WhatsApp Bot Configuration
OPENAI_API_KEY=your_openai_api_key_here
RAILWAY_DB_HOST=your_db_host_here
RAILWAY_DB_USER=your_db_user_here
RAILWAY_DB_PASSWORD=your_db_password_here
RAILWAY_DB_NAME=your_db_name_here
RAILWAY_DB_PORT=5432
ADMIN_WA_ID=whatsapp:+your_phone_number_here

# Optional: Frontend URL for verification
FRONTEND_URL=https://iqstrade.onrender.com

# Optional: Test environment
TEST_ENV=true
`;
    
    fs.writeFileSync('.env', envTemplate);
    console.log('✅ .env file created. Please update it with your actual values.');
} else {
    console.log('✅ .env file already exists');
}

// Check required environment variables
console.log('\n🔍 Checking environment variables...');
require('dotenv').config();

const requiredVars = [
    'OPENAI_API_KEY',
    'RAILWAY_DB_HOST',
    'RAILWAY_DB_USER',
    'RAILWAY_DB_PASSWORD',
    'RAILWAY_DB_NAME',
    'ADMIN_WA_ID'
];

let missingVars = [];
requiredVars.forEach(varName => {
    if (!process.env[varName] || process.env[varName] === `your_${varName.toLowerCase()}_here`) {
        missingVars.push(varName);
    }
});

if (missingVars.length > 0) {
    console.log('⚠️  Missing or default environment variables:');
    missingVars.forEach(varName => {
        console.log(`   - ${varName}`);
    });
    console.log('\n📝 Please update your .env file with the actual values.');
} else {
    console.log('✅ All required environment variables are set');
}

// Test database connection
console.log('\n🔍 Testing database connection...');
try {
    const { Pool } = require('pg');
    const pool = new Pool({
        host: process.env.RAILWAY_DB_HOST,
        user: process.env.RAILWAY_DB_USER,
        password: process.env.RAILWAY_DB_PASSWORD,
        database: process.env.RAILWAY_DB_NAME,
        port: process.env.RAILWAY_DB_PORT || 5432,
        ssl: { rejectUnauthorized: false }
    });
    
    const result = await pool.query('SELECT NOW()');
    console.log('✅ Database connection successful');
    console.log(`   Server time: ${result.rows[0].now}`);
    await pool.end();
} catch (error) {
    console.log('❌ Database connection failed:', error.message);
    console.log('   Please check your database credentials in .env');
}

// Test OpenAI connection
console.log('\n🔍 Testing OpenAI connection...');
try {
    const OpenAI = require('openai');
    const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY
    });
    
    const response = await openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 10
    });
    
    console.log('✅ OpenAI connection successful');
    console.log(`   Model: ${response.model}`);
} catch (error) {
    console.log('❌ OpenAI connection failed:', error.message);
    console.log('   Please check your OpenAI API key in .env');
}

console.log('\n🎉 Setup completed!');
console.log('\n📋 Next Steps:');
console.log('1. Update .env file with your actual values');
console.log('2. Run simple tests: node test_whatsapp_simple.js');
console.log('3. Run full tests: node test_whatsapp_system.js');
console.log('4. Start the bot: node index.js');

console.log('\n📚 Available Test Scripts:');
console.log('   - test_whatsapp_simple.js (recommended for testing)');
console.log('   - test_whatsapp_system.js (full WhatsApp Web testing)');
console.log('   - test.js (basic functionality test)'); 