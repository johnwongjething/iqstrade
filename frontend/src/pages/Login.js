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
  const [geetestReady, setGeetestReady] = useState(false);
  const [geetestObj, setGeetestObj] = useState(null);
  const [geetestData, setGeetestData] = useState(null);
  const geetestRef = useRef();
  const navigate = useNavigate();
  const { setUser, fetchCsrfToken, fetchUserIfNeeded } = useContext(UserContext);

  // Dynamically load Geetest script
  useEffect(() => {
    const scriptId = 'geetest-script';
    if (document.getElementById(scriptId)) return;
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://static.geetest.com/v4/gt4.js';
    script.async = true;
    script.onload = () => setGeetestReady(true);
    document.body.appendChild(script);
    return () => {
      if (document.getElementById(scriptId)) {
        document.body.removeChild(document.getElementById(scriptId));
      }
    };
  }, []);

  // Fetch Geetest challenge and render widget
  useEffect(() => {
    if (!geetestReady) return;
    async function initGeetest() {
      try {
        // Fetch real Geetest challenge from backend
        const res = await fetch(`${API_BASE_URL}/api/geetest/register`);
        const data = await res.json();
        console.log('Geetest /register response:', data); // Debug
        if (window.initGeetest4) {
          window.initGeetest4(
            {
              captchaId: data.gt,
              challenge: data.challenge, // Pass challenge from backend
              product: 'float',
              language: 'en'
            },
            (captchaObj) => {
              setGeetestObj(captchaObj);
              captchaObj.appendTo(geetestRef.current);
              captchaObj.onReady(() => {
                console.log('Geetest widget ready');
              });
              captchaObj.onSuccess(() => {
                // Get real Geetest data from widget
                const result = captchaObj.getValidate();
                console.log('Geetest widget validate result:', result); // Debug
                setGeetestData({
                  lot_number: result.lot_number,
                  captcha_output: result.captcha_output,
                  pass_token: result.pass_token
                });
              });
              captchaObj.onError((err) => {
                console.error('Geetest widget error:', err);
                setError('Geetest failed to load.');
              });
            }
          );
        } else {
          console.error('window.initGeetest4 not found');
        }
      } catch (err) {
        console.error('Failed to load Geetest:', err);
        setError('Failed to load Geetest.');
      }
    }
    initGeetest();
  }, [geetestReady]);

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
        lot_number: geetestData.lot_number,
        captcha_output: geetestData.captcha_output,
        pass_token: geetestData.pass_token
      };
      console.log('Submitting login with body:', body); // Debug
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
      console.log('Login response:', data); // Debug
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
        if (geetestObj) geetestObj.reset && geetestObj.reset();
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(t('loginFailed') + ': ' + err.message);
      setGeetestData(null);
      if (geetestObj) geetestObj.reset && geetestObj.reset();
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
            <div ref={geetestRef} style={{ width: 300, minHeight: 60 }} />
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