# 🚀 Azure Deployment Guide for IQS Trade

## 📋 **System Overview**
Your IQS Trade system is **production-ready** with all core features implemented:
- ✅ **Customer Features**: Upload, search, view invoices/receipts, bulk upload (5 files)
- ✅ **Business Features**: Payment processing (AllinPay + bank transfers), invoice generation, financial reports
- ✅ **Email System**: AI-powered email processing with draft generation
- ✅ **OCR Processing**: Enhanced V5 with human oversight for accuracy

## 🎯 **Azure Deployment Checklist**

### **1. Azure Services Required**

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| **Azure App Service** | Web application hosting | ~$75/month |
| **Azure PostgreSQL** | Database hosting | ~$75/month |
| **Azure Blob Storage** | File storage (optional - can keep Cloudinary) | ~$5/month |
| **Azure Key Vault** | Secrets management | ~$3/month |
| **Application Insights** | Monitoring (optional) | ~$10/month |

**Total Estimated Cost: ~$168/month**

### **2. Pre-Deployment Preparation**

#### **A. Update OpenAI API (Critical)**
```bash
# Current: OpenAI 0.28.0 (outdated)
# Required: OpenAI 1.x (latest)

pip install --upgrade openai
```

#### **B. Environment Variables for Azure**
Create `azure.env` file:
```bash
# === CORE APPLICATION ===
SECRET_KEY=your_azure_secret_key
JWT_SECRET_KEY=your_jwt_secret_for_azure
FLASK_ENV=production
FLASK_DEBUG=false

# === DATABASE (Azure PostgreSQL) ===
DATABASE_URL=postgresql://username:password@azure-postgresql-host:5432/database_name

# === EMAIL CONFIGURATION ===
EMAIL_HOST=imap.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp-relay.brevo.com
SMTP_USERNAME=your_brevo_username
SMTP_PASSWORD=your_brevo_password
FROM_EMAIL=your_email@gmail.com

# === OPENAI INTEGRATION ===
OPENAI_API_KEY=sk-your_openai_api_key_here

# === FILE STORAGE (Choose one) ===
# Option 1: Keep Cloudinary (easier)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Option 2: Azure Blob Storage (more control)
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
AZURE_STORAGE_CONTAINER_NAME=iqstrade-files

# === AZURE SPECIFIC ===
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# === SECURITY ===
CORS_ORIGINS=https://your-azure-app.azurewebsites.net
JWT_COOKIE_DOMAIN=your-azure-app.azurewebsites.net
JWT_COOKIE_CSRF_PROTECT=true

# === PERFORMANCE ===
MAX_CONTENT_LENGTH=10485760  # 10MB
EMAIL_CHECK_INTERVAL=900     # 15 minutes
AUTO_SEND_ENABLED=true
CONFIDENCE_THRESHOLD=0.8
```

### **3. Azure Setup Steps**

#### **Step 1: Create Azure Resources**
```bash
# 1. Create Resource Group
az group create --name iqstrade-rg --location eastasia

# 2. Create App Service Plan
az appservice plan create --name iqstrade-plan --resource-group iqstrade-rg --sku S1

# 3. Create Web App
az webapp create --name iqstrade-app --resource-group iqstrade-rg --plan iqstrade-plan --runtime "PYTHON:3.11"

# 4. Create PostgreSQL Database
az postgres flexible-server create --name iqstrade-db --resource-group iqstrade-rg --location eastasia --admin-user admin --admin-password YourPassword123! --sku-name Standard_B1ms --version 14

# 5. Create Storage Account (optional - for file storage)
az storage account create --name iqstradestorage --resource-group iqstrade-rg --location eastasia --sku Standard_LRS

# 6. Create Key Vault
az keyvault create --name iqstrade-kv --resource-group iqstrade-rg --location eastasia
```

#### **Step 2: Configure Database**
```sql
-- Connect to Azure PostgreSQL and run:
\i backend/migrations/20250716_openai_integration_schema.sql

-- Or run individual migration files:
\i backend/migrations/20240625_add_customer_invoice_and_packing_list.sql
\i backend/migrations/20250101_add_container_breakdown.sql
-- ... (all other migration files)
```

#### **Step 3: Configure App Service**
```bash
# Set environment variables
az webapp config appsettings set --name iqstrade-app --resource-group iqstrade-rg --settings @azure.env

# Configure Python version
az webapp config set --name iqstrade-app --resource-group iqstrade-rg --linux-fx-version "PYTHON|3.11"

# Enable HTTPS
az webapp update --name iqstrade-app --resource-group iqstrade-rg --https-only true
```

