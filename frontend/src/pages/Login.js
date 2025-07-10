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
        // Always return a static mock Geetest challenge for demo
        const data = {
          gt: 'demo_gt_id',
          challenge: 'demo_challenge',
          success: 1
        };
        if (window.initGeetest4) {
          window.initGeetest4(
            {
              captchaId: data.gt,
              product: 'float',
              language: 'en'
            },
            (captchaObj) => {
              setGeetestObj(captchaObj);
              captchaObj.appendTo(geetestRef.current);
              captchaObj.onReady(() => {});
              captchaObj.onSuccess(() => {
                // Always set mock Geetest data for demo
                setGeetestData({
                  lot_number: 'demo_lot',
                  captcha_output: 'demo_output',
                  pass_token: 'demo_token'
                });
              });
              captchaObj.onError(() => {
                setError('Geetest failed to load.');
              });
            }
          );
        }
      } catch (err) {
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