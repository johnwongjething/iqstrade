import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Paper
} from '@mui/material';
import {
  Notifications,
  PhoneAndroid,
  CheckCircle,
  Error,
  Info,
  ContentCopy,
  Refresh,
  Settings,
  Security
} from '@mui/icons-material';
import { UserContext } from '../UserContext';

const FCMSetup = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [fcmToken, setFcmToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [permission, setPermission] = useState('');
  const [serviceWorkerStatus, setServiceWorkerStatus] = useState('');
  const [deviceInfo, setDeviceInfo] = useState({});

  useEffect(() => {
    // Temporarily disable authentication check for testing
    console.log('FCMSetup component mounted');
    checkInitialStatus();
  }, []);

  const checkInitialStatus = async () => {
    setStatus('Checking current status...');
    
    // Check notification permission
    if ('Notification' in window) {
      setPermission(Notification.permission);
    } else {
      setPermission('not-supported');
    }

    // Check service worker
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        setServiceWorkerStatus(registration ? 'registered' : 'not-registered');
      } catch (error) {
        setServiceWorkerStatus('error');
      }
    } else {
      setServiceWorkerStatus('not-supported');
    }

    // Get device info
    setDeviceInfo({
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine
    });

    setStatus('');
  };

  const requestNotificationPermission = async () => {
    setIsLoading(true);
    setError('');
    setSuccess('');
    setStatus('Requesting notification permission...');

    try {
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        setPermission(permission);
        
        if (permission === 'granted') {
          setSuccess('Notification permission granted!');
          await getFCMToken();
        } else {
          setError('Notification permission denied. Please enable notifications in your browser settings.');
        }
      } else {
        setError('Notifications are not supported in this browser.');
      }
    } catch (error) {
      setError(`Error requesting permission: ${error.message}`);
    } finally {
      setIsLoading(false);
      setStatus('');
    }
  };

  const getFCMToken = async () => {
    setStatus('Getting FCM token...');
    
    try {
      // Import Firebase functions dynamically
      const { getFCMToken } = await import('../firebase');
      const token = await getFCMToken();
      
      if (token) {
        setFcmToken(token);
        setSuccess('FCM token obtained successfully!');
        
        // Test the token by sending a test notification
        await testFCMToken(token);
      } else {
        setError('Failed to get FCM token. Please try again.');
      }
    } catch (error) {
      setError(`Error getting FCM token: ${error.message}`);
    } finally {
      setStatus('');
    }
  };

  const testFCMToken = async (token) => {
    setStatus('Testing FCM token...');
    
    try {
      const baseUrl = window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin;
      const response = await fetch(`${baseUrl}/api/fcm/send/direct`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          title: '🔔 FCM Setup Test',
          body: 'Your device is now configured for notifications!'
        }),
        credentials: 'include'
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setSuccess('Test notification sent successfully! Check if you received it.');
        } else {
          setError(`Test failed: ${result.error}`);
        }
      } else {
        setError('Failed to send test notification');
      }
    } catch (error) {
      setError(`Error testing FCM: ${error.message}`);
    } finally {
      setStatus('');
    }
  };

  const copyToken = () => {
    if (fcmToken) {
      navigator.clipboard.writeText(fcmToken);
      setSuccess('FCM token copied to clipboard!');
    }
  };

  const clearToken = () => {
    setFcmToken('');
    setSuccess('FCM token cleared.');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'granted': return 'success';
      case 'denied': return 'error';
      case 'default': return 'warning';
      case 'registered': return 'success';
      case 'not-registered': return 'warning';
      case 'not-supported': return 'error';
      default: return 'info';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'granted':
      case 'registered': return <CheckCircle />;
      case 'denied':
      case 'not-supported': return <Error />;
      default: return <Info />;
    }
  };

  // Temporarily disable authentication check for testing
  console.log('FCMSetup component rendering, user:', user);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          <Notifications sx={{ mr: 2, verticalAlign: 'middle' }} />
          FCM Device Setup
        </Typography>
        <Button 
          variant="outlined" 
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </Button>
      </Box>
      
      <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
        Configure your device to receive push notifications for important updates
      </Typography>

      {/* Status Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Security color={getStatusColor(permission)} sx={{ mr: 1 }} />
              <Typography variant="h6">Notification Permission</Typography>
            </Box>
            <Chip 
              label={permission || 'Checking...'} 
              color={getStatusColor(permission)}
              icon={getStatusIcon(permission)}
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Settings color={getStatusColor(serviceWorkerStatus)} sx={{ mr: 1 }} />
              <Typography variant="h6">Service Worker</Typography>
            </Box>
            <Chip 
              label={serviceWorkerStatus || 'Checking...'} 
              color={getStatusColor(serviceWorkerStatus)}
              icon={getStatusIcon(serviceWorkerStatus)}
            />
          </CardContent>
        </Card>
      </Box>

      {/* Setup Instructions */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <PhoneAndroid sx={{ mr: 1, verticalAlign: 'middle' }} />
            Setup Instructions
          </Typography>
          
          <List>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Step 1: Grant Notification Permission"
                secondary="Click the button below to allow notifications from this website"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Step 2: Get FCM Token"
                secondary="Your device will receive a unique token for notifications"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Step 3: Test Notification"
                secondary="Verify that notifications are working properly"
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
        <Button
          variant="contained"
          size="large"
          onClick={requestNotificationPermission}
          disabled={isLoading || permission === 'granted'}
          startIcon={isLoading ? <CircularProgress size={20} /> : <Notifications />}
        >
          {permission === 'granted' ? 'Permission Granted' : 'Enable Notifications'}
        </Button>

        {permission === 'granted' && (
          <Button
            variant="outlined"
            size="large"
            onClick={getFCMToken}
            disabled={isLoading || fcmToken}
            startIcon={isLoading ? <CircularProgress size={20} /> : <Refresh />}
          >
            {fcmToken ? 'Token Obtained' : 'Get FCM Token'}
          </Button>
        )}
      </Box>

      {/* FCM Token Display */}
      {fcmToken && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              FCM Token
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={fcmToken}
              variant="outlined"
              InputProps={{ readOnly: true }}
              sx={{ mb: 2 }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<ContentCopy />}
                onClick={copyToken}
              >
                Copy Token
              </Button>
              <Button
                variant="outlined"
                color="warning"
                onClick={clearToken}
              >
                Clear Token
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Device Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Device Information
          </Typography>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Platform:</strong> {deviceInfo.platform}
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Language:</strong> {deviceInfo.language}
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Online:</strong> {deviceInfo.onLine ? 'Yes' : 'No'}
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Cookies:</strong> {deviceInfo.cookieEnabled ? 'Enabled' : 'Disabled'}
            </Typography>
          </Paper>
        </CardContent>
      </Card>

      {/* Status Messages */}
      {status && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {status}
        </Alert>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {success}
        </Alert>
      )}
    </Container>
  );
};

export default FCMSetup; 