# 🔧 Azure URL Fixes - Remove Hardcoded Localhost/IP Addresses

## 🚨 **Critical Files That Need URL Updates**

### **1. Frontend Configuration Files**

#### **A. `frontend/src/config.js`**
**Current (Hardcoded):**
```javascript
API_BASE_URL: 'http://localhost:5000', // Flask server port
```

**Fix for Azure:**
```javascript
API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'https://your-azure-app.azurewebsites.net',
```

#### **B. `frontend/env.example`**
**Current (Hardcoded):**
```bash
REACT_APP_API_BASE_URL=http://localhost:5000
```

**Fix for Azure:**
```bash
REACT_APP_API_BASE_URL=https://your-azure-app.azurewebsites.net
```

#### **C. `frontend/start_local.js`**
**Current (Hardcoded):**
```javascript
process.env.REACT_APP_API_BASE_URL = 'http://localhost:8000';
```

**Fix for Azure:**
```javascript
// This file should only be used for local development
// For Azure, use environment variables instead
```

### **2. Backend Configuration Files**

#### **A. `backend/config.py`**
**Current (Hardcoded):**
```python
return os.getenv('DB_HOST', 'localhost')
```

**Fix for Azure:**
```python
return os.getenv('DB_HOST', 'your-azure-postgresql-host.postgres.database.azure.com')
```

#### **B. `backend/config_local.py`**
**Current (Hardcoded):**
```python
'http://localhost:3000',  # React dev server
'http://localhost:3001',
'http://localhost:5000',  # Flask dev server
JWT_COOKIE_DOMAIN = None  # No domain restriction for localhost
```

**Fix for Azure:**
```python
'https://your-frontend-domain.azurewebsites.net',  # Frontend domain
'https://your-azure-app.azurewebsites.net',        # Backend domain
JWT_COOKIE_DOMAIN = 'your-azure-app.azurewebsites.net'  # Azure domain
```

### **3. Outlook Add-in Files (Critical)**

#### **A. `backend/outlook_addin/manifest.xml`**
**Current (Hardcoded IP):**
```xml
<IconUrl DefaultValue="https://192.168.50.244:5001/assets/icon-32.png" />
<HighResolutionIconUrl DefaultValue="https://192.168.50.244:5001/assets/icon-64.png" />
<AppDomain>192.168.50.244</AppDomain>
<AppDomain>localhost</AppDomain>
<bt:Url id="functionFile" DefaultValue="https://192.168.50.244:5001/outlook_addin/function.html" />
<bt:Url id="messageReadTaskPaneUrl" DefaultValue="https://192.168.50.244:5001/outlook_addin/taskpane.html" />
```

**Fix for Azure:**
```xml
<IconUrl DefaultValue="https://your-azure-app.azurewebsites.net/assets/icon-32.png" />
<HighResolutionIconUrl DefaultValue="https://your-azure-app.azurewebsites.net/assets/icon-64.png" />
<AppDomain>your-azure-app.azurewebsites.net</AppDomain>
<bt:Url id="functionFile" DefaultValue="https://your-azure-app.azurewebsites.net/outlook_addin/function.html" />
<bt:Url id="messageReadTaskPaneUrl" DefaultValue="https://your-azure-app.azurewebsites.net/outlook_addin/taskpane.html" />
```

#### **B. `backend/outlook_addin/taskpane.js`**
**Current (Hardcoded IP):**
```javascript
const API_BASE_URL = 'http://192.168.50.244:5000/api/outlook';
```

**Fix for Azure:**
```javascript
const API_BASE_URL = 'https://your-azure-app.azurewebsites.net/api/outlook';
```

#### **C. `backend/outlook_test_interface.py`**
**Current (Hardcoded):**
```python
BACKEND_URL = "http://localhost:5000"  # Change to your actual backend URL
```

**Fix for Azure:**
```python
BACKEND_URL = "https://your-azure-app.azurewebsites.net"
```

