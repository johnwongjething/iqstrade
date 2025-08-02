#!/usr/bin/env python3
"""
Minimal Email Ingestor for testing database locking system
"""

import os
import logging
from dotenv import load_dotenv
from db_utils import get_db_conn

# Load environment variables
load_dotenv('.env.local')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def acquire_db_processing_lock(user_id, timeout_seconds=30):
    """Acquire database-based processing lock"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Clean up stale locks (older than 10 minutes)
        cursor.execute("""
            DELETE FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '10 minutes'
        """)
        
        # Try to insert a new lock
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES (%s, NOW(), NOW() + INTERVAL '%s seconds')
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (user_id, timeout_seconds))
        
        result = cursor.fetchone()
        if result:
            conn.commit()
            logger.info(f"🔒 Database lock acquired by: {user_id}")
            return True
        else:
            # Check if there's an existing lock
            cursor.execute("""
                SELECT user_id, created_at FROM email_processing_locks 
                WHERE expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1
            """)
            existing = cursor.fetchone()
            if existing:
                logger.warning(f"⏰ Database lock already held by: {existing[0]} since {existing[1]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to acquire database lock: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def release_db_processing_lock(user_id):
    """Release database-based processing lock"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM email_processing_locks 
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        logger.info(f"🔓 Database lock released by: {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to release database lock: {e}")
    finally:
        cursor.close()
        conn.close()

def get_db_processing_status():
    """Get current database processing status"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT user_id, created_at, expires_at 
            FROM email_processing_locks 
            WHERE expires_at > NOW()
            ORDER BY created_at DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            user_id, created_at, expires_at = result
            return {
                'is_processing': True,
                'started_by': user_id,
                'started_at': created_at.isoformat() if created_at else None,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
        else:
            return {
                'is_processing': False,
                'started_by': None,
                'started_at': None,
                'expires_at': None
            }
    except Exception as e:
        logger.error(f"❌ Failed to get database processing status: {e}")
        return {
            'is_processing': False,
            'started_by': None,
            'started_at': None,
            'expires_at': None,
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

def process_inbox(user_id=None):
    """Minimal process_inbox function for testing"""
    logger.info(f"🔄 Starting email processing for user: {user_id}")
    
    # Try to acquire the database lock
    if not acquire_db_processing_lock(user_id or 'unknown_user'):
        logger.warning("⏰ Email processing already in progress by another user")
        return []
    
    try:
        # Simulate some processing time
        import time
        time.sleep(2)
        
        logger.info("✅ Email processing completed successfully")
        return [{"email_id": "test", "classification": "test"}]
        
    except Exception as e:
        logger.error(f"❌ Email processing failed: {e}")
        return []
    finally:
        # Always release the lock
        release_db_processing_lock(user_id or 'unknown_user')

def ingest_emails():
    """Alias for process_inbox to maintain compatibility"""
    return process_inbox() 