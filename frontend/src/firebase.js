import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Firebase configuration - REPLACE WITH YOUR ACTUAL VALUES
const firebaseConfig = {
  apiKey: "AIzaSyBqEvEzPZNbvrDeW8k8iL2UW54hij9lODQ",
  authDomain: "iqstrade-notifications.firebaseapp.com",
  projectId: "iqstrade-notifications",
  storageBucket: "iqstrade-notifications.firebasestorage.app",
  messagingSenderId: "1014016675028",
  appId: "1:1014016675028:web:fddce8afb4a82a857e7f41",
  measurementId: "G-D5YCYHCQMF"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// VAPID key for web push notifications - REPLACE WITH YOUR ACTUAL VAPID KEY
const vapidKey = "BFwxgQkr7b5ScQrbsmlbiffWSQxzV051VhEw9tHaT8_yvwd3HBu7CmfUXxCKOsvbvKWT6ETb4A0ixJSIU81qOrw";

// Request notification permission and get FCM token
export const requestNotificationPermission = async () => {
  try {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      console.log('Notification permission granted');
      return await getFCMToken();
    } else {
      console.log('Notification permission denied');
      return null;
    }
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return null;
  }
};

// Get FCM token
export const getFCMToken = async () => {
  try {
    console.log('🔔 Getting FCM token...');
    console.log('🔔 Firebase messaging object:', messaging);
    console.log('🔔 VAPID key:', vapidKey);
    console.log('🔔 Checking if service worker is registered...');
    
    // Check if service worker is registered
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        console.log('✅ Service worker is registered:', registration);
        console.log('🔔 Service worker scope:', registration.scope);
        console.log('🔔 Service worker state:', registration.active ? 'active' : 'inactive');
      } else {
        console.log('❌ No service worker registered');
        // Try to register the service worker
        console.log('🔔 Attempting to register service worker...');
        try {
          const newRegistration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
          console.log('✅ Service worker registered:', newRegistration);
        } catch (error) {
          console.error('❌ Failed to register service worker:', error);
        }
      }
    } else {
      console.log('❌ Service workers not supported');
    }
    
    console.log('🔔 Requesting FCM token with vapidKey:', vapidKey);
    console.log('🔔 About to call getToken()...');
    
    const currentToken = await getToken(messaging, { vapidKey });
    
    console.log('🔔 getToken() completed');
    console.log('🔔 Token result:', currentToken);
    console.log('🔔 Token type:', typeof currentToken);
    
    if (currentToken) {
      console.log('✅ FCM Token generated:', currentToken);
      console.log('📱 Token length:', currentToken.length);
      console.log('📱 Token preview:', currentToken.substring(0, 50) + '...');
      console.log('📱 Token ends with:', currentToken.substring(currentToken.length - 20));
      console.log('📱 Token contains ":" count:', (currentToken.match(/:/g) || []).length);
      
      // Send token to backend
      console.log('🔔 Sending token to backend...');
      await sendTokenToBackend(currentToken);
      console.log('🔔 Token sent to backend successfully');
      
      return currentToken;
    } else {
      console.warn('❌ No registration token available');
      console.log('🔔 currentToken is falsy:', currentToken);
      return null;
    }
  } catch (error) {
    console.error('❌ Error getting FCM token:', error);
    console.error('❌ Error name:', error.name);
    console.error('❌ Error message:', error.message);
    console.error('❌ Error stack:', error.stack);
    return null;
  }
};

// Send FCM token to backend
export const sendTokenToBackend = async (token) => {
  try {
    // Use dynamic API base URL
    const baseUrl = window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin;
    const response = await fetch(`${baseUrl}/api/fcm/token/public`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
      credentials: 'include'
    });
    
    if (response.ok) {
      console.log('FCM token sent to backend successfully');
      return true;
    } else {
      console.error('Failed to send FCM token to backend');
      return false;
    }
  } catch (error) {
    console.error('Error sending FCM token to backend:', error);
    return false;
  }
};

// Listen for foreground messages
export const setupForegroundListener = (callback) => {
  console.log('🔔 Setting up FCM foreground listener...');
  
  return onMessage(messaging, (payload) => {
    console.log('🔔 Foreground message received:', payload);
    console.log('🔔 Payload structure:', JSON.stringify(payload, null, 2));
    
    // Show notification even when app is in foreground
    if (payload.notification) {
      const { title, body } = payload.notification;
      console.log('🔔 Showing foreground notification:', title, body);
      showLocalNotification(title, body, payload.data);
    } else {
      console.log('🔔 No notification in payload, payload keys:', Object.keys(payload));
    }
    
    // Call custom callback if provided
    if (callback) {
      callback(payload);
    }
  });
};

// Show local notification
export const showLocalNotification = async (title, body, data = {}) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    try {
      // Use service worker for better mobile compatibility
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          await registration.showNotification(title, {
            body,
            icon: '/favicon.ico',
            badge: '/favicon.ico',
            data,
            requireInteraction: true,
            actions: [
              {
                action: 'view',
                title: 'View Details'
              },
              {
                action: 'dismiss',
                title: 'Dismiss'
              }
            ]
          });
          console.log('✅ Foreground notification shown via service worker');
          return;
        }
      }
      
      // Fallback to direct notification (for desktop)
      const notification = new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        data
      });
      
      // Handle notification click
      notification.onclick = () => {
        window.focus();
        notification.close();
        
        // Handle different notification types
        if (data.type) {
          handleNotificationClick(data);
        }
      };
      
      console.log('✅ Foreground notification shown directly');
    } catch (error) {
      console.error('❌ Error showing foreground notification:', error);
    }
  } else {
    console.log('❌ Notification permission not granted');
  }
};

// Handle notification click based on type
const handleNotificationClick = (data) => {
  switch (data.type) {
    case 'new_bill':
      // Navigate to bill details
      if (data.billId) {
        window.location.href = `/edit-bill/${data.billId}`;
      }
      break;
    case 'payment_confirmation':
      // Navigate to payment details
      if (data.billId) {
        window.location.href = `/edit-bill/${data.billId}`;
      }
      break;
    case 'system_error':
      // Navigate to system status or dashboard
      window.location.href = '/dashboard';
      break;
    case 'customer_escalation':
      // Navigate to customer emails or escalation page
      window.location.href = '/customer-emails';
      break;
    default:
      // Default to dashboard
      window.location.href = '/dashboard';
  }
};

// Subscribe to a topic
export const subscribeToTopic = async (topic) => {
  try {
    const token = await getFCMToken();
    if (!token) {
      throw new Error('No FCM token available');
    }
    
    // Send subscription request to backend
    const baseUrl = window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin;
    const response = await fetch(`${baseUrl}/api/fcm/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, topic }),
      credentials: 'include'
    });
    
    if (response.ok) {
      console.log(`✅ Subscribed to topic: ${topic}`);
      return true;
    } else {
      console.error('Failed to subscribe to topic');
      return false;
    }
  } catch (error) {
    console.error('Error subscribing to topic:', error);
    return false;
  }
};

export { messaging, vapidKey }; 