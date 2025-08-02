import React, { useState } from 'react';
import { Button, Card, Typography, Box, Alert } from '@mui/material';

const SimpleNotificationTest = () => {
  console.log('🔔 SimpleNotificationTest component is rendering!');
  
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

  const testBackendNotification = async () => {
    try {
      const response = await fetch('/api/fcm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });

      if (response.ok) {
        setMessage('✅ Backend notification test sent!');
      } else {
        setMessage('❌ Backend notification failed - check if you are logged in');
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🔔 Simple Notification Test
      </Typography>
      
      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📱 Instructions
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          1. Click "Request Permission" to allow notifications
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          2. Test local notifications first
        </Typography>
        <Typography variant="body2" color="text.secondary">
          3. Then test backend notifications (requires login)
        </Typography>
      </Card>

      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔐 Permission Status
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Status: <strong>{permission}</strong>
        </Typography>
        
        {permission !== 'granted' && (
          <Button 
            variant="contained" 
            onClick={requestPermission}
            sx={{ mb: 2 }}
          >
            Request Notification Permission
          </Button>
        )}
      </Card>

      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🧪 Test Notifications
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={testLocalNotification}
            disabled={permission !== 'granted'}
            sx={{ p: 2 }}
          >
            🧪 Test Local Notification
          </Button>
          
          <Button
            variant="outlined"
            onClick={testBackendNotification}
            sx={{ p: 2 }}
          >
            🔔 Test Backend Notification
          </Button>
        </Box>
      </Card>

      {message && (
        <Alert severity={message.includes('✅') ? 'success' : 'error'} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Card sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📋 Next Steps
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>✅ This page loads without errors</li>
          <li>✅ Notification permission works</li>
          <li>✅ Local notifications work</li>
          <li>✅ Backend notifications work</li>
          <li>✅ Ready for phone testing</li>
        </Box>
      </Card>
    </Box>
  );
};

export default SimpleNotificationTest; 