### **4. Environment Template Files**

#### **A. `backend/env_local_template.txt`**
**Current (Hardcoded):**
```bash
LOCAL_DATABASE_URL=postgresql://postgres:123456@localhost:5432/iqstrade_local
LOCAL_DB_HOST=localhost
```

**Fix for Azure:**
```bash
# For Azure, use:
DATABASE_URL=postgresql://username:password@your-azure-postgresql-host:5432/database_name
DB_HOST=your-azure-postgresql-host.postgres.database.azure.com
```

#### **B. `backend/create_env_local.py`**
**Current (Hardcoded):**
```python
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000
```

**Fix for Azure:**
```python
ALLOWED_ORIGINS=https://your-frontend-domain.azurewebsites.net,https://your-azure-app.azurewebsites.net
```

## 🛠️ **Implementation Steps**

### **Step 1: Create Azure Environment Variables**

Create `azure.env` file:
```bash
# === AZURE SPECIFIC URLS ===
AZURE_FRONTEND_URL=https://your-frontend-domain.azurewebsites.net
AZURE_BACKEND_URL=https://your-azure-app.azurewebsites.net
AZURE_DATABASE_URL=postgresql://username:password@your-azure-postgresql-host:5432/database_name

# === FRONTEND CONFIG ===
REACT_APP_API_BASE_URL=https://your-azure-app.azurewebsites.net

# === BACKEND CONFIG ===
CORS_ORIGINS=https://your-frontend-domain.azurewebsites.net,https://your-azure-app.azurewebsites.net
JWT_COOKIE_DOMAIN=your-azure-app.azurewebsites.net
DATABASE_URL=postgresql://username:password@your-azure-postgresql-host:5432/database_name
```

### **Step 2: Update Frontend Configuration**

#### **A. Update `frontend/src/config.js`**
```javascript
const config = {
  development: {
    API_BASE_URL: 'http://localhost:5000', // Local development
    ENABLE_DEBUG: true,
  },
  production: {
    API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'https://your-azure-app.azurewebsites.net',
    ENABLE_DEBUG: false,
  },
  local: {
    API_BASE_URL: 'http://localhost:5000', // Local development
    ENABLE_DEBUG: true,
  }
};
```

#### **B. Update `frontend/env.example`**
```bash
REACT_APP_API_BASE_URL=https://your-azure-app.azurewebsites.net
```

### **Step 3: Update Backend Configuration**

#### **A. Update `backend/config.py`**
```python
def get_database_host():
    """Get database host from environment or default to Azure"""
    if os.getenv('FLASK_ENV') == 'production':
        return os.getenv('DB_HOST', 'your-azure-postgresql-host.postgres.database.azure.com')
    else:
        return os.getenv('DB_HOST', 'localhost')
```

#### **B. Update `backend/config_local.py`**
```python
# For Azure production
CORS_ORIGINS = [
    'https://your-frontend-domain.azurewebsites.net',
    'https://your-azure-app.azurewebsites.net',
]

JWT_COOKIE_DOMAIN = 'your-azure-app.azurewebsites.net' if os.getenv('FLASK_ENV') == 'production' else None
```

### **Step 4: Update Outlook Add-in Files**

#### **A. Update `backend/outlook_addin/manifest.xml`**
Replace all instances of `192.168.50.244` and `localhost` with your Azure domain:
```xml
<IconUrl DefaultValue="https://your-azure-app.azurewebsites.net/assets/icon-32.png" />
<HighResolutionIconUrl DefaultValue="https://your-azure-app.azurewebsites.net/assets/icon-64.png" />
<AppDomain>your-azure-app.azurewebsites.net</AppDomain>
<bt:Url id="functionFile" DefaultValue="https://your-azure-app.azurewebsites.net/outlook_addin/function.html" />
<bt:Url id="messageReadTaskPaneUrl" DefaultValue="https://your-azure-app.azurewebsites.net/outlook_addin/taskpane.html" />
```

