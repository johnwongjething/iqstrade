# 🔔 Firebase Cloud Messaging (FCM) Setup Guide

## 📋 Overview
This guide will help you set up Firebase Cloud Messaging for push notifications in your IQS Trade BOL system. The implementation includes 4 high-priority notification types:

1. **New Bill Uploads** 🔔
2. **Payment Confirmations** ✅
3. **System Errors** 🚨
4. **Customer Escalations** 📞

## 🚀 Step 1: Firebase Project Setup

### 1.1 Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or use existing project
3. Enter project name: `iqstrade-notifications`
4. Enable Google Analytics (optional)
5. Click "Create project"

### 1.2 Enable Cloud Messaging
1. In Firebase Console, go to **Project Settings** (gear icon)
2. Click **Cloud Messaging** tab
3. Under **Web configuration**, click **Generate key pair**
4. Copy the **Web Push certificate** (VAPID key) - you'll need this later

### 1.3 Add Web App
1. In Project Settings, click **Add app** → **Web**
2. App nickname: `IQS Trade Web App`
3. Click **Register app**
4. Copy the **firebaseConfig** object - you'll need this for frontend

## 🔧 Step 2: Frontend Configuration

### 2.1 Install Firebase SDK
```bash
cd frontend
npm install firebase
```

### 2.2 Update Firebase Configuration
Edit `frontend/src/firebase.js`:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_ACTUAL_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};

const vapidKey = "YOUR_ACTUAL_VAPID_KEY";
```

### 2.3 Update Service Worker
Edit `frontend/public/firebase-messaging-sw.js` with the same `firebaseConfig`.

## 🔧 Step 3: Backend Configuration

### 3.1 Add Environment Variables
Add to your `.env.local` file:

```bash
# Firebase Configuration
FIREBASE_SERVER_KEY=YOUR_FIREBASE_SERVER_KEY
FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
FIREBASE_WEB_PUSH_CERTIFICATE=YOUR_VAPID_KEY
```

### 3.2 Get Firebase Server Key
1. In Firebase Console, go to **Project Settings**
2. Click **Service accounts** tab
3. Click **Generate new private key**
4. Download the JSON file
5. Copy the `server_key` value to your environment variables

### 3.3 Run Database Migration
```sql
-- Run this SQL in your database
CREATE TABLE IF NOT EXISTS fcm_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT fk_fcm_tokens_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fcm_tokens_user_id ON fcm_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_token ON fcm_tokens(token);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_active ON fcm_tokens(is_active);
```

## 🧪 Step 4: Testing

### 4.1 Start the Application
```bash
# Backend
cd backend
python app.py

# Frontend (in new terminal)
cd frontend
npm start
```

### 4.2 Test Notifications
1. Open your app in browser: `http://localhost:3000`
2. Log in to the system
3. Navigate to: `http://localhost:3000/notification-test`
4. Grant notification permissions when prompted
5. Click test buttons to send notifications

## 📱 Step 5: Integration with Existing Code

### 5.1 New Bill Upload Integration
Add to your bill upload endpoint:

```python
from fcm_service import fcm_service

# After successful bill upload
fcm_service.send_new_bill_notification(
    bill_id=bill_id,
    customer_name=customer_name,
    amount=amount,
    bill_number=bill_number
)
```

### 5.2 Payment Confirmation Integration
Add to your payment processing:

```python
# After payment confirmation
fcm_service.send_payment_confirmation_notification(
    bill_id=bill_id,
    bill_number=bill_number,
    amount=amount,
    payment_method=payment_method
)
```

### 5.3 System Error Integration
Add to your error handling:

```python
# When system errors occur
fcm_service.send_system_error_notification(
    error_type="Database Connection",
    error_message="Connection timeout",
    severity="high"
)
```

### 5.4 Customer Escalation Integration
Add to your escalation system:

```python
# When customer escalations occur
fcm_service.send_customer_escalation_notification(
    customer_name=customer_name,
    customer_phone=customer_phone,
    issue_type=issue_type,
    priority="high"
)
```

## 🔍 Step 6: Troubleshooting

### Common Issues:

1. **"FCM server key not configured"**
   - Check your `FIREBASE_SERVER_KEY` environment variable
   - Make sure you copied the correct server key from Firebase

2. **"No registration token available"**
   - Check browser console for FCM errors
   - Ensure notification permissions are granted
   - Verify Firebase configuration is correct

3. **Notifications not showing**
   - Check if browser supports notifications
   - Verify service worker is registered
   - Check browser console for errors

4. **"Failed to send notification"**
   - Check Firebase Console for error logs
   - Verify topic names are correct
   - Check network connectivity

### Debug Commands:

```bash
# Check if FCM service is working
curl -X POST http://localhost:5000/api/fcm/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check FCM tokens
curl -X GET http://localhost:5000/api/fcm/tokens \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 Step 7: Production Deployment

### 7.1 Environment Variables
Make sure these are set in your production environment:
- `FIREBASE_SERVER_KEY`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_WEB_PUSH_CERTIFICATE`

### 7.2 HTTPS Requirements
- FCM works on HTTP for localhost testing
- Production requires HTTPS (already configured on Render.com)

### 7.3 Service Worker
- Service worker is automatically served from `/firebase-messaging-sw.js`
- No additional configuration needed

## 🎯 Step 8: Usage Examples

### Send Test Notification
```javascript
// Frontend
fetch('/api/fcm/test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include'
});
```

### Send Custom Notification
```javascript
// Frontend
fetch('/api/fcm/notify/custom', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'custom_topic',
    title: 'Custom Title',
    body: 'Custom message',
    data: { customField: 'value' }
  }),
  credentials: 'include'
});
```

## ✅ Success Checklist

- [ ] Firebase project created
- [ ] Web app added to Firebase
- [ ] VAPID key generated
- [ ] Server key obtained
- [ ] Environment variables configured
- [ ] Database migration run
- [ ] Frontend Firebase config updated
- [ ] Service worker configured
- [ ] Test notifications working
- [ ] Integration with existing code complete

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Check Firebase Console for delivery reports
3. Verify all configuration values are correct
4. Test with the notification test page first

---

**🎉 Congratulations!** Your FCM push notification system is now ready to send high-priority alerts for your BOL system. 