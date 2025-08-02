import React, { useState, useEffect, useContext } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
  Box,
  Typography
} from '@mui/material';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function ProfileUpdateModal({ open, onClose, user, onSuccess }) {
  const { csrfToken } = useContext(UserContext);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Initialize form data when user data is available
  useEffect(() => {
    if (user) {
      setFormData({
        customer_name: user.customer_name || '',
        customer_email: user.customer_email || '',
        customer_phone: user.customer_phone || ''
      });
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear errors when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.customer_name.trim()) {
      setError('Customer name is required');
      return false;
    }
    if (!formData.customer_email.trim()) {
      setError('Email is required');
      return false;
    }
    // Basic email validation
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(formData.customer_email)) {
      setError('Please enter a valid email address');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (csrfToken) {
        headers['X-CSRF-TOKEN'] = csrfToken;
      }
      
      const response = await fetch(`${API_BASE_URL}/api/update-profile`, {
        method: 'PUT',
        headers,
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Profile updated successfully!');
        if (onSuccess) {
          onSuccess(data.profile);
        }
        // Close modal after 2 seconds
        setTimeout(() => {
          onClose();
          setSuccess('');
        }, 2000);
      } else {
        setError(data.error || 'Failed to update profile');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError('');
    setSuccess('');
    setLoading(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Update Profile</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Username: <strong>{user?.username}</strong>
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Role: <strong>{user?.role}</strong>
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          <TextField
            fullWidth
            label="Full Name"
            name="customer_name"
            value={formData.customer_name}
            onChange={handleChange}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Email Address"
            name="customer_email"
            type="email"
            value={formData.customer_email}
            onChange={handleChange}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Phone Number"
            name="customer_phone"
            value={formData.customer_phone}
            onChange={handleChange}
            margin="normal"
            disabled={loading}
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
          >
            {loading ? 'Updating...' : 'Update Profile'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default ProfileUpdateModal; 