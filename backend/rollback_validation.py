#!/usr/bin/env python3
"""
Rollback Script for Email Validation System
Restore original files if needed
"""

import os
import shutil

def rollback_validation():
    """Rollback to original files"""
    
    print("🔄 ROLLING BACK EMAIL VALIDATION SYSTEM")
    print("=" * 40)
    
    backups = {
        "utils/ingest_emails.py": "utils/ingest_emails.py.backup_20250728_111506",
        "email_ingestor.py": "email_ingestor.py.backup_20250728_111506",
        "email_scheduler.py": "email_scheduler.py.backup_20250728_111506"
    }
    
    for original, backup in backups.items():
        if backup != "NOT_FOUND" and os.path.exists(backup):
            try:
                shutil.copy2(backup, original)
                print(f"✅ Restored: {original}")
            except Exception as e:
                print(f"❌ Error restoring {original}: {e}")
        else:
            print(f"⚠️ Backup not found for: {original}")
    
    print("\n🔄 Rollback completed!")

if __name__ == "__main__":
    rollback_validation()
