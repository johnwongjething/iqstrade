import React, { useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Box, Typography, Stack } from '@mui/material';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function Dashboard({ t = x => x }) {
  const { user, setUser } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      fetch(`${API_BASE_URL}/api/me`, { credentials: 'include' })
        .then(res => {
          if (res.status === 401) {
            navigate('/login');
            return null;
          }
          return res.json();
        })
        .then(data => {
          if (data && !data.error) setUser(data);
        });
    }
  }, [user, setUser, navigate]);

  const handleLogout = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    if (response.ok) {
      setUser(null);
      navigate('/login');
    }
  } catch (err) {
    setUser(null);
    navigate('/login');
  }
};
  
  if (!user) return null; // or loading spinner

  // Management Dashboard navigation button
  const handleGoToManagementDashboard = () => {
    console.log('Navigating to Management Dashboard');
    navigate('/admin/dashboard');
  };

  return (
    <Box sx={{ my: 4, textAlign: 'center' }}>
      <Typography variant="h3" gutterBottom>
        {t('dashboard')}
      </Typography>
      <Typography variant="h6" gutterBottom>
        {t('welcome')}, {user.username} ({t(user.role)})
      </Typography>

      {/* Management Dashboard Button - only for user 'ray40' */}
      {user && user.username === 'ray40' && (
        <Button
          variant="contained"
          color="secondary"
          sx={{ mb: 2 }}
          onClick={handleGoToManagementDashboard}
        >
          Go to Management Dashboard
        </Button>
      )}

      {/* First Row - Primary Navigation */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        {user.role !== 'customer' && (
          <>
            <Button variant="contained" onClick={() => navigate('/review')}>{t('reviewBills')}</Button>
            <Button variant="contained" onClick={() => navigate('/staff-stats')}>{t('staffStats')}</Button>
          </>
        )}
        <Button variant="contained" onClick={() => navigate('/search')}>{t('billSearch')}</Button>
      </Stack>
      </Stack>

      {/* Second Row - Document Management */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        {user.role !== 'customer' && (
          <>
            <Button variant="contained" onClick={() => navigate('/edit-delete-bills')}>{t('editDeleteBills')}</Button>
            <Button variant="contained" onClick={() => navigate('/account-page')}>{t('accountPage')}</Button>
          </>
        )}
        <Button variant="contained" onClick={() => navigate('/upload')}>{t('uploadBill')}</Button>
      </Stack>

      {/* Third Row - User Management */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        {user.role === 'staff' || user.role === 'admin' ? (
          <>
            <Button variant="contained" onClick={() => navigate('/register')}>{t('registerUser')}</Button>
            <Button variant="contained" onClick={() => navigate('/user-approval')}>{t('userApproval')}</Button>
            <Button variant="contained" onClick={() => navigate('/accounting-review')}>{t('accountSettlement')}</Button>
          </>
        ) : (
          <></>
        )}
      </Stack>

      {/* Bank Import Row - only for user 'ray40' */}
      {user && user.username === 'ray40' && (
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
          <Button variant="contained" color="primary" onClick={() => navigate('/bank-import')}>
            Import Bank Statement
          </Button>
        </Stack>
      )}

      {/* Logout button */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 4 }}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleLogout}
        >
          {t('logout')}
        </Button>
      </Stack>
    </Box>
  );
}

export default Dashboard;