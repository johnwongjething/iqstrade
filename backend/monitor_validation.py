#!/usr/bin/env python3
"""
Email Validation Monitoring Script
Monitor validation system performance
"""

import os
import sys
from datetime import datetime, timedelta
from config import get_db_conn

def monitor_validation_performance():
    """Monitor validation system performance"""
    
    print("📊 EMAIL VALIDATION MONITORING")
    print("=" * 40)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get recent emails (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        cursor.execute("""
            SELECT 
                ce.id,
                ce.subject,
                ce.created_at,
                cer.confidence_score,
                cer.body as reply_text
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            WHERE ce.created_at >= %s
            ORDER BY ce.created_at DESC
        """, (cutoff_time,))
        
        emails = cursor.fetchall()
        
        print(f"📧 Total emails in last 24 hours: {len(emails)}")
        
        # Analyze validation patterns
        high_confidence = 0
        low_confidence = 0
        no_reply = 0
        
        for email in emails:
            if email[4]:  # Has reply
                if email[3] and email[3] >= 0.9:
                    high_confidence += 1
                else:
                    low_confidence += 1
            else:
                no_reply += 1
        
        print(f"✅ High confidence replies (≥0.9): {high_confidence}")
        print(f"⚠️ Low confidence replies (<0.9): {low_confidence}")
        print(f"❌ No replies: {no_reply}")
        
        if len(emails) > 0:
            success_rate = (high_confidence / len(emails)) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Check for validation keywords in logs
        print("\n🔍 Check logs for validation messages:")
        print("   - 'Validation failed'")
        print("   - 'Enhanced processing'")
        print("   - 'Validation issues'")
        
    except Exception as e:
        print(f"❌ Error monitoring: {e}")

if __name__ == "__main__":
    monitor_validation_performance()
