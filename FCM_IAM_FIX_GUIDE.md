# 🔧 FCM IAM Permission Fix Guide

## 🚨 Current Issue
```
"Permission 'cloudmessaging.messages.create' denied on resource '//cloudresourcemanager.googleapis.com/projects/iqstrade-notifications'"
```

This is a **Google Cloud IAM permission issue** - the service account doesn't have permission to send FCM messages.

## 🔧 Solution 1: Fix IAM Permissions (Recommended)

### Step 1: Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: `iqstrade-notifications`
3. Navigate to **IAM & Admin** → **IAM**

### Step 2: Find the Service Account
Look for the service account that's being used. Based on your environment variables, it should be:
- **Service Account Email**: `iqstrade-notifications-firebase-adminsdk-fbsvc@iqstrade-notifications.iam.gserviceaccount.com`
- **Service Account File**: `/etc/secrets/iqstrade-notifications-firebase-adminsdk-fbsvc-1aaa5c1174.json`

### Step 3: Add Required Permissions
Click the **pencil icon** next to the service account and add these roles:

**Primary Role:**
- **Firebase Cloud Messaging Admin** (`roles/firebase.cloudMessagingAdmin`)

**Additional Roles (if needed):**
- **Firebase Admin** (`roles/firebase.admin`)
- **Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`)

### Step 4: Verify Permissions
The service account should have these permissions:
- `firebase.cloudMessaging.messages.create`
- `firebase.projects.get`
- `iam.serviceAccounts.actAs`

## 🔧 Solution 2: Use Legacy FCM API (Fallback)

If IAM permissions can't be fixed immediately, we can switch to the legacy FCM API which uses server keys instead of service accounts.

### Step 1: Update Environment Variables
Add to your Render environment variables:
```
FIREBASE_SERVER_KEY=YOUR_LEGACY_SERVER_KEY
```

### Step 2: Switch to Legacy FCM Service
The code already has a fallback mechanism. If the modern service fails, it will use the legacy service.

## 🔧 Solution 3: Create New Service Account (Alternative)

### Step 1: Create New Service Account
1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Name: `fcm-notification-service`
4. Description: `Service account for FCM notifications`

### Step 2: Assign Permissions
Add these roles:
- **Firebase Cloud Messaging Admin**
- **Service Account Token Creator**

### Step 3: Create and Download Key
1. Click **Create Key** → **JSON**
2. Download the JSON file
3. Upload to Render as a new secret
4. Update `FIREBASE_SERVICE_ACCOUNT_PATH` environment variable

## 🔍 Verification Steps

### Test FCM Permissions
After fixing permissions, test with:

```bash
# Test FCM endpoint
curl -X POST https://iqstrade.onrender.com/api/fcm/test/public
```

### Check Service Account Status
```bash
# Verify service account can access FCM
gcloud auth activate-service-account --key-file=service-account.json
gcloud projects describe iqstrade-notifications
```

## 📋 Environment Variables Check

Ensure these are set in Render:
```
FIREBASE_PROJECT_ID=iqstrade-notifications
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/iqstrade-notifications-firebase-adminsdk-fbsvc-1aaa5c1174.json
FIREBASE_SERVER_KEY=AIzaSyBqEvEzPZNbvrDeW8k8iL2UW54hij9lODQ  # Legacy fallback
```

## 🚀 Quick Fix Commands

### Using gcloud CLI (if you have access):
```bash
# Add FCM Admin role to service account
gcloud projects add-iam-policy-binding iqstrade-notifications \
    --member="serviceAccount:iqstrade-notifications-firebase-adminsdk-fbsvc@iqstrade-notifications.iam.gserviceaccount.com" \
    --role="roles/firebase.cloudMessagingAdmin"

# Verify the role was added
gcloud projects get-iam-policy iqstrade-notifications \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:iqstrade-notifications-firebase-adminsdk-fbsvc@iqstrade-notifications.iam.gserviceaccount.com"
```

## 📞 Next Steps

1. **Immediate**: Fix IAM permissions in Google Cloud Console
2. **Test**: Verify FCM works after permission fix
3. **Monitor**: Check logs for successful FCM messages
4. **Fallback**: If IAM fix fails, switch to legacy FCM API

## 🔗 Useful Links

- [Firebase Cloud Messaging Admin Role](https://cloud.google.com/firebase/docs/projects/iam/roles#firebase_cloud_messaging_admin)
- [Google Cloud IAM Documentation](https://cloud.google.com/iam/docs)
- [FCM HTTP v1 API Reference](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send) 