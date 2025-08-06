#!/usr/bin/env python3
"""
Test Script for Duplicate Payment Protection
Tests all payment streams to ensure duplicate payments are detected and notifications are sent
"""

import requests
import json
import logging
from datetime import datetime
import pytz
from config import get_db_conn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webhook_duplicate_protection():
    """Test Allinpay webhook duplicate payment protection"""
    logger.info("🧪 Testing Allinpay webhook duplicate payment protection...")
    
    # Test data
    test_data = {
        "transaction_id": "ABC123456",  # Use a test unique number
        "amount": 200.00,
        "currency": "USD",
        "status": "completed",
        "customer_email": "test@example.com",
        "payment_phase": "initial"
    }
    
    try:
        # First payment (should succeed)
        response1 = requests.post(
            "http://localhost:5000/payment",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"First payment response: {response1.status_code}")
        
        # Second payment (should be detected as duplicate)
        response2 = requests.post(
            "http://localhost:5000/payment",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"Second payment response: {response2.status_code}")
        
        if response2.status_code == 409:
            logger.info("✅ Webhook duplicate protection working correctly")
            return True
        else:
            logger.error("❌ Webhook duplicate protection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook test failed: {e}")
        return False

def test_email_duplicate_protection():
    """Test email payment duplicate protection"""
    logger.info("🧪 Testing email payment duplicate protection...")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Create a test email record
        test_email_data = {
            "from_addr": "test@example.com",
            "subject": "Payment Receipt Test",
            "body_text": "Payment of $200 for BL TEST123",
            "bl_payment_map": {"TEST123": 200.00}
        }
        
        # Insert test email
        cur.execute("""
            INSERT INTO customer_emails (from_addr, subject, body_text, processed_for_payments)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
        """, (test_email_data["from_addr"], test_email_data["subject"], test_email_data["body_text"]))
        
        email_id = cur.fetchone()[0]
        conn.commit()
        
        # Process email first time (should succeed)
        from email_ingestor_working import process_payment_receipt_email
        result1 = process_payment_receipt_email(
            email_id=email_id,
            from_addr=test_email_data["from_addr"],
            subject=test_email_data["subject"],
            body_text=test_email_data["body_text"],
            attachments=[],
            bl_payment_map=test_email_data["bl_payment_map"],
            conn=conn
        )
        logger.info(f"First email processing result: {result1}")
        
        # Process email second time (should detect duplicate)
        result2 = process_payment_receipt_email(
            email_id=email_id,
            from_addr=test_email_data["from_addr"],
            subject=test_email_data["subject"],
            body_text=test_email_data["body_text"],
            attachments=[],
            bl_payment_map=test_email_data["bl_payment_map"],
            conn=conn
        )
        logger.info(f"Second email processing result: {result2}")
        
        # Check if duplicate was detected
        cur.execute("""
            SELECT COUNT(*) FROM customer_balance_transactions 
            WHERE payment_source = 'email' AND bl_id IN (
                SELECT id FROM bill_of_lading WHERE bl_number = 'TEST123'
            )
        """)
        transaction_count = cur.fetchone()[0]
        
        if transaction_count == 1:
            logger.info("✅ Email duplicate protection working correctly")
            return True
        else:
            logger.error(f"❌ Email duplicate protection failed - found {transaction_count} transactions")
            return False
            
    except Exception as e:
        logger.error(f"❌ Email test failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_bank_import_duplicate_protection():
    """Test bank import duplicate protection"""
    logger.info("🧪 Testing bank import duplicate protection...")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Test bank statement data
        test_bank_data = {
            "date": "2025-01-27",
            "description": "Payment for BL TEST456",
            "amount": 300.00
        }
        
        # First import (should succeed)
        from bank_routes import import_bank_statement
        result1 = import_bank_statement(test_bank_data)
        logger.info(f"First bank import result: {result1}")
        
        # Second import (should detect duplicate)
        result2 = import_bank_statement(test_bank_data)
        logger.info(f"Second bank import result: {result2}")
        
        # Check if duplicate was detected
        cur.execute("""
            SELECT COUNT(*) FROM customer_balance_transactions 
            WHERE payment_source = 'bank_import' AND bl_id IN (
                SELECT id FROM bill_of_lading WHERE bl_number = 'TEST456'
            )
        """)
        transaction_count = cur.fetchone()[0]
        
        if transaction_count == 1:
            logger.info("✅ Bank import duplicate protection working correctly")
            return True
        else:
            logger.error(f"❌ Bank import duplicate protection failed - found {transaction_count} transactions")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bank import test failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_whatsapp_duplicate_protection():
    """Test WhatsApp duplicate protection"""
    logger.info("🧪 Testing WhatsApp duplicate protection...")
    
    # This would test the Node.js chatHandler.js
    # For now, we'll test the database functions directly
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Test WhatsApp payment data
        test_whatsapp_data = {
            "bl_number": "TEST789",
            "amount": 250.00,
            "customer_username": "testuser"
        }
        
        # Get BL ID
        cur.execute("SELECT id FROM bill_of_lading WHERE bl_number = %s", (test_whatsapp_data["bl_number"],))
        bl_result = cur.fetchone()
        
        if not bl_result:
            logger.error("❌ Test BL not found in database")
            return False
            
        bl_id = bl_result[0]
        
        # Check if payment already processed
        from utils.balance_utils import check_payment_processed
        is_duplicate = check_payment_processed(bl_id, 'whatsapp')
        
        if is_duplicate:
            logger.info("✅ WhatsApp duplicate detection working correctly")
            return True
        else:
            # Mark as processed for testing
            from utils.balance_utils import mark_payment_processed
            mark_payment_processed(bl_id, 'whatsapp', 'test_script')
            
            # Check again
            is_duplicate_after = check_payment_processed(bl_id, 'whatsapp')
            if is_duplicate_after:
                logger.info("✅ WhatsApp duplicate protection working correctly")
                return True
            else:
                logger.error("❌ WhatsApp duplicate protection failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ WhatsApp test failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_notification_system():
    """Test duplicate payment notification system"""
    logger.info("🧪 Testing duplicate payment notification system...")
    
    try:
        from utils.duplicate_payment_notifications import send_duplicate_payment_notifications
        
        # Test notification data
        test_notification_data = {
            "bl_id": 1,
            "bl_number": "TEST999",
            "customer_username": "testuser",
            "customer_email": "test@example.com",
            "payment_amount": 150.00,
            "payment_source": "test",
            "original_payment_date": datetime.now(pytz.timezone('Asia/Hong_Kong'))
        }
        
        # Send test notification
        send_duplicate_payment_notifications(**test_notification_data)
        logger.info("✅ Duplicate payment notification system working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Notification test failed: {e}")
        return False

def test_database_schema():
    """Test database schema for duplicate payment protection"""
    logger.info("🧪 Testing database schema...")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check if required tables exist
        required_tables = [
            'customer_balances',
            'customer_balance_transactions',
            'bill_of_lading'
        ]
        
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table,))
            
            exists = cur.fetchone()[0]
            if not exists:
                logger.error(f"❌ Required table {table} does not exist")
                return False
                
        # Check if balance_applied column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bill_of_lading' 
            AND column_name = 'balance_applied'
        """)
        
        balance_applied_exists = cur.fetchone() is not None
        if not balance_applied_exists:
            logger.error("❌ balance_applied column does not exist in bill_of_lading table")
            return False
            
        logger.info("✅ Database schema is correct")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema test failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def run_all_tests():
    """Run all duplicate payment protection tests"""
    logger.info("🚀 Starting comprehensive duplicate payment protection tests...")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Notification System", test_notification_system),
        ("Webhook Protection", test_webhook_duplicate_protection),
        ("Email Protection", test_email_duplicate_protection),
        ("Bank Import Protection", test_bank_import_duplicate_protection),
        ("WhatsApp Protection", test_whatsapp_duplicate_protection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Duplicate payment protection is working correctly.")
    else:
        logger.error("⚠️ Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests() 