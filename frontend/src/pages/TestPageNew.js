import React from 'react';

const TestPageNew = () => {
  console.log('🧪 TestPageNew component is rendering!');

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🧪 NEW Test Page - {new Date().toLocaleTimeString()}</h1>
      <p>This is a completely new test component.</p>
      <p>If you see this, the issue was with the old TestPage.js file.</p>
      
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#e8f5e8', borderRadius: '4px' }}>
        <h3>🔔 Notification Test</h3>
        <button 
          onClick={() => {
            if ('Notification' in window) {
              Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                  new Notification('Test Notification', {
                    body: 'This is a test notification!',
                    icon: '/favicon.ico'
                  });
                  alert('✅ Notification sent!');
                } else {
                  alert('❌ Permission denied');
                }
              });
            } else {
              alert('❌ Notifications not supported');
            }
          }}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#4caf50', 
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

export default TestPageNew; 