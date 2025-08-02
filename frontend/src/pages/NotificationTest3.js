import React, { useState } from 'react';

const NotificationTest3 = () => {
  console.log('🔔 NotificationTest3 component is rendering!');
  
  const [permission, setPermission] = useState('default');
  const [message, setMessage] = useState('');

  const requestPermission = async () => {
    try {
      if ('Notification' in window) {
        const result = await Notification.requestPermission();
        setPermission(result);
        
        if (result === 'granted') {
          setMessage('✅ Notification permission granted!');
        } else {
          setMessage('❌ Notification permission denied.');
        }
      } else {
        setMessage('❌ Notifications not supported in this browser.');
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    }
  };

  const testLocalNotification = () => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('🧪 Test Notification', {
        body: 'This is a test notification from IQS Trade!',
        icon: '/favicon.ico'
      });
      setMessage('✅ Local notification sent!');
    } else {
      setMessage('❌ Cannot send notification - permission not granted');
    }
  };

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🔔 Notification Test 3</h1>
      <p>This is a new test component to avoid caching issues.</p>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>🔐 Permission Status</h3>
        <p>Status: <strong>{permission}</strong></p>
        
        {permission !== 'granted' && (
          <button 
            onClick={requestPermission}
            style={{ 
              padding: '10px 20px', 
              backgroundColor: '#1976d2', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer',
              marginBottom: '10px'
            }}
          >
            Request Notification Permission
          </button>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>🧪 Test Notifications</h3>
        
        <button
          onClick={testLocalNotification}
          disabled={permission !== 'granted'}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: permission === 'granted' ? '#4caf50' : '#ccc', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: permission === 'granted' ? 'pointer' : 'not-allowed',
            marginBottom: '10px'
          }}
        >
          🧪 Test Local Notification
        </button>
      </div>

      {message && (
        <div style={{ 
          padding: '10px', 
          backgroundColor: message.includes('✅') ? '#d4edda' : '#f8d7da',
          color: message.includes('✅') ? '#155724' : '#721c24',
          border: '1px solid',
          borderColor: message.includes('✅') ? '#c3e6cb' : '#f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {message}
        </div>
      )}
    </div>
  );
};

export default NotificationTest3; 