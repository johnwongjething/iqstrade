#!/usr/bin/env python3
"""
JSON Corruption Detector
Detect common issues that cause JSON corruption
"""
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env.local')

def detect_json_corruption():
    """Detect common JSON corruption issues"""
    print("🔍 Detecting JSON corruption issues...")
    
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    if not service_account_path:
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH not set")
        return
    
    if not os.path.exists(service_account_path):
        print(f"❌ File not found: {service_account_path}")
        return
    
    print(f"📄 Analyzing: {service_account_path}")
    
    try:
        # Read file content
        with open(service_account_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📏 File size: {len(content)} characters")
        
        # Check for common corruption issues
        issues = []
        
        # 1. Check for BOM (Byte Order Mark)
        if content.startswith('\ufeff'):
            issues.append("⚠️ Contains BOM (Byte Order Mark) - may cause issues")
        
        # 2. Check for invalid characters
        invalid_chars = re.findall(r'[^\x20-\x7E\n\r\t]', content)
        if invalid_chars:
            issues.append(f"⚠️ Contains {len(invalid_chars)} invalid characters")
        
        # 3. Check for line ending issues
        crlf_count = content.count('\r\n')
        lf_count = content.count('\n') - crlf_count
        cr_count = content.count('\r') - crlf_count
        
        if crlf_count > 0 and lf_count > 0:
            issues.append("⚠️ Mixed line endings (CRLF and LF)")
        elif cr_count > 0:
            issues.append("⚠️ Contains CR line endings (Mac OS 9 style)")
        
        # 4. Check for trailing commas
        if re.search(r',\s*}', content) or re.search(r',\s*]', content):
            issues.append("⚠️ Contains trailing commas")
        
        # 5. Check for missing quotes
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*:', content):
            issues.append("⚠️ May contain unquoted keys")
        
        # 6. Try to parse JSON
        try:
            parsed = json.loads(content)
            print("✅ JSON syntax is valid")
            
            # Check required fields
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in parsed]
            
            if missing_fields:
                issues.append(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
        except json.JSONDecodeError as e:
            issues.append(f"❌ JSON syntax error: {e}")
        
        # 7. Check private key format
        try:
            parsed = json.loads(content)
            private_key = parsed.get('private_key', '')
            
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                issues.append("❌ Private key format is invalid")
            elif not private_key.endswith('-----END PRIVATE KEY-----'):
                issues.append("❌ Private key is incomplete")
            else:
                print("✅ Private key format is valid")
                
        except:
            pass
        
        # 8. Check for common text editor artifacts
        if '\t' in content:
            issues.append("⚠️ Contains tab characters (may cause issues)")
        
        if content.count('"') % 2 != 0:
            issues.append("⚠️ Odd number of quotes (may indicate corruption)")
        
        # Report findings
        print(f"\n📊 Analysis Results:")
        if issues:
            print("❌ Issues found:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ No corruption issues detected")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if issues:
            print("   🔄 Consider re-downloading the JSON file from Google Cloud Console")
            print("   📝 Use a proper JSON editor (VS Code, Notepad++)")
            print("   🔒 Store the file securely to prevent corruption")
        else:
            print("   ✅ Your JSON file appears to be in good condition")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("JSON Corruption Detector")
    print("=" * 50)
    detect_json_corruption() 