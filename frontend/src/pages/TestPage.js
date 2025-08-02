import React from 'react';

const TestPage = () => {
  console.log('🧪 SIMPLE TestPage component is rendering!');

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🧪 SIMPLE Test Page - {new Date().toLocaleTimeString()}</h1>
      <p>This is a very simple test component.</p>
      <p>If you see this, hot reloading is working!</p>
      
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
        <h3>🔔 Basic Notification Test</h3>
        <button 
          onClick={() => {
            if ('Notification' in window) {
              Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                  new Notification('Test Notification', {
                    body: 'This is a test notification!',
                    icon: '/favicon.ico'
                  });
                  alert('Notification sent!');
                } else {
                  alert('Permission denied');
                }
              });
            } else {
              alert('Notifications not supported');
            }
          }}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#1976d2', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Test Notification
        </button>
      </div>
    </div>
  );
};

export default TestPage; 