#!/usr/bin/env python3
"""
Outlook Template Export
Export AI-generated replies as email templates for Outlook
"""

import os
import json
import csv
from datetime import datetime
from config import get_db_conn
import logging

logger = logging.getLogger(__name__)

class OutlookTemplateExporter:
    """
    Export AI-generated replies as Outlook email templates
    """
    
    def __init__(self):
        self.export_dir = "outlook_exports"
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_replies_as_templates(self, format_type='csv', date_from=None, date_to=None):
        """
        Export AI replies as email templates
        
        Args:
            format_type: 'csv', 'json', or 'outlook'
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        """
        
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT 
                    cer.id,
                    ce.sender,
                    ce.subject,
                    ce.body as original_email,
                    cer.body as ai_reply,
                    cer.confidence_score,
                    cer.created_at,
                    cer.auto_send_recommended
                FROM customer_email_replies cer
                JOIN customer_emails ce ON cer.customer_email_id = ce.id
                WHERE cer.confidence_score >= 0.7
            """
            
            params = []
            
            if date_from:
                query += " AND cer.created_at >= %s"
                params.append(f"{date_from} 00:00:00")
            
            if date_to:
                query += " AND cer.created_at <= %s"
                params.append(f"{date_to} 23:59:59")
            
            query += " ORDER BY cer.created_at DESC"
            
            cursor.execute(query, params)
            replies = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(replies)} high-confidence replies to export")
            
            if format_type == 'csv':
                return self._export_as_csv(replies)
            elif format_type == 'json':
                return self._export_as_json(replies)
            elif format_type == 'outlook':
                return self._export_as_outlook_templates(replies)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting templates: {e}")
            return None
    
    def _export_as_csv(self, replies):
        """Export as CSV file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/outlook_templates_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Template_ID',
                'Subject',
                'Reply_Text',
                'Original_Email',
                'Confidence_Score',
                'Created_Date',
                'Auto_Send_Recommended'
            ])
            
            # Write data
            for reply in replies:
                reply_id, sender, subject, original_email, ai_reply, confidence, created_at, auto_send = reply
                
                writer.writerow([
                    reply_id,
                    subject or "No Subject",
                    ai_reply or "",
                    original_email or "",
                    confidence or 0,
                    created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
                    "Yes" if auto_send else "No"
                ])
        
        logger.info(f"✅ Exported {len(replies)} templates to {filename}")
        return filename
    
    def _export_as_json(self, replies):
        """Export as JSON file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/outlook_templates_{timestamp}.json"
        
        templates = []
        for reply in replies:
            reply_id, sender, subject, original_email, ai_reply, confidence, created_at, auto_send = reply
            
            templates.append({
                'template_id': reply_id,
                'subject': subject or "No Subject",
                'reply_text': ai_reply or "",
                'original_email': original_email or "",
                'confidence_score': float(confidence) if confidence else 0,
                'created_date': created_at.isoformat() if created_at else "",
                'auto_send_recommended': bool(auto_send),
                'sender': sender
            })
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(templates, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exported {len(templates)} templates to {filename}")
        return filename
    
    def _export_as_outlook_templates(self, replies):
        """Export as Outlook-compatible template files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_dir = f"{self.export_dir}/outlook_templates_{timestamp}"
        os.makedirs(template_dir, exist_ok=True)
        
        exported_files = []
        
        for reply in replies:
            reply_id, sender, subject, original_email, ai_reply, confidence, created_at, auto_send = reply
            
            # Create template file
            template_filename = f"template_{reply_id}.txt"
            template_path = os.path.join(template_dir, template_filename)
            
            with open(template_path, 'w', encoding='utf-8') as template_file:
                template_file.write(f"Subject: {subject or 'No Subject'}\n")
                template_file.write(f"Confidence: {confidence or 0}\n")
                template_file.write(f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else ''}\n")
                template_file.write(f"Auto-Send: {'Yes' if auto_send else 'No'}\n")
                template_file.write("-" * 50 + "\n")
                template_file.write("REPLY TEXT:\n")
                template_file.write(ai_reply or "")
                template_file.write("\n\n")
                template_file.write("-" * 50 + "\n")
                template_file.write("ORIGINAL EMAIL:\n")
                template_file.write(original_email or "")
            
            exported_files.append(template_path)
        
        logger.info(f"✅ Exported {len(exported_files)} template files to {template_dir}")
        return template_dir
    
    def create_outlook_import_guide(self):
        """Create a guide for importing templates into Outlook"""
        
        guide_content = """
MICROSOFT OUTLOOK TEMPLATE IMPORT GUIDE
======================================

This guide explains how to import AI-generated email templates into Microsoft Outlook.

METHOD 1: MANUAL COPY-PASTE
---------------------------
1. Open the exported CSV/JSON file
2. Copy the reply text from the "Reply_Text" column
3. In Outlook, create a new email
4. Paste the reply text
5. Save as template: File > Save As > Outlook Template (*.oft)

METHOD 2: QUICK PARTS
---------------------
1. In Outlook, go to Insert > Quick Parts > Save Selection to Quick Part Gallery
2. Copy the AI reply text
3. Paste into the Quick Part dialog
4. Give it a name (e.g., "AI Reply - High Confidence")
5. Choose a category (e.g., "AI Templates")
6. Click OK

METHOD 3: SIGNATURES
--------------------
1. In Outlook, go to File > Options > Mail > Signatures
2. Create a new signature
3. Paste the AI reply text
4. Save the signature
5. Use Insert > Signature to add to emails

METHOD 4: AUTOCOMPLETE
----------------------
1. Create a new email in Outlook
2. Type a few words from the AI reply
3. Outlook will suggest the full text
4. Press Tab to accept the suggestion

RECOMMENDED WORKFLOW:
--------------------
1. Export high-confidence replies (confidence >= 0.8)
2. Review and edit the templates if needed
3. Save as Quick Parts for easy access
4. Use templates when responding to similar emails

TEMPLATE CATEGORIES:
-------------------
- Payment Confirmations
- Fee Inquiries
- CTN Requests
- Business Hours
- General Support

For questions or support, contact your system administrator.
"""
        
        guide_file = f"{self.export_dir}/OUTLOOK_IMPORT_GUIDE.txt"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        logger.info(f"✅ Created import guide: {guide_file}")
        return guide_file

def main():
    """Main function for template export"""
    
    print("🔧 Outlook Template Export")
    print("=" * 40)
    
    exporter = OutlookTemplateExporter()
    
    # Export templates
    print("📤 Exporting AI replies as Outlook templates...")
    
    # Export as CSV (most compatible)
    csv_file = exporter.export_replies_as_templates(format_type='csv')
    if csv_file:
        print(f"✅ CSV export: {csv_file}")
    
    # Export as JSON (structured data)
    json_file = exporter.export_replies_as_templates(format_type='json')
    if json_file:
        print(f"✅ JSON export: {json_file}")
    
    # Export as Outlook templates
    template_dir = exporter.export_replies_as_templates(format_type='outlook')
    if template_dir:
        print(f"✅ Template files: {template_dir}")
    
    # Create import guide
    guide_file = exporter.create_outlook_import_guide()
    print(f"✅ Import guide: {guide_file}")
    
    print("\n🎉 Export complete!")
    print("📁 Check the 'outlook_exports' folder for your files")

if __name__ == "__main__":
    main() 