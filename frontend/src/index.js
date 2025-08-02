import 'antd/dist/reset.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './pages/App';
import reportWebVitals from './reportWebVitals';
import { UserProvider } from './UserContext';
import { BrowserRouter } from 'react-router-dom';

// Register service worker for FCM
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
      .then((registration) => {
        console.log('✅ Service Worker registered successfully:', registration);
        
        // Force update the service worker
        registration.update();
        
        // Listen for service worker updates
        registration.addEventListener('updatefound', () => {
          console.log('🔔 Service worker update found');
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            console.log('🔔 Service worker state changed:', newWorker.state);
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('🔔 New service worker installed, reloading...');
              window.location.reload();
            }
          });
        });
        
        // Listen for service worker messages
        navigator.serviceWorker.addEventListener('message', (event) => {
          console.log('🔔 Received message from service worker:', event.data);
          console.log('🔔 Message type:', typeof event.data);
          console.log('🔔 Message keys:', Object.keys(event.data || {}));
          console.log('🔔 Full message structure:', JSON.stringify(event.data, null, 2));
          
          // Check if this is an FCM message and show notification
          if (event.data && event.data.notification) {
            console.log('🔔 FCM message received in main thread, showing notification...');
            console.log('🔔 Notification object:', event.data.notification);
            console.log('🔔 Data object:', event.data.data);
            
            // Show notification using service worker
            registration.showNotification(event.data.notification.title || 'IQS Trade Notification', {
              body: event.data.notification.body || 'You have a new notification',
              icon: '/favicon.ico',
              badge: '/favicon.ico',
              data: event.data.data || {},
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
            console.log('✅ FCM notification shown via service worker from main thread');
          } else {
            console.log('🔔 Not an FCM notification message - no push notification triggered');
            console.log('🔔 Reason: event.data.notification is missing or falsy');
          }
        });
      })
      .catch((error) => {
        console.error('❌ Service Worker registration failed:', error);
      });
  });
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <UserProvider>
        <App />
      </UserProvider>
    </BrowserRouter>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
