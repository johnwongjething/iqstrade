import React, { useEffect, useState, useContext } from 'react';
import { Container, Typography, Box, Button, List, ListItem, ListItemText, Snackbar, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function UserApproval({ t = x => x }) {
  const [unapprovedUsers, setUnapprovedUsers] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const navigate = useNavigate();
  const { user, fetchUserIfNeeded, csrfToken } = useContext(UserContext);

  // Move fetchUnapprovedUsers to top-level so it can be reused
  const fetchUnapprovedUsers = async () => {
    const ok = await fetchUserIfNeeded();
    if (!ok || !user || !user.role) {
      setSnackbar({ open: true, message: t('authenticationRequired'), severity: 'error' });
      navigate('/login');
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/unapproved_users`, {
        credentials: 'include',
      });
      if (res.status === 401) {
        setSnackbar({ open: true, message: t('sessionExpired'), severity: 'error' });
        navigate('/login');
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setUnapprovedUsers(data);
      } else {
        setSnackbar({ open: true, message: t('failedToFetchUsers'), severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: t('failedToFetchUsers'), severity: 'error' });
    }
  };

  // Always call hooks at the top level
  useEffect(() => {
    fetchUnapprovedUsers();
    // eslint-disable-next-line
  }, [navigate]);

  const handleApprove = async (id) => {
    if (csrfToken === undefined) {
      setSnackbar({ open: true, message: t('securityTokenNotReady'), severity: 'error' });
      return;
    }
    const ok = await fetchUserIfNeeded();
    if (!ok || !user || !user.role) {
      setSnackbar({ open: true, message: t('authenticationRequired'), severity: 'error' });
      navigate('/login');
      return;
    }
    try {
      const headers = {};
      if (csrfToken) headers['X-CSRF-TOKEN'] = csrfToken;
      const res = await fetch(`${API_BASE_URL}/api/approve_user/${id}`, {
        method: 'POST',
        credentials: 'include',
        headers
      });
      if (res.ok) {
        setSnackbar({ open: true, message: t('userApprovedSuccessfully'), severity: 'success' });
        fetchUnapprovedUsers();
      } else {
        setSnackbar({ open: true, message: t('failedToApproveUser'), severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: t('failedToApproveUser'), severity: 'error' });
    }
  };

  // Conditional rendering for loading state
  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Button onClick={() => navigate('/dashboard')} variant="contained" color="primary" style={{ color: '#fff', marginBottom: 16 }}>
          {t('backToDashboard')}
        </Button>
        <Typography variant="h4" gutterBottom>{t('userApproval')}</Typography>
        <List>
          {unapprovedUsers.map((user) => (
            <ListItem key={user.id}>
              <ListItemText
                primary={user.username}
                secondary={
                  <>
                    <div>{t('email')}: {user.customer_email}</div>
                    <div>{t('companyName')}: {user.customer_name}</div>
                    <div>{t('phone')}: {user.customer_phone}</div>
                    <div>{t('role')}: {t(user.role)}</div>
                  </>
                }
              />
              <Button variant="contained" color="primary" onClick={() => handleApprove(user.id)}>
                {t('approve')}
              </Button>
            </ListItem>
          ))}
        </List>
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
}

export default UserApproval;