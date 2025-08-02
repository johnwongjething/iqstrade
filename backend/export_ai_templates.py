#!/usr/bin/env python3
"""
Export AI Templates for Outlook
Simple export of AI-generated replies as email templates
"""

import os
import json
from datetime import datetime, timedelta
from config import get_db_conn

def export_ai_templates():
    """Export AI-generated replies as Outlook templates"""
    
    print("📤 Exporting AI Templates for Outlook")
    print("=" * 50)
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get high-confidence replies from the last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        
        cursor.execute("""
            SELECT 
                cer.id,
                ce.sender,
                ce.subject,
                cer.body as ai_reply,
                cer.confidence_score,
                cer.created_at,
                cer.auto_send_recommended
            FROM customer_email_replies cer
            JOIN customer_emails ce ON cer.customer_email_id = ce.id
            WHERE cer.confidence_score >= 0.7
                AND cer.created_at >= %s
            ORDER BY cer.confidence_score DESC, cer.created_at DESC
        """, (week_ago,))
        
        replies = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"📊 Found {len(replies)} high-confidence replies")
        
        if not replies:
            print("❌ No high-confidence replies found")
            return
        
        # Create export directory
        export_dir = "outlook_templates"
        os.makedirs(export_dir, exist_ok=True)
        
        # Export as individual template files
        template_files = []
        
        for reply in replies:
            reply_id, sender, subject, ai_reply, confidence, created_at, auto_send = reply
            
            # Create template filename
            safe_subject = (subject or "No Subject").replace("/", "_").replace("\\", "_")[:30]
            filename = f"template_{reply_id}_{safe_subject}.txt"
            filepath = os.path.join(export_dir, filename)
            
            # Write template content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"AI TEMPLATE #{reply_id}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Subject: {subject or 'No Subject'}\n")
                f.write(f"Confidence: {confidence:.2f}\n")
                f.write(f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Auto-Send Recommended: {'Yes' if auto_send else 'No'}\n")
                f.write(f"Original Sender: {sender}\n")
                f.write("-" * 50 + "\n")
                f.write("REPLY TEXT:\n")
                f.write("-" * 50 + "\n")
                f.write(ai_reply or "")
                f.write("\n\n")
                f.write("=" * 50 + "\n")
                f.write("INSTRUCTIONS:\n")
                f.write("1. Copy the reply text above\n")
                f.write("2. Paste into Outlook email\n")
                f.write("3. Review and edit as needed\n")
                f.write("4. Send to customer\n")
            
            template_files.append(filepath)
        
        # Create summary file
        summary_file = os.path.join(export_dir, "TEMPLATE_SUMMARY.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("AI TEMPLATE SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Templates: {len(template_files)}\n\n")
            
            for reply in replies:
                reply_id, sender, subject, ai_reply, confidence, created_at, auto_send = reply
                f.write(f"Template #{reply_id}:\n")
                f.write(f"  Subject: {subject or 'No Subject'}\n")
                f.write(f"  Confidence: {confidence:.2f}\n")
                f.write(f"  Auto-Send: {'Yes' if auto_send else 'No'}\n")
                f.write(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"  File: template_{reply_id}_{(subject or 'No Subject')[:30]}.txt\n\n")
        
        # Create Outlook import guide
        guide_file = os.path.join(export_dir, "OUTLOOK_IMPORT_GUIDE.txt")
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write("OUTLOOK TEMPLATE IMPORT GUIDE\n")
            f.write("=" * 50 + "\n\n")
            f.write("METHOD 1: QUICK PARTS (Recommended)\n")
            f.write("-" * 30 + "\n")
            f.write("1. Open any template file (.txt)\n")
            f.write("2. Copy the reply text (between the dashed lines)\n")
            f.write("3. In Outlook, go to Insert > Quick Parts > Save Selection to Quick Part Gallery\n")
            f.write("4. Paste the text and give it a name\n")
            f.write("5. Choose category 'AI Templates'\n")
            f.write("6. Click OK\n\n")
            f.write("METHOD 2: MANUAL COPY-PASTE\n")
            f.write("-" * 30 + "\n")
            f.write("1. Open template file\n")
            f.write("2. Copy reply text\n")
            f.write("3. Paste into Outlook email\n")
            f.write("4. Review and edit\n")
            f.write("5. Send\n\n")
            f.write("METHOD 3: SIGNATURES\n")
            f.write("-" * 30 + "\n")
            f.write("1. Go to File > Options > Mail > Signatures\n")
            f.write("2. Create new signature\n")
            f.write("3. Paste AI reply text\n")
            f.write("4. Save and use as needed\n\n")
            f.write("IMPORTANT NOTES:\n")
            f.write("- Always review AI replies before sending\n")
            f.write("- Edit for tone, accuracy, and completeness\n")
            f.write("- Check customer-specific details\n")
            f.write("- Verify amounts and payment information\n")
        
        print(f"✅ Exported {len(template_files)} templates to '{export_dir}' folder")
        print(f"📁 Summary: {summary_file}")
        print(f"📖 Guide: {guide_file}")
        print("\n🎯 Next Steps:")
        print("1. Open the 'outlook_templates' folder")
        print("2. Review the templates")
        print("3. Import into Outlook using the guide")
        print("4. Use templates when responding to customers")
        
        return export_dir
        
    except Exception as e:
        print(f"❌ Error exporting templates: {e}")
        return None

if __name__ == "__main__":
    export_ai_templates() 