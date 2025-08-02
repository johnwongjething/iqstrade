// Firebase messaging service worker for background notifications
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

console.log('🔔 Service worker script loading...');

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

// VAPID key for web push notifications
const vapidKey = "BFwxgQkr7b5ScQrbsmlbiffWSQxzV051VhEw9tHaT8_yvwd3HBu7CmfUXxCKOsvbvKWT6ETb4A0ixJSIU81qOrw";

console.log('🔔 Initializing Firebase in service worker...');

try {
  // Initialize Firebase
  firebase.initializeApp(firebaseConfig);
  const messaging = firebase.messaging();

  console.log('🔔 Firebase messaging initialized:', messaging);

  // Handle background messages
  messaging.onBackgroundMessage((payload) => {
    console.log('🔔 FCM Background message received:', payload);
    console.log('📱 Payload notification:', payload.notification);
    console.log('📱 Payload data:', payload.data);

    const notificationTitle = payload.notification.title || 'IQS Trade Notification';
    const notificationOptions = {
      body: payload.notification.body || 'You have a new notification',
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      data: payload.data || {},
      requireInteraction: true, // Keep notification until user interacts
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
    };

    console.log('📱 Showing notification with title:', notificationTitle);
    console.log('📱 Notification options:', notificationOptions);

    // Show notification
    return self.registration.showNotification(notificationTitle, notificationOptions);
  });

  console.log('🔔 FCM background message handler registered');

} catch (error) {
  console.error('❌ Error initializing Firebase in service worker:', error);
}

// Add a simple message listener for debugging
self.addEventListener('message', (event) => {
  console.log('🔔 Service worker received message:', event.data);
  console.log('🔔 Message type:', typeof event.data);
  console.log('🔔 Message keys:', Object.keys(event.data || {}));
  console.log('🔔 Full message structure:', JSON.stringify(event.data, null, 2));
  
  // Handle skip waiting message
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('🔔 Skipping waiting and activating new service worker...');
    self.skipWaiting();
    return;
  }
  
  // Try to extract notification from any possible structure
  let notification = null;
  let data = {};
  
  // Check all possible notification locations
  if (event.data?.notification) {
    notification = event.data.notification;
    data = event.data.data || {};
  } else if (event.data?.data?.notification) {
    notification = event.data.data.notification;
    data = event.data.data;
  } else if (event.data?.message?.notification) {
    notification = event.data.message.notification;
    data = event.data.message.data || {};
  } else if (event.data?.message?.message?.notification) {
    notification = event.data.message.message.notification;
    data = event.data.message.message.data || {};
  }
  
  console.log('🔔 Extracted notification:', notification);
  console.log('🔔 Extracted data:', data);
  
  if (notification) {
    console.log('🔔 FCM message received via message event - showing notification');
    
    const notificationTitle = notification.title || 'IQS Trade Notification';
    const notificationOptions = {
      body: notification.body || 'You have a new notification',
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      data: data,
      requireInteraction: true, // Keep notification until user interacts
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
    };

    console.log('📱 Showing notification with title:', notificationTitle);
    console.log('📱 Notification options:', notificationOptions);

    // Show notification
    try {
      const result = self.registration.showNotification(notificationTitle, notificationOptions);
      console.log('📱 Notification show result:', result);
      return result;
    } catch (error) {
      console.error('❌ Error showing notification:', error);
    }
  } else {
    console.log('🔔 Not an FCM notification message, ignoring');
  }
});

// Add install event for debugging
self.addEventListener('install', (event) => {
  console.log('🔔 Service worker installing...');
  // Force activate immediately
  self.skipWaiting();
});

// Add activate event for debugging
self.addEventListener('activate', (event) => {
  console.log('🔔 Service worker activating...');
  // Take control of all clients immediately
  event.waitUntil(self.clients.claim());
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const data = event.notification.data;
  const action = event.action;
  
  if (action === 'dismiss') {
    return;
  }
  
  // Handle different notification types
  let url = '/dashboard'; // Default URL
  
  if (data && data.type) {
    switch (data.type) {
      case 'new_bill':
        if (data.billId) {
          url = `/edit-bill/${data.billId}`;
        }
        break;
      case 'payment_confirmation':
        if (data.billId) {
          url = `/edit-bill/${data.billId}`;
        }
        break;
      case 'system_error':
        url = '/dashboard';
        break;
      case 'customer_escalation':
        url = '/customer-emails';
        break;
    }
  }
  
  // Open the app and navigate to the specific page
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if app is already open
      for (const client of clientList) {
        if (client.url.includes(window.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      
      // If app is not open, open it
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event);
  // You can add analytics tracking here if needed
}); 