/**
 * Test script for WhatsApp balance processing
 * Run this to verify that the balance system is working
 */

const {
  markPaymentProcessed,
  processPaymentBalance,
  checkPaymentProcessed,
  getCustomerBalance,
  pool
} = require('./utils/balance_utils_node');

async function testBalanceProcessing() {
  console.log('🧪 Testing WhatsApp Balance Processing...');
  try {
    console.log('\n1. Testing database connection...');
    const result = await pool.query('SELECT NOW() as current_time');
    console.log('✅ Database connection successful:', result.rows[0].current_time);

    console.log('\n2. Checking if admin user exists...');
    const adminResult = await pool.query('SELECT username FROM users WHERE username = $1', ['admin']);
    if (adminResult.rows.length > 0) {
      console.log('✅ Admin user exists');
    } else {
      console.log('❌ Admin user not found');
      return;
    }

    console.log('\n3. Checking customer_balances table...');
    const balanceResult = await pool.query('SELECT COUNT(*) FROM customer_balances');
    console.log(`✅ Customer balances table has ${balanceResult.rows[0].count} records`);

    console.log('\n4. Checking customer_balance_transactions table...');
    const transactionResult = await pool.query('SELECT COUNT(*) FROM customer_balance_transactions');
    console.log(`✅ Customer balance transactions table has ${transactionResult.rows[0].count} records`);

    console.log('\n5. Checking bill_of_lading table...');
    const blResult = await pool.query('SELECT COUNT(*) FROM bill_of_lading WHERE customer_username IS NOT NULL');
    console.log(`✅ Bill of lading table has ${blResult.rows[0].count} records with customer_username`);

    console.log('\n6. Testing markPaymentProcessed function...');
    await markPaymentProcessed(999999, 'test', 'test_script');
    console.log('✅ markPaymentProcessed function executed without error');

    console.log('\n7. Testing processPaymentBalance function...');
    const adjustment = await processPaymentBalance('admin', 20, 0, 999999, 'test', 'test_script');
    console.log(`✅ processPaymentBalance function executed, adjustment: ${adjustment}`);

    console.log('\n8. Testing duplicate payment detection...');
    console.log('   - Checking if BL 999999 is marked as processed...');
    const isProcessed = await checkPaymentProcessed(999999, 'test');
    console.log(`   - Result: ${isProcessed} (should be true)`);
    
    if (isProcessed) {
      console.log('✅ Duplicate payment detection is working correctly');
    } else {
      console.log('❌ Duplicate payment detection is NOT working');
    }

    console.log('\n9. Testing with a new BL number...');
    const isNewProcessed = await checkPaymentProcessed(888888, 'test');
    console.log(`   - Result for new BL 888888: ${isNewProcessed} (should be false)`);
    
    if (!isNewProcessed) {
      console.log('✅ New payment detection is working correctly');
    } else {
      console.log('❌ New payment detection is NOT working');
    }

    console.log('\n🎉 Balance processing test completed!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    process.exit(0);
  }
}

testBalanceProcessing(); 