import React, { useState, useEffect } from 'react';
import { Button, Card, Typography, Box, Alert, Divider } from '@mui/material';
// import { requestNotificationPermission, getFCMToken } from '../firebase';

const NotificationTestPage = () => {
  const [permission, setPermission] = useState('default');
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    checkNotificationPermission();
  }, []);

  const checkNotificationPermission = async () => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  };

  const requestPermission = async () => {
    setLoading(true);
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
    setLoading(false);
  };

  const testNotification = async (type) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/fcm/notify/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(getTestData(type)),
        credentials: 'include'
      });

      const result = await response.json();
      
      if (response.ok) {
        setMessage(`✅ ${type} notification sent successfully!`);
      } else {
        setMessage(`❌ Failed to send ${type} notification: ${result.error}`);
      }
    } catch (error) {
      setMessage(`❌ Error sending notification: ${error.message}`);
    }
    setLoading(false);
  };

  const getTestData = (type) => {
    switch (type) {
      case 'new-bill':
        return {
          bill_id: 123,
          customer_name: 'Test Customer',
          amount: 1500.00,
          bill_number: 'TEST123'
        };
      case 'payment-confirmation':
        return {
          bill_id: 123,
          bill_number: 'TEST123',
          amount: 1500.00,
          payment_method: 'Credit Card'
        };
      case 'system-error':
        return {
          error_type: 'Database',
          error_message: 'Connection timeout test',
          severity: 'high'
        };
      case 'customer-escalation':
        return {
          customer_name: 'John Doe',
          customer_phone: '+1234567890',
          issue_type: 'Payment Issue',
          priority: 'high'
        };
      default:
        return {};
    }
  };

  const testLocalNotification = () => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('🧪 Local Test', {
        body: 'This is a local notification test',
        icon: '/favicon.ico'
      });
      setMessage('✅ Local notification sent!');
    } else {
      setMessage('❌ Cannot send local notification - permission not granted');
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🔔 FCM Notification Test
      </Typography>
      
      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📱 Setup Instructions
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          1. Open this page on your phone browser (http://localhost:3000/notification-test)
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          2. Grant notification permission when prompted
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          3. Test different notification types using the buttons below
        </Typography>
        <Typography variant="body2" color="text.secondary">
          4. You should receive push notifications on your phone!
        </Typography>
      </Card>

      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔐 Permission Status
        </Typography>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body1">
            Status: <strong>{permission}</strong>
          </Typography>
          {token && (
            <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
              FCM Token: {token.substring(0, 50)}...
            </Typography>
          )}
        </Box>
        
        {permission !== 'granted' && (
          <Button 
            variant="contained" 
            onClick={requestPermission}
            disabled={loading}
            sx={{ mb: 2 }}
          >
            {loading ? 'Requesting...' : 'Request Notification Permission'}
          </Button>
        )}
      </Card>

      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🧪 Test Notifications
        </Typography>
        
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' } }}>
          <Button
            variant="outlined"
            onClick={() => testNotification('new-bill')}
            disabled={loading || permission !== 'granted'}
            sx={{ p: 2 }}
          >
            🔔 New Bill Upload
          </Button>
          
          <Button
            variant="outlined"
            onClick={() => testNotification('payment-confirmation')}
            disabled={loading || permission !== 'granted'}
            sx={{ p: 2 }}
          >
            ✅ Payment Confirmation
          </Button>
          
          <Button
            variant="outlined"
            onClick={() => testNotification('system-error')}
            disabled={loading || permission !== 'granted'}
            sx={{ p: 2 }}
          >
            🚨 System Error
          </Button>
          
          <Button
            variant="outlined"
            onClick={() => testNotification('customer-escalation')}
            disabled={loading || permission !== 'granted'}
            sx={{ p: 2 }}
          >
            📞 Customer Escalation
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />
        
        <Button
          variant="contained"
          onClick={testLocalNotification}
          disabled={permission !== 'granted'}
          sx={{ p: 2 }}
        >
          🧪 Test Local Notification
        </Button>
      </Card>

      {message && (
        <Alert severity={message.includes('✅') ? 'success' : 'error'} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Card sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📋 Testing Checklist
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>✅ Backend running on port 5000</li>
          <li>✅ Frontend running on port 3000</li>
          <li>✅ Notification permission granted</li>
          <li>✅ FCM token received</li>
          <li>✅ Test notifications sent</li>
          <li>✅ Notifications received on phone</li>
        </Box>
      </Card>
    </Box>
  );
};

export default NotificationTestPage; 