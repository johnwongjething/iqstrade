import React from 'react';
import { Button, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function NotFound({ t = x => x }) {
  const navigate = useNavigate();
  return (
    <div style={{ textAlign: 'center', marginTop: 80 }}>
      <Typography variant="h2" color="error" gutterBottom>
        {t('notFoundTitle') || '404 - Page Not Found'}
      </Typography>
      <Typography variant="body1" gutterBottom>
        {t('notFoundMessage') || 'Sorry, the page you are looking for does not exist.'}
      </Typography>
      <Button variant="contained" color="primary" onClick={() => navigate('/')}
        style={{ marginTop: 24 }}>
        {t('goHome') || 'Go to Homepage'}
      </Button>
    </div>
  );
}