#### **Step 4: Deploy Application**
```bash
# Option 1: Deploy from Git
az webapp deployment source config --name iqstrade-app --resource-group iqstrade-rg --repo-url https://github.com/your-repo/iqstrade --branch main

# Option 2: Deploy from local files
az webapp deployment source config-local-git --name iqstrade-app --resource-group iqstrade-rg
git remote add azure https://your-app.scm.azurewebsites.net/your-app.git
git push azure main
```

### **4. Frontend Deployment**

#### **Option A: Azure Static Web Apps (Recommended)**
```bash
# 1. Build React app
cd frontend
npm run build

# 2. Deploy to Azure Static Web Apps
az staticwebapp create --name iqstrade-frontend --resource-group iqstrade-rg --source https://github.com/your-repo/iqstrade --location eastasia --branch main --app-location frontend --api-location backend
```

#### **Option B: Azure App Service**
```bash
# 1. Build React app
cd frontend
npm run build

# 2. Deploy build folder to Azure App Service
az webapp deployment source config-zip --name iqstrade-frontend --resource-group iqstrade-rg --src frontend/build.zip
```

### **5. Post-Deployment Configuration**

#### **A. Configure CORS**
```bash
# Allow frontend domain
az webapp config cors add --name iqstrade-app --resource-group iqstrade-rg --allowed-origins "https://your-frontend-domain.azurewebsites.net"
```

#### **B. Set up SSL Certificate**
```bash
# Azure provides free SSL certificates automatically
# Verify HTTPS is working
curl -I https://your-app.azurewebsites.net
```

#### **C. Configure Monitoring**
```bash
# Enable Application Insights
az monitor app-insights component create --app iqstrade-insights --location eastasia --resource-group iqstrade-rg --application-type web
```

### **6. Testing Checklist**

#### **Backend Tests**
- [ ] API endpoints responding (https://your-app.azurewebsites.net/api/test)
- [ ] Database connection working
- [ ] File uploads working (Cloudinary or Azure Blob)
- [ ] Email processing working
- [ ] OCR processing working
- [ ] Payment webhooks working

#### **Frontend Tests**
- [ ] Login/authentication working
- [ ] File upload working
- [ ] Bill search working
- [ ] Invoice generation working
- [ ] Payment processing working
- [ ] Email system working

### **7. Performance Optimization**

#### **A. Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_bills_customer_email ON bill_of_lading(customer_email);
CREATE INDEX idx_bills_created_at ON bill_of_lading(created_at);
CREATE INDEX idx_customer_emails_created_at ON customer_emails(created_at);
```

#### **B. Application Optimization**
```python
# In app.py, configure for production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
```

### **8. Security Hardening**

#### **A. Azure Security Center**
- Enable Azure Security Center
- Configure security policies
- Set up threat detection

#### **B. Network Security**
```bash
# Configure network security groups
az network nsg rule create --name allow-https --nsg-name iqstrade-nsg --resource-group iqstrade-rg --protocol tcp --destination-port-range 443 --priority 100
```

### **9. Backup Strategy**

#### **A. Database Backups**
```bash
# Azure PostgreSQL provides automatic backups
# Configure backup retention
az postgres flexible-server update --name iqstrade-db --resource-group iqstrade-rg --backup-retention-days 30
```

#### **B. Application Backups**
- Use Azure App Service backup
- Configure file storage backups
- Set up disaster recovery

### **10. Monitoring & Alerts**

#### **A. Application Insights**
- Monitor application performance
- Track user behavior
- Set up alerts for errors

#### **B. Azure Monitor**
- Monitor resource usage
- Set up cost alerts
- Configure scaling rules

## 🎯 **Deployment Timeline**

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1** | 1-2 days | Azure resource setup, database migration |
| **Phase 2** | 1 day | Backend deployment and testing |
| **Phase 3** | 1 day | Frontend deployment and testing |
| **Phase 4** | 1 day | Security configuration, monitoring setup |
| **Phase 5** | 1 day | Performance optimization, final testing |

**Total: 5-7 days for complete Azure deployment**

## 🚀 **Ready to Deploy!**

Your IQS Trade system is **production-ready** and well-suited for Azure deployment. The main work is:

1. **Update OpenAI API** (critical security fix)
2. **Configure Azure resources**
3. **Migrate database**
4. **Deploy application**
5. **Configure monitoring**

**Would you like me to help with any specific part of the Azure deployment process?** 