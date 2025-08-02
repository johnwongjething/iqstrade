// Frontend FCM Debug Tool
// Add this to your browser console to debug FCM issues

console.log('🔍 FCM Debug Tool Starting...');

// Check if service worker is registered
async function checkServiceWorker() {
    console.log('📱 Checking Service Worker...');
    
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.getRegistration();
            if (registration) {
                console.log('✅ Service Worker is registered:', registration);
                console.log('📱 Service Worker state:', registration.active ? 'active' : 'inactive');
                return registration;
            } else {
                console.log('❌ No service worker registered');
                return null;
            }
        } catch (error) {
            console.log('❌ Error checking service worker:', error);
            return null;
        }
    } else {
        console.log('❌ Service workers not supported');
        return null;
    }
}

// Check notification permission
function checkNotificationPermission() {
    console.log('📱 Checking Notification Permission...');
    
    if ('Notification' in window) {
        const permission = Notification.permission;
        console.log('📱 Current permission:', permission);
        return permission;
    } else {
        console.log('❌ Notifications not supported');
        return null;
    }
}

// Check FCM token
async function checkFCMToken() {
    console.log('📱 Checking FCM Token...');
    
    try {
        // Import Firebase functions
        const { getFCMToken } = await import('./firebase');
        const token = await getFCMToken();
        
        if (token) {
            console.log('✅ FCM Token found:', token);
            console.log('📱 Token length:', token.length);
            console.log('📱 Token starts with:', token.substring(0, 20));
            return token;
        } else {
            console.log('❌ No FCM token available');
            return null;
        }
    } catch (error) {
        console.log('❌ Error getting FCM token:', error);
        return null;
    }
}

// Test local notification
async function testLocalNotification() {
    console.log('📱 Testing Local Notification...');
    
    if ('Notification' in window && Notification.permission === 'granted') {
        try {
            const registration = await navigator.serviceWorker.getRegistration();
            if (registration) {
                await registration.showNotification('Debug Test', {
                    body: 'This is a debug test notification',
                    icon: '/favicon.ico',
                    requireInteraction: true
                });
                console.log('✅ Local notification sent via service worker');
            } else {
                new Notification('Debug Test', {
                    body: 'This is a debug test notification',
                    icon: '/favicon.ico'
                });
                console.log('✅ Local notification sent directly');
            }
        } catch (error) {
            console.log('❌ Error sending local notification:', error);
        }
    } else {
        console.log('❌ Notification permission not granted');
    }
}

// Test FCM notification
async function testFCMNotification() {
    console.log('📱 Testing FCM Notification...');
    
    const token = await checkFCMToken();
    if (!token) {
        console.log('❌ Cannot test FCM without token');
        return;
    }
    
    try {
        const baseUrl = window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin;
        const response = await fetch(`${baseUrl}/api/fcm/send/direct`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: token,
                title: '🔍 Debug FCM Test',
                body: 'This is a debug FCM test notification'
            }),
            credentials: 'include'
        });
        
        console.log('📡 FCM Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ FCM Response:', result);
            console.log('📱 Check if you received the notification!');
        } else {
            console.log('❌ FCM request failed:', response.status, response.statusText);
        }
    } catch (error) {
        console.log('❌ Error testing FCM:', error);
    }
}

// Run all diagnostics
async function runDiagnostics() {
    console.log('🔍 Running FCM Diagnostics...');
    console.log('=' .repeat(50));
    
    // Check service worker
    const sw = await checkServiceWorker();
    
    // Check notification permission
    const permission = checkNotificationPermission();
    
    // Check FCM token
    const token = await checkFCMToken();
    
    console.log('=' .repeat(50));
    console.log('📊 Summary:');
    console.log(`Service Worker: ${sw ? '✅ Registered' : '❌ Not Registered'}`);
    console.log(`Notification Permission: ${permission || '❌ Not Supported'}`);
    console.log(`FCM Token: ${token ? '✅ Available' : '❌ Not Available'}`);
    
    if (sw && permission === 'granted' && token) {
        console.log('🎉 All checks passed! FCM should work.');
    } else {
        console.log('⚠️ Some checks failed. FCM may not work properly.');
    }
}

// Export functions for manual testing
window.FCMDebug = {
    checkServiceWorker,
    checkNotificationPermission,
    checkFCMToken,
    testLocalNotification,
    testFCMNotification,
    runDiagnostics
};

console.log('🔍 FCM Debug Tool loaded!');
console.log('📱 Run FCMDebug.runDiagnostics() to check everything');
console.log('📱 Run FCMDebug.testLocalNotification() to test local notifications');
console.log('📱 Run FCMDebug.testFCMNotification() to test FCM notifications'); 