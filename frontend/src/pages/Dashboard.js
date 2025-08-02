import React, { useEffect, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Box, Typography, Stack } from '@mui/material';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';
import ProfileUpdateModal from '../components/ProfileUpdateModal';
import ChangePasswordModal from '../components/ChangePasswordModal';

function Dashboard({ t = x => x }) {
  const { user, setUser } = useContext(UserContext);
  const navigate = useNavigate();
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);

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
    navigate('/admin/dashboard');
  };

  // Profile update success handler
  const handleProfileUpdateSuccess = (updatedProfile) => {
    // Update user context with new profile data
    setUser(prev => ({
      ...prev,
      ...updatedProfile
    }));
  };

  // Password change success handler
  const handlePasswordChangeSuccess = () => {
    // User will be logged out automatically
    setUser(null);
  };

  return (
    <Box sx={{ my: 4, textAlign: 'center' }}>
      <Typography variant="h3" gutterBottom>
        {t('dashboard')}
      </Typography>
      <Typography variant="h6" gutterBottom>
        {t('welcome')}, {user.username} ({t(user.role)})
      </Typography>

      {/* Management Dashboard + Customer Emails + Import Bank Statement - only for user 'ray40' */}
      {user && user.username === 'ray40' && (
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 2 }}>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleGoToManagementDashboard}
          >
            {t('goToManagementDashboard')}
          </Button>
          <Button
            variant="contained"
            color="info"
            onClick={() => navigate('/customer-emails')}
          >
            {t('customerEmails')}
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/bank-import')}
          >
            {t('importBankStatement')}
          </Button>
        </Stack>
      )}

      {/* First Row - Primary Navigation */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        {user.role !== 'customer' && (
          <>
            <Button variant="contained" onClick={() => navigate('/review')}>{t('reviewBills')}</Button>
            <Button variant="contained" onClick={() => navigate('/staff-stats')}>{t('staffStats')}</Button>
            {/* Customer Emails button moved to top for ray40 */}
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

      {/* Third Row - Customer Profile Management */}
      {user.role === 'customer' && (
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => setProfileModalOpen(true)}
          >
            {t('updateProfile') || 'Update Profile'}
          </Button>
          <Button 
            variant="contained" 
            color="secondary"
            onClick={() => setPasswordModalOpen(true)}
          >
            {t('changePassword') || 'Change Password'}
          </Button>
        </Stack>
      )}

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

      {/* Fourth Row - Staff Tools */}
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ my: 2 }}>
        {user.role === 'staff' || user.role === 'admin' ? (
          <>
            <Button 
              variant="contained" 
              color="info"
              onClick={() => navigate('/fcm-setup')}
            >
              🔔 Setup Notifications
            </Button>
          </>
        ) : (
          <></>
        )}
      </Stack>

      {/* Bank Import button moved to top for ray40 */}

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

      {/* Modals */}
      <ProfileUpdateModal
        open={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        user={user}
        onSuccess={handleProfileUpdateSuccess}
      />

      <ChangePasswordModal
        open={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
        onSuccess={handlePasswordChangeSuccess}
      />
    </Box>
  );
}

export default Dashboard;