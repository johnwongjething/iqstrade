#!/usr/bin/env python3
"""
Email Ingestion Results Analyzer
Comprehensive analysis of email processing results
"""
import os
import sys
import json
from datetime import datetime, timedelta
from config import get_db_conn

def analyze_recent_email_processing():
    """Analyze recent email processing results"""
    print("📊 Email Ingestion Results Analysis")
    print("=" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get recent emails with full details
        cursor.execute("""
            SELECT 
                ce.id,
                ce.sender,
                ce.subject,
                ce.body,
                ce.created_at,
                ce.message_id,
                ce.attachments,
                ce.processed_for_payments,
                LENGTH(ce.body) as body_length,
                COUNT(cer.id) as reply_count
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            WHERE ce.created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY ce.id, ce.sender, ce.subject, ce.body, ce.created_at, ce.message_id, ce.attachments, ce.processed_for_payments
            ORDER BY ce.created_at DESC
            LIMIT 20
        """)
        
        recent_emails = cursor.fetchall()
        print(f"📧 Analyzing {len(recent_emails)} recent emails...")
        print("-" * 80)
        
        total_emails = len(recent_emails)
        emails_with_attachments = 0
        emails_with_replies = 0
        emails_processed_for_payments = 0
        total_attachments = 0
        total_replies = 0
        
        for email in recent_emails:
            eid, sender, subject, body, created_at, message_id, attachments, processed, body_length, reply_count = email
            
            has_attachments = attachments is not None and attachments != '[]' and attachments != 'null'
            has_replies = reply_count > 0
            has_body = body and body_length > 0
            
            if has_attachments:
                emails_with_attachments += 1
                # Count attachments
                try:
                    if isinstance(attachments, str):
                        att_list = json.loads(attachments)
                    else:
                        att_list = attachments
                    total_attachments += len(att_list) if isinstance(att_list, list) else 1
                except:
                    total_attachments += 1
            
            if has_replies:
                emails_with_replies += 1
                total_replies += reply_count
            
            if processed:
                emails_processed_for_payments += 1
            
            # Display email details
            print(f"📧 Email ID {eid}: {subject[:50]:<50}")
            print(f"    From: {sender}")
            print(f"    Created: {created_at}")
            print(f"    Status: {'✅ Processed' if processed else '⏳ Pending'}")
            print(f"    Attachments: {'✅ ' + str(total_attachments) if has_attachments else '❌ None'}")
            print(f"    AI Replies: {'✅ ' + str(reply_count) if has_replies else '❌ None'}")
            print(f"    Body: {'✅ ' + str(body_length) + ' chars' if has_body else '❌ Empty'}")
            if has_attachments:
                try:
                    if isinstance(attachments, str):
                        att_list = json.loads(attachments)
                    else:
                        att_list = attachments
                    print(f"    Attachment URLs: {att_list}")
                except:
                    print(f"    Attachment Data: {attachments}")
            print()
        
        # Summary statistics
        print("=" * 80)
        print("📊 Processing Summary (Last 24 hours):")
        print(f"  Total Emails: {total_emails}")
        print(f"  With Attachments: {emails_with_attachments} ({emails_with_attachments/total_emails*100:.1f}%)")
        print(f"  With AI Replies: {emails_with_replies} ({emails_with_replies/total_emails*100:.1f}%)")
        print(f"  Processed for Payments: {emails_processed_for_payments} ({emails_processed_for_payments/total_emails*100:.1f}%)")
        print(f"  Total Attachments: {total_attachments}")
        print(f"  Total AI Replies: {total_replies}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def analyze_ai_replies():
    """Analyze AI-generated replies"""
    print(f"\n🤖 AI Reply Analysis:")
    print("-" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get recent AI replies
        cursor.execute("""
            SELECT 
                cer.id,
                cer.customer_email_id,
                cer.body,
                cer.created_at,
                cer.confidence_score,
                ce.sender,
                ce.subject
            FROM customer_email_replies cer
            JOIN customer_emails ce ON cer.customer_email_id = ce.id
            WHERE cer.created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY cer.created_at DESC
            LIMIT 10
        """)
        
        replies = cursor.fetchall()
        print(f"📝 Found {len(replies)} AI replies:")
        
        for reply in replies:
            rid, email_id, body, created_at, confidence, sender, subject = reply
            
            print(f"\n  Reply ID {rid} (Email {email_id}):")
            print(f"    To: {sender}")
            print(f"    Subject: {subject}")
            print(f"    Confidence: {confidence:.2f}" if confidence else "    Confidence: N/A")
            print(f"    Created: {created_at}")
            print(f"    Preview: {body[:100]}{'...' if len(body) > 100 else ''}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ AI reply analysis failed: {e}")

def analyze_cloudinary_uploads():
    """Analyze Cloudinary uploads"""
    print(f"\n☁️ Cloudinary Upload Analysis:")
    print("-" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get emails with attachments and analyze Cloudinary URLs
        cursor.execute("""
            SELECT id, sender, subject, attachments, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL 
            AND attachments != '[]' 
            AND attachments != 'null'
            AND created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
        """)
        
        emails_with_attachments = cursor.fetchall()
        
        email_attachments = 0
        receipt_attachments = 0
        invoice_attachments = 0
        other_attachments = 0
        
        print(f"📎 Found {len(emails_with_attachments)} emails with attachments:")
        
        for email in emails_with_attachments:
            eid, sender, subject, attachments, created_at = email
            
            try:
                if isinstance(attachments, str):
                    att_list = json.loads(attachments)
                else:
                    att_list = attachments
                
                if isinstance(att_list, list):
                    for url in att_list:
                        if 'email_attachments' in url:
                            email_attachments += 1
                        elif 'receipts' in url:
                            receipt_attachments += 1
                        elif 'invoices' in url:
                            invoice_attachments += 1
                        else:
                            other_attachments += 1
                    
                    print(f"\n  Email {eid}: {subject}")
                    print(f"    Sender: {sender}")
                    print(f"    Attachments: {len(att_list)}")
                    for url in att_list:
                        folder = "Unknown"
                        if 'email_attachments' in url:
                            folder = "Email Attachments"
                        elif 'receipts' in url:
                            folder = "Receipts"
                        elif 'invoices' in url:
                            folder = "Invoices"
                        print(f"      {folder}: {url}")
                
            except Exception as e:
                print(f"    Error parsing attachments: {e}")
        
        print(f"\n📊 Upload Summary:")
        print(f"  Email Attachments: {email_attachments}")
        print(f"  Receipt Uploads: {receipt_attachments}")
        print(f"  Invoice Uploads: {invoice_attachments}")
        print(f"  Other Uploads: {other_attachments}")
        print(f"  Total Uploads: {email_attachments + receipt_attachments + invoice_attachments + other_attachments}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Cloudinary analysis failed: {e}")

def analyze_payment_processing():
    """Analyze payment processing results"""
    print(f"\n💰 Payment Processing Analysis:")
    print("-" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get payment-related emails
        cursor.execute("""
            SELECT 
                ce.id,
                ce.sender,
                ce.subject,
                ce.created_at,
                ce.processed_for_payments,
                COUNT(cer.id) as reply_count
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            WHERE ce.created_at >= NOW() - INTERVAL '24 hours'
            AND (ce.subject ILIKE '%payment%' OR ce.subject ILIKE '%receipt%' OR ce.subject ILIKE '%invoice%')
            GROUP BY ce.id, ce.sender, ce.subject, ce.created_at, ce.processed_for_payments
            ORDER BY ce.created_at DESC
        """)
        
        payment_emails = cursor.fetchall()
        print(f"💰 Found {len(payment_emails)} payment-related emails:")
        
        processed_count = 0
        pending_count = 0
        
        for email in payment_emails:
            eid, sender, subject, created_at, processed, reply_count = email
            
            status = "✅ Processed" if processed else "⏳ Pending"
            if processed:
                processed_count += 1
            else:
                pending_count += 1
            
            print(f"  Email {eid}: {subject}")
            print(f"    From: {sender}")
            print(f"    Status: {status}")
            print(f"    AI Replies: {reply_count}")
            print(f"    Created: {created_at}")
            print()
        
        print(f"📊 Payment Processing Summary:")
        print(f"  Processed: {processed_count}")
        print(f"  Pending: {pending_count}")
        print(f"  Success Rate: {processed_count/(processed_count+pending_count)*100:.1f}%" if (processed_count+pending_count) > 0 else "  Success Rate: N/A")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Payment analysis failed: {e}")

def analyze_database_updates():
    """Analyze database update patterns"""
    print(f"\n🗄️ Database Update Analysis:")
    print("-" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Check bill_of_lading updates
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bills,
                COUNT(CASE WHEN receipt_url IS NOT NULL THEN 1 END) as bills_with_receipts,
                COUNT(CASE WHEN paid_amount > 0 THEN 1 END) as bills_paid,
                COUNT(CASE WHEN status = 'Awaiting Bank In' THEN 1 END) as awaiting_bank,
                COUNT(CASE WHEN status = 'Paid and CTN Valid' THEN 1 END) as paid_status
            FROM bill_of_lading
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        
        bill_stats = cursor.fetchone()
        if bill_stats:
            total_bills, bills_with_receipts, bills_paid, awaiting_bank, paid_status = bill_stats
            print(f"📋 Bill of Lading Updates (Last 24 hours):")
            print(f"  Total Bills: {total_bills}")
            print(f"  With Receipts: {bills_with_receipts}")
            print(f"  Paid Amount > 0: {bills_paid}")
            print(f"  Awaiting Bank: {awaiting_bank}")
            print(f"  Paid Status: {paid_status}")
        
        # Check recent bill updates
        cursor.execute("""
            SELECT 
                id,
                bl_number,
                paid_amount,
                status,
                receipt_url,
                updated_at
            FROM bill_of_lading
            WHERE updated_at >= NOW() - INTERVAL '24 hours'
            ORDER BY updated_at DESC
            LIMIT 5
        """)
        
        recent_updates = cursor.fetchall()
        if recent_updates:
            print(f"\n🔄 Recent Bill Updates:")
            for update in recent_updates:
                bid, bl_number, paid_amount, status, receipt_url, updated_at = update
                print(f"  BL {bl_number}: ${paid_amount} - {status}")
                print(f"    Receipt: {'✅' if receipt_url else '❌'}")
                print(f"    Updated: {updated_at}")
                print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")

def generate_report():
    """Generate a comprehensive report"""
    print(f"\n📋 Generating Comprehensive Report...")
    print("=" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_emails,
                COUNT(CASE WHEN attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null' THEN 1 END) as emails_with_attachments,
                COUNT(CASE WHEN processed_for_payments = TRUE THEN 1 END) as processed_emails,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h
            FROM customer_emails
        """)
        
        stats = cursor.fetchone()
        if stats:
            total_emails, emails_with_attachments, processed_emails, last_hour, last_24h = stats
            
            print(f"🎯 Overall System Performance:")
            print(f"  Total Emails (All Time): {total_emails}")
            print(f"  Emails with Attachments: {emails_with_attachments} ({emails_with_attachments/total_emails*100:.1f}%)")
            print(f"  Processed for Payments: {processed_emails} ({processed_emails/total_emails*100:.1f}%)")
            print(f"  Last Hour: {last_hour}")
            print(f"  Last 24 Hours: {last_24h}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")

def main():
    """Main function"""
    print("🚀 Email Ingestion Results Analyzer")
    print("=" * 80)
    
    if not analyze_recent_email_processing():
        return
    
    analyze_ai_replies()
    analyze_cloudinary_uploads()
    analyze_payment_processing()
    analyze_database_updates()
    generate_report()
    
    print(f"\n✅ Analysis Complete!")
    print(f"This report shows:")
    print(f"  📧 Email processing results")
    print(f"  🤖 AI reply generation")
    print(f"  ☁️ Cloudinary uploads")
    print(f"  💰 Payment processing")
    print(f"  🗄️ Database updates")

if __name__ == "__main__":
    main() 