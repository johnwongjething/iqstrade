import React, { useState, useContext } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
  Typography,
  Box
} from '@mui/material';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function ChangePasswordModal({ open, onClose, onSuccess }) {
  const { csrfToken } = useContext(UserContext);
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear errors when user starts typing
    if (error) setError('');
  };

  const validatePassword = (password) => {
    const errors = [];
    
    if (password.length < 8) {
      errors.push('At least 8 characters');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('One uppercase letter');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('One lowercase letter');
    }
    if (!/\d/.test(password)) {
      errors.push('One number');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('One special character');
    }
    
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.current_password || !formData.new_password || !formData.confirm_password) {
      setError('All fields are required');
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError('New password and confirmation do not match');
      return;
    }

    const passwordErrors = validatePassword(formData.new_password);
    if (passwordErrors.length > 0) {
      setError(`Password requirements not met: ${passwordErrors.join(', ')}`);
      return;
    }

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
      
      const response = await fetch(`${API_BASE_URL}/api/change-password`, {
        method: 'PUT',
        headers,
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Password changed successfully! You will be logged out.');
        if (onSuccess) {
          onSuccess();
        }
        // Close modal and logout after 3 seconds
        setTimeout(() => {
          onClose();
          // Redirect to login
          window.location.href = '/login';
        }, 3000);
      } else {
        setError(data.error || 'Failed to change password');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      current_password: '',
      new_password: '',
      confirm_password: ''
    });
    setError('');
    setSuccess('');
    setLoading(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Change Password</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
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
            label="Current Password"
            name="current_password"
            type="password"
            value={formData.current_password}
            onChange={handleChange}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="New Password"
            name="new_password"
            type="password"
            value={formData.new_password}
            onChange={handleChange}
            margin="normal"
            required
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Confirm New Password"
            name="confirm_password"
            type="password"
            value={formData.confirm_password}
            onChange={handleChange}
            margin="normal"
            required
            disabled={loading}
          />

          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              <strong>Password Requirements:</strong>
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Password must be at least 8 characters, include an uppercase letter, a lowercase letter, a number, and a special character.
            </Typography>
          </Box>
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
            {loading ? 'Changing...' : 'Change Password'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default ChangePasswordModal; 