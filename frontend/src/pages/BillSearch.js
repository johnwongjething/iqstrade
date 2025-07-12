import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, TextField, Button, Snackbar, Alert,
  Table, TableHead, TableBody, TableRow, TableCell
} from '@mui/material';
import { API_BASE_URL } from '../config';
import LoadingModal from '../components/LoadingModal';
import { UserContext } from '../UserContext';

export default function BillSearch({ t = x => x }) {
  const [form, setForm] = useState({
    unique_number: '',
    bl_number: '',
    customer_name: ''
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [tokenTimeout, setTokenTimeout] = useState(false);
  const navigate = useNavigate();
  const { user, fetchUserIfNeeded, csrfToken } = useContext(UserContext);

  // Move checkUser to a regular function
  async function checkUser() {
    const ok = await fetchUserIfNeeded();
    if (!ok || !user || !user.role) {
      setSnackbar({ open: true, message: 'Authentication required. Please log in again.', severity: 'error' });
      navigate('/login');
      return false;
    }
    if (user.role === 'customer') {
      handleSearch(user.username, user.role);
    }
    return true;
  }

  // Only run checkUser after user is loaded
  useEffect(() => {
    if (!user) return;
    checkUser();
    // eslint-disable-next-line
  }, [user, navigate]);

  useEffect(() => {
    if (csrfToken !== null) {
      setTokenTimeout(false);
      return;
    }
    const timer = setTimeout(() => setTokenTimeout(true), 8000); // 8 seconds
    return () => clearTimeout(timer);
  }, [csrfToken]);

  function handleSessionReset() {
    document.cookie.split(';').forEach(c => {
      document.cookie = c
        .replace(/^ +/, '')
        .replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
    });
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  }

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSearch = async (usernameOverride, roleOverride) => {
    // Only require CSRF if present
    if (csrfToken === undefined) {
      setSnackbar({ open: true, message: 'Security token not ready. Please wait and try again.', severity: 'error' });
      return;
    }
    setLoading(true);
    let searchForm = { ...form };
    const roleToUse = roleOverride || user.role;
    const usernameToUse = usernameOverride || user.username;
    if (roleToUse === 'customer') {
      searchForm.username = usernameToUse;
    }
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (csrfToken) headers['X-CSRF-TOKEN'] = csrfToken;
      const res = await fetch(`${API_BASE_URL}/api/search_bills`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify(searchForm)
      });
      if (res.status === 401) {
        setSnackbar({ open: true, message: 'Session expired. Please log in again.', severity: 'error' });
        navigate('/login');
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      } else {
        setSnackbar({ open: true, message: t('failedToFetchBills'), severity: 'error' });
      }
    } catch (err) {
      setSnackbar({ open: true, message: t('failedToFetchBills'), severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setForm({
      unique_number: '',
      bl_number: '',
      customer_name: ''
    });
    setResults([]);
  };

  const getStatus = (record) => {
    if (record.status === t('invoiceSent')) return t('invoiceSent');
    if (record.status === t('awaitingBankIn')) return t('awaitingBankIn');
    if (record.status === t('paidAndCtnValid')) return t('paidAndCtnValid');
    if (record.status === t('pending')) return t('pending');
    if (record.status === 'Completed') return t('paidAndCtnValid');
    return record.status || t('pending');
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  };

  // Conditional rendering for loading state
  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <Container maxWidth="md" sx={{ py: { xs: 2, sm: 4 } }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-start' }}>
        <Button onClick={() => navigate('/dashboard')} variant="contained" color="primary">
          {t('backToDashboard')}
        </Button>
      </Box>
      <Typography variant="h4" align="center" gutterBottom>
        {t('yourBills')}
      </Typography>

      {user.role !== 'customer' && (
        <Box
          component="form"
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 2,
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2
          }}
          onSubmit={e => { e.preventDefault(); handleSearch(); }}
        >
          <TextField
            label={t('ctnNumber')}
            name="unique_number"
            value={form.unique_number}
            onChange={handleChange}
            size="small"
          />
          <TextField
            label={t('billOfLadingNumber')}
            name="bl_number"
            value={form.bl_number}
            onChange={handleChange}
            size="small"
          />
          <TextField
            label={t('customerName')}
            name="customer_name"
            value={form.customer_name}
            onChange={handleChange}
            size="small"
          />
          <Button variant="contained" color="primary" type="submit" disabled={loading}>
            {t('search')}
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleClear} disabled={loading}>
            {t('clear')}
          </Button>
        </Box>
      )}

      <Box sx={{ overflowX: 'auto', mt: 2 }}>
        <Table size="small" sx={{
          minWidth: 600,
          '& th, & td': {
            whiteSpace: { xs: 'nowrap', sm: 'normal' },
            fontSize: { xs: '0.85rem', sm: '1rem' },
            px: { xs: 1, sm: 2 },
            py: { xs: 0.5, sm: 1 }
          }
        }}>
          <TableHead>
            <TableRow>
              <TableCell>{t('ctnNumber')}</TableCell>
              <TableCell>{t('billOfLadingNumber')}</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{t('customerName')}</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{t('containerNo')}</TableCell>
              <TableCell>{t('status')}</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{t('createdAt')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map(row => (
              <TableRow key={row.id}>
                <TableCell>{row.unique_number}</TableCell>
                <TableCell>{row.bl_number}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{row.customer_name}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{row.container_numbers}</TableCell>
                <TableCell>{getStatus(row)}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{formatDate(row.created_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      <LoadingModal 
        open={loading} 
        message={t('loadingData')} 
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}