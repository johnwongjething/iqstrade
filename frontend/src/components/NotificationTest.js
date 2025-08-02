import React, { useState } from 'react';
import { Button, Card, CardContent, Typography, Box, Alert, Divider } from '@mui/material';
import { Send, Notifications, Warning, Payment, Business } from '@mui/icons-material';

const NotificationTest = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const testNotification = async (type, data) => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`/api/fcm/notify/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        credentials: 'include'
      });

      const result = await response.json();
      
      if (response.ok) {
        setResult({ success: true, message: result.message });
      } else {
        setResult({ success: false, message: result.error || 'Failed to send notification' });
      }
    } catch (error) {
      setResult({ success: false, message: `Error: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const testCases = [
    {
      type: 'new-bill',
      title: 'New Bill Upload',
      description: 'Test notification for new bill upload',
      icon: <Business color="primary" />,
      data: {
        bill_id: 123,
        customer_name: 'Test Customer',
        amount: 2500.00,
        bill_number: 'BL-2024-001'
      }
    },
    {
      type: 'payment-confirmation',
      title: 'Payment Confirmation',
      description: 'Test notification for payment confirmation',
      icon: <Payment color="success" />,
      data: {
        bill_id: 123,
        bill_number: 'BL-2024-001',
        amount: 2500.00,
        payment_method: 'Bank Transfer'
      }
    },
    {
      type: 'system-error',
      title: 'System Error',
      description: 'Test notification for system errors',
      icon: <Warning color="error" />,
      data: {
        error_type: 'Database Connection',
        error_message: 'Connection timeout after 30 seconds',
        severity: 'high'
      }
    },
    {
      type: 'customer-escalation',
      title: 'Customer Escalation',
      description: 'Test notification for customer escalations',
      icon: <Notifications color="warning" />,
      data: {
        customer_name: 'John Smith',
        customer_phone: '+852 1234 5678',
        issue_type: 'Payment Issue',
        priority: 'high'
      }
    }
  ];

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🔔 FCM Notification Testing
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        This page allows you to test the 4 high-priority notification types. 
        Make sure you have granted notification permissions in your browser.
      </Alert>

      {result && (
        <Alert 
          severity={result.success ? 'success' : 'error'} 
          sx={{ mb: 3 }}
          onClose={() => setResult(null)}
        >
          {result.message}
        </Alert>
      )}

      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' } }}>
        {testCases.map((testCase, index) => (
          <Card key={index} sx={{ height: 'fit-content' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {testCase.icon}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {testCase.title}
                </Typography>
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {testCase.description}
              </Typography>

              <Divider sx={{ my: 1 }} />

              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Data: {JSON.stringify(testCase.data, null, 2)}
              </Typography>

              <Button
                variant="contained"
                startIcon={<Send />}
                onClick={() => testNotification(testCase.type, testCase.data)}
                disabled={loading}
                fullWidth
              >
                {loading ? 'Sending...' : `Test ${testCase.title}`}
              </Button>
            </CardContent>
          </Card>
        ))}
      </Box>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📋 How to Use
          </Typography>
          <Typography variant="body2" color="text.secondary">
            1. Make sure you're logged in to the system<br/>
            2. Grant notification permissions when prompted<br/>
            3. Click any test button to send a notification<br/>
            4. Check your device for the notification<br/>
            5. Click on the notification to navigate to the relevant page
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default NotificationTest; 