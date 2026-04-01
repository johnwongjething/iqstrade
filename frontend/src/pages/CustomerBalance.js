import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const CustomerBalance = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Customer Balance Management - TEST
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This is a test page to verify the route is working.
        </Typography>
      </Box>
    </Container>
  );
};

export default CustomerBalance; 