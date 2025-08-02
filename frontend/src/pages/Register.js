import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

function Register({ t = x => x }) {
  const initialFormData = {
    username: '',
    password: '',
    role: 'customer',
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    confirm_email: '',
  };
  const [formData, setFormData] = useState(initialFormData);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [validationErrors, setValidationErrors] = useState({});
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState(null);
  const [emailAvailable, setEmailAvailable] = useState(null);
  const navigate = useNavigate();

  // Debounced validation functions
  const checkUsernameAvailability = async (username) => {
    if (!username || username.length < 3) {
      setUsernameAvailable(null);
      return;
    }
    
    setIsCheckingUsername(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/check-username`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      const data = await response.json();
      setUsernameAvailable(data.available);
    } catch (error) {
      setUsernameAvailable(null);
    } finally {
      setIsCheckingUsername(false);
    }
  };

  const checkEmailAvailability = async (email) => {
    if (!email || !email.includes('@')) {
      setEmailAvailable(null);
      return;
    }
    
    setIsCheckingEmail(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/check-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await response.json();
      setEmailAvailable(data.available);
    } catch (error) {
      setEmailAvailable(null);
    } finally {
      setIsCheckingEmail(false);
    }
  };

  // Debounced effect for username validation
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      checkUsernameAvailability(formData.username);
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [formData.username]);

  // Debounced effect for email validation
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      checkEmailAvailability(formData.customer_email);
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [formData.customer_email]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    
    // Clear validation errors when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Client-side validation
    const errors = {};
    
    if (formData.confirm_email && formData.customer_email !== formData.confirm_email) {
      errors.confirm_email = t('emailMismatch') || 'Email addresses do not match';
    }
    
    if (usernameAvailable === false) {
      errors.username = 'Username is already taken';
    }
    
    if (emailAvailable === false) {
      errors.customer_email = 'Email is already taken';
    }
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok) {
        setSnackbar({ open: true, message: data.message, severity: 'success' });
        await fetch(`${API_BASE_URL}/api/notify_new_user`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: formData.username,
            email: formData.customer_email,
            role: formData.role,
          }),
        });
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setSnackbar({ open: true, message: data.error, severity: 'error' });
      }
    } catch (err) {
      setSnackbar({ open: true, message: t('registrationFailed') || 'Registration failed', severity: 'error' });
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4, p: { xs: 2, sm: 4 }, boxShadow: 2, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          {t('register')}
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label={t('username')}
            name="username"
            value={formData.username}
            onChange={handleChange}
            margin="normal"
            required
            error={!!validationErrors.username || usernameAvailable === false}
            helperText={
              validationErrors.username || 
              (usernameAvailable === false ? 'Username is already taken' : '') ||
              (usernameAvailable === true ? 'Username is available' : '') ||
              (isCheckingUsername ? 'Checking availability...' : '')
            }
            InputProps={{
              endAdornment: isCheckingUsername ? (
                <CircularProgress size={20} />
              ) : usernameAvailable === true ? (
                <span style={{ color: 'green' }}>✓</span>
              ) : usernameAvailable === false ? (
                <span style={{ color: 'red' }}>✗</span>
              ) : null
            }}
          />
          <TextField
            fullWidth
            label={t('password')}
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
          />
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {t('passwordRequirement') ||
              'Password must be at least 8 characters, include an uppercase letter, a lowercase letter, a number, and a special character.'}
          </Typography>
          <FormControl fullWidth margin="normal" required>
            <InputLabel id="role-label">{t('role')}</InputLabel>
            <Select
              labelId="role-label"
              id="role"
              name="role"
              value={formData.role}
              label={t('role')}
              onChange={handleChange}
            >
              <MenuItem value="customer">{t('customer')}</MenuItem>
              <MenuItem value="staff">{t('staff')}</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label={t('customerName')}
            name="customer_name"
            value={formData.customer_name}
            onChange={handleChange}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label={t('email')}
            name="customer_email"
            type="email"
            value={formData.customer_email}
            onChange={handleChange}
            margin="normal"
            required
            error={!!validationErrors.customer_email || emailAvailable === false}
            helperText={
              validationErrors.customer_email || 
              (emailAvailable === false ? 'Email is already taken' : '') ||
              (emailAvailable === true ? 'Email is available' : '') ||
              (isCheckingEmail ? 'Checking availability...' : '')
            }
            InputProps={{
              endAdornment: isCheckingEmail ? (
                <CircularProgress size={20} />
              ) : emailAvailable === true ? (
                <span style={{ color: 'green' }}>✓</span>
              ) : emailAvailable === false ? (
                <span style={{ color: 'red' }}>✗</span>
              ) : null
            }}
          />
          <TextField
            fullWidth
            label={t('confirmEmail') || 'Confirm Email Address'}
            name="confirm_email"
            type="email"
            value={formData.confirm_email}
            onChange={handleChange}
            margin="normal"
            required
            error={!!validationErrors.confirm_email}
            helperText={validationErrors.confirm_email}
          />
          <TextField
            fullWidth
            label={t('phoneNumber')}
            name="customer_phone"
            value={formData.customer_phone}
            onChange={handleChange}
            margin="normal"
            required
          />
          <Button type="submit" variant="contained" color="primary" sx={{ mt: 2 }} fullWidth>
            {t('register')}
          </Button>
        </form>
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

export default Register;

// No changes needed for registration endpoint, as it is public.
// If you add any protected fetches, use credentials: 'include'.