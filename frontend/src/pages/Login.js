import React, { useState, useContext, useEffect, useRef } from 'react';
import { Container, Typography, Box, TextField, Button, Snackbar, Alert } from '@mui/material';
import { useNavigate, Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function fetchWithTimeout(resource, options = {}, timeout = 15000) {
  return Promise.race([
    fetch(resource, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Request timed out')), timeout))
  ]);
}

function Login({ t = x => x }) {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [scriptReady, setScriptReady] = useState(false);
  const [geetestData, setGeetestData] = useState(null);
  const geetestContainerRef = useRef(null);
  const geetestWidgetRef = useRef(null);
  const navigate = useNavigate();
  const { fetchCsrfToken, fetchUserIfNeeded } = useContext(UserContext);

  // Effect 1: Load the Geetest script once.
  useEffect(() => {
    const scriptId = 'geetest-script';
    if (document.getElementById(scriptId)) {
      setScriptReady(true);
      return;
    }
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://static.geetest.com/v4/gt4.js';
    script.async = true;
    script.onload = () => setScriptReady(true);
    document.body.appendChild(script);
  }, []);

  // Effect 2: Initialize the widget when the script is ready.
  useEffect(() => {
    if (!scriptReady || geetestWidgetRef.current) {
      return;
    }

    fetch(`${API_BASE_URL}/api/geetest/register`)
      .then(res => res.json())
      .then(data => {
        if (window.initGeetest4) {
          window.initGeetest4(
            {
              captchaId: data.gt,
              challenge: data.challenge,
              product: 'float',
              language: 'en',
            },
            (captcha) => {
              geetestWidgetRef.current = captcha;
              if (geetestContainerRef.current) {
                captcha.appendTo(geetestContainerRef.current);
              }
              captcha.onSuccess(() => {
                const result = captcha.getValidate();
                setGeetestData(result);
              });
              captcha.onError(() => {
                setError('Geetest failed to load.');
              });
            }
          );
        }
      })
      .catch(() => {
        setError('Failed to load Geetest.');
      });

    return () => {
      if (geetestWidgetRef.current) {
        geetestWidgetRef.current.destroy();
        geetestWidgetRef.current = null;
      }
    };
  }, [scriptReady]);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    if (!geetestData || !geetestData.lot_number || !geetestData.captcha_output || !geetestData.pass_token) {
      setError('Please complete the CAPTCHA');
      setLoading(false);
      return;
    }
    try {
      // Send Geetest v4 fields as top-level keys for backend compatibility
      const body = {
        ...formData,
        ...geetestData
      };
      // Submitting login
      const res = await fetchWithTimeout(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'include'
      });
      let data;
      try {
        data = await res.json();
      } catch {
        data = {};
      }
      // Login response received
      if (res.ok) {
        const success = await fetchUserIfNeeded(true);
        if (success) {
          await fetchCsrfToken();
          navigate('/dashboard');
        } else {
          setError(t('loginFailed') || 'Login failed');
        }
      } else {
        setError(data.error || t('loginFailed') || 'Login failed');
        setGeetestData(null);
        if (geetestWidgetRef.current) {
            geetestWidgetRef.current.reset();
        }
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(t('loginFailed') + ': ' + err.message);
      setGeetestData(null);
      if (geetestWidgetRef.current) {
        geetestWidgetRef.current.reset();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4, p: { xs: 2, sm: 4 }, boxShadow: 2, borderRadius: 2 }}>
        <Typography variant="h4" align="center" gutterBottom>{t('login')}</Typography>
        <form onSubmit={handleSubmit}>
          <TextField fullWidth label={t('username')} name="username" value={formData.username} onChange={handleChange} margin="normal" required />
          <TextField fullWidth label={t('password')} name="password" type="password" value={formData.password} onChange={handleChange} margin="normal" required />
          <Box sx={{ mt: 2, mb: 2, display: 'flex', justifyContent: 'center' }}>
            <div ref={geetestContainerRef} style={{ width: 300, minHeight: 60 }} />
          </Box>
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }} disabled={loading || !geetestData}>
            {loading ? t('loading') || 'Loading...' : t('login')}
          </Button>
        </form>
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Link to="/forgot-password" style={{ textDecoration: 'none', color: '#1976d2' }}>{t('forgotPassword')}</Link>
          <Link to="/forgot-username" style={{ textDecoration: 'none', color: '#1976d2' }}>{t('forgotUsername')}</Link>
        </Box>
        <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError('')} anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
          <Alert onClose={() => setError('')} severity="error" sx={{ width: '100%' }}>{error}</Alert>
        </Snackbar>
      </Box>
    </Container>
  );
}

export default Login;