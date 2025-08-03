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
import { getFCMToken, messaging, vapidKey } from '../firebase';

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
  const [debugLogs, setDebugLogs] = useState([]); // Add debug logs state

  // Debug logging function
  const addDebugLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { timestamp, message, type };
    setDebugLogs(prev => [...prev.slice(-9), logEntry]); // Keep last 10 logs
  };

  // Add this at the beginning of the component to debug FCM setup
  useEffect(() => {
    addDebugLog('🔍 FCM Setup Debug - Starting...', 'info');
    addDebugLog(`🔍 Browser: ${navigator.userAgent}`, 'info');
    addDebugLog(`🔍 Service Worker Support: ${'serviceWorker' in navigator}`, 'info');
    addDebugLog(`🔍 Notification Support: ${'Notification' in window}`, 'info');
    addDebugLog(`🔍 Notification Permission: ${Notification.permission}`, 'info');
    
    // Check Firebase availability
    if (messaging) {
      addDebugLog('🔍 Firebase messaging available: YES', 'success');
    } else {
      addDebugLog('🔍 Firebase messaging NOT available', 'error');
    }
    
    // Check for any global errors
    window.addEventListener('error', (e) => {
      addDebugLog(`🔍 Global error caught: ${e.error}`, 'error');
    });
    
    window.addEventListener('unhandledrejection', (e) => {
      addDebugLog(`🔍 Unhandled promise rejection: ${e.reason}`, 'error');
    });
  }, []);

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
          await generateFCMToken();
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

  const generateFCMToken = async () => {
    setStatus('Getting FCM token...');
    addDebugLog('📱 Starting FCM token generation...', 'info');
    
    try {
      // Step 1: Check if Firebase is available
      if (!messaging) {
        addDebugLog('❌ Firebase messaging not available', 'error');
        throw new Error('Firebase messaging not available. Please check your internet connection.');
      }
      
      addDebugLog('✅ Firebase messaging available', 'success');
      
      // Step 2: Register service worker if not already registered
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
          addDebugLog('✅ Service worker registered successfully', 'success');
        } catch (swError) {
          addDebugLog(`⚠️ Service worker registration failed: ${swError.message}`, 'warning');
          // Continue anyway - some mobile browsers handle this differently
        }
      }
      
      // Step 3: Get FCM token with retry logic
      addDebugLog('📱 Requesting FCM token...', 'info');
      addDebugLog(`📱 VAPID key: ${vapidKey.substring(0, 20)}...`, 'info');
      addDebugLog(`📱 Service worker support: ${'serviceWorker' in navigator}`, 'info');
      
      let token = null;
      let retryCount = 0;
      const maxRetries = 3;
      
      while (!token && retryCount < maxRetries) {
        try {
          if (retryCount > 0) {
            addDebugLog(`📱 Retry ${retryCount} - waiting 2 seconds...`, 'info');
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
          
          addDebugLog(`📱 Attempt ${retryCount + 1} - calling getFCMToken()...`, 'info');
          
          // Use the imported getFCMToken function
          token = await getFCMToken();
          
          addDebugLog(`📱 Token obtained: ${token ? 'SUCCESS' : 'FAILED'}`, token ? 'success' : 'error');
          addDebugLog(`📱 Token length: ${token ? token.length : 0}`, 'info');
          addDebugLog(`📱 Token type: ${typeof token}`, 'info');
          
          if (token) {
            addDebugLog(`📱 Token preview: ${token.substring(0, 50)}...`, 'info');
            addDebugLog(`📱 Token ends with: ${token.substring(token.length - 20)}`, 'info');
            addDebugLog(`📱 Token contains ":" count: ${(token.match(/:/g) || []).length}`, 'info');
            break;
          } else {
            addDebugLog('📱 Token is null/undefined/empty', 'error');
          }
          
        } catch (error) {
          addDebugLog(`📱 Attempt ${retryCount + 1} failed: ${error.message}`, 'error');
          addDebugLog(`📱 Error name: ${error.name}`, 'error');
          retryCount++;
          
          if (retryCount >= maxRetries) {
            throw new Error(`Failed to get FCM token after ${maxRetries} attempts: ${error.message}`);
          }
        }
      }
      
      if (!token) {
        addDebugLog('❌ Could not obtain FCM token', 'error');
        throw new Error('Could not obtain FCM token. Please try again.');
      }
      
      addDebugLog('✅ FCM token obtained successfully', 'success');
      
      // Step 4: Save token to backend
      addDebugLog('📱 Saving token to backend...', 'info');
      const response = await fetch('/api/fcm/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
        credentials: 'include'
      });
      
      addDebugLog(`📱 Backend response status: ${response.status}`, 'info');
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (parseError) {
          console.error('📱 Could not parse error response:', parseError);
          const errorText = await response.text();
          console.error('📱 Raw error response:', errorText);
        }
        throw new Error(`Failed to save token: ${errorMessage}`);
      }
      
      let result;
      try {
        result = await response.json();
        console.log('📱 Token saved successfully:', result);
      } catch (parseError) {
        console.error('📱 Could not parse success response:', parseError);
        const responseText = await response.text();
        console.log('📱 Raw success response:', responseText);
        result = { message: 'Token saved (response not JSON)' };
      }
      
      // Step 5: Set token in state
      setFcmToken(token);
      setSuccess('FCM token obtained and saved successfully!');
      
      // Step 6: Test notification
      console.log('📱 Testing notification...');
      await testFCMToken(token);
      
    } catch (error) {
      console.error('📱 FCM token generation failed:', error);
      setError(`Error getting FCM token: ${error.message}`);
      
      // Show detailed error message for mobile debugging
      alert(`❌ FCM Setup Failed\n\nError: ${error.message}\n\nPlease try:\n1. Refresh the page\n2. Check your internet connection\n3. Try a different browser\n4. Make sure notifications are allowed`);
    } finally {
      setStatus('');
    }
  };

  const testFCMToken = async (token) => {
    setStatus('Testing FCM token...');
    console.log('📱 Testing FCM token...');
    
    try {
      const response = await fetch('/api/fcm/send/direct', {
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

      console.log('📱 Test response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('📱 Test result:', result);
        
        if (result.success) {
          setSuccess('✅ Test notification sent successfully! Check if you received it on your phone.');
          console.log('📱 Test notification sent successfully');
        } else {
          console.error('📱 Test failed:', result.error);
          setError(`Test failed: ${result.error || 'Unknown error'}`);
        }
      } else {
        const errorText = await response.text();
        console.error('📱 Test response error:', errorText);
        setError(`Failed to send test notification: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('📱 Test error:', error);
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
        {/* Mobile-Optimized Setup Button */}
        <Button
          variant="contained"
          size="large"
          color="primary"
          onClick={async () => {
            setIsLoading(true);
            try {
              // Step 1: Request permission
              if (permission !== 'granted') {
                await requestNotificationPermission();
              }
              
              // Step 2: Get FCM token
              if (permission === 'granted' && !fcmToken) {
                await generateFCMToken();
              }
            } catch (error) {
              console.error('📱 Mobile setup failed:', error);
            } finally {
              setIsLoading(false);
            }
          }}
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : <PhoneAndroid />}
          sx={{ 
            fontSize: '1.1rem', 
            py: 2,
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
          }}
        >
          {isLoading ? 'Setting up...' : '📱 Setup Phone Notifications'}
        </Button>

        {/* Individual Step Buttons */}
        <Divider sx={{ my: 2 }}>
          <Chip label="Or Setup Step by Step" />
        </Divider>

        <Button
          variant="outlined"
          size="large"
          onClick={requestNotificationPermission}
          disabled={isLoading || permission === 'granted'}
          startIcon={isLoading ? <CircularProgress size={20} /> : <Notifications />}
        >
          {permission === 'granted' ? 'Permission Granted' : 'Step 1: Enable Notifications'}
        </Button>

        {permission === 'granted' && (
                  <Button
          variant="outlined"
          size="large"
          onClick={generateFCMToken}
          disabled={isLoading || fcmToken}
          startIcon={isLoading ? <CircularProgress size={20} /> : <Refresh />}
        >
          {fcmToken ? 'Token Obtained' : 'Step 2: Get FCM Token'}
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

      {/* Debug Panel */}
      <Card sx={{ mt: 4, backgroundColor: '#f5f5f5' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            🔍 Debug Logs (Mobile-Friendly)
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
            {debugLogs.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                No debug logs yet. Start the setup process to see logs here.
              </Typography>
            ) : (
              debugLogs.map((log, index) => (
                <Box key={index} sx={{ mb: 1, p: 1, backgroundColor: 'white', borderRadius: 1 }}>
                  <Typography variant="caption" color="textSecondary">
                    {log.timestamp}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontFamily: 'monospace',
                      color: log.type === 'error' ? '#d32f2f' : 
                             log.type === 'success' ? '#2e7d32' : 
                             log.type === 'warning' ? '#ed6c02' : '#1976d2'
                    }}
                  >
                    {log.message}
                  </Typography>
                </Box>
              ))
            )}
          </Paper>
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setDebugLogs([])}
            >
              Clear Logs
            </Button>
            <Typography variant="caption" color="textSecondary" sx={{ alignSelf: 'center' }}>
              {debugLogs.length} logs
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default FCMSetup; 