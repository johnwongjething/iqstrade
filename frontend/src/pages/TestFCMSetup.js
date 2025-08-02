import React from 'react';
import { Container, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const TestFCMSetup = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🔔 FCM Setup Test Page
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        This is a test page to verify routing is working.
      </Typography>
      
      <Button 
        variant="contained" 
        onClick={() => navigate('/dashboard')}
      >
        Back to Dashboard
      </Button>
    </Container>
  );
};

export default TestFCMSetup; 