#### **B. Update `backend/outlook_addin/taskpane.js`**
```javascript
const API_BASE_URL = 'https://your-azure-app.azurewebsites.net/api/outlook';
```

### **Step 5: Update Test Files**

#### **A. Update `backend/outlook_test_interface.py`**
```python
BACKEND_URL = "https://your-azure-app.azurewebsites.net"
```

#### **B. Update other test files**
```python
# In test_profile_endpoints.py, test_csrf_fix.py, etc.
API_BASE_URL = "https://your-azure-app.azurewebsites.net"
```

## 🎯 **Automated Fix Script**

Create `fix_azure_urls.py`:
```python
#!/usr/bin/env python3
"""
Script to automatically replace hardcoded URLs with Azure URLs
"""

import os
import re
from pathlib import Path

# Azure configuration
AZURE_FRONTEND_URL = "https://your-frontend-domain.azurewebsites.net"
AZURE_BACKEND_URL = "https://your-azure-app.azurewebsites.net"
AZURE_DATABASE_HOST = "your-azure-postgresql-host.postgres.database.azure.com"

# Files to update
FILES_TO_UPDATE = [
    "frontend/src/config.js",
    "frontend/env.example",
    "backend/config.py",
    "backend/config_local.py",
    "backend/outlook_addin/manifest.xml",
    "backend/outlook_addin/taskpane.js",
    "backend/outlook_test_interface.py",
    "backend/env_local_template.txt",
    "backend/create_env_local.py",
]

def replace_urls_in_file(file_path, replacements):
    """Replace URLs in a file"""
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for old_url, new_url in replacements.items():
        content = content.replace(old_url, new_url)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated: {file_path}")
    else:
        print(f"ℹ️  No changes needed: {file_path}")

def main():
    """Main function to fix all URLs"""
    print("🔧 Fixing hardcoded URLs for Azure deployment...")
    
    replacements = {
        'http://localhost:5000': AZURE_BACKEND_URL,
        'http://localhost:3000': AZURE_FRONTEND_URL,
        'http://localhost:8000': AZURE_BACKEND_URL,
        'http://192.168.50.244:5000': AZURE_BACKEND_URL,
        'https://192.168.50.244:5001': AZURE_BACKEND_URL,
        '192.168.50.244': AZURE_BACKEND_URL.replace('https://', '').replace('http://', ''),
        'localhost': AZURE_DATABASE_HOST,
    }
    
    for file_path in FILES_TO_UPDATE:
        replace_urls_in_file(file_path, replacements)
    
    print("\n🎉 URL fixes completed!")
    print(f"📝 Frontend URL: {AZURE_FRONTEND_URL}")
    print(f"🔧 Backend URL: {AZURE_BACKEND_URL}")
    print(f"🗄️  Database Host: {AZURE_DATABASE_HOST}")

if __name__ == "__main__":
    main()
```

## 🚀 **Deployment Checklist**

After fixing URLs:

- [ ] **Frontend**: Update `REACT_APP_API_BASE_URL` environment variable
- [ ] **Backend**: Update `CORS_ORIGINS` and `JWT_COOKIE_DOMAIN`
- [ ] **Database**: Update connection string to Azure PostgreSQL
- [ ] **Outlook Add-in**: Update manifest.xml and taskpane.js
- [ ] **Test**: Verify all endpoints work with new URLs
- [ ] **SSL**: Ensure all URLs use HTTPS

## ⚠️ **Important Notes**

1. **Environment Variables**: Use environment variables instead of hardcoded URLs
2. **HTTPS Only**: All Azure URLs must use HTTPS
3. **CORS**: Update CORS origins to include your Azure domains
4. **JWT Cookies**: Update cookie domain for Azure
5. **Database**: Update connection strings for Azure PostgreSQL

**Would you like me to help you implement these fixes or create the automated script?** 