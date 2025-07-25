import React, { useEffect, useState, useContext } from 'react';
import { Container, Typography, Box, Grid, Paper, Button, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Link } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';

function StaffStats({ t = x => x }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [outstanding, setOutstanding] = useState([]);
  const [loadingOutstanding, setLoadingOutstanding] = useState(true);
  const navigate = useNavigate();
  const { user, fetchUserIfNeeded, csrfToken } = useContext(UserContext);

  useEffect(() => {
    // Ensure user is loaded and authenticated
    const checkUser = async () => {
      const ok = await fetchUserIfNeeded();
      if (!ok || !user || !user.role) {
        setError(t('authenticationRequired'));
        navigate('/login');
        return false;
      }
      return true;
    };
    const fetchStats = async () => {
      setLoading(true);
      setError(null);
      if (!(await checkUser())) return;
      try {
        const res = await fetch(`${API_BASE_URL}/api/stats/summary`, {
          credentials: 'include',
        });
        if (res.status === 401) {
          setError(t('sessionExpired'));
          navigate('/login');
          return;
        }
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        } else {
          setError(t('failedToFetchStats'));
        }
      } catch (err) {
        setError(t('failedToFetchStats'));
      }
      setLoading(false);
    };
    fetchStats();
    // eslint-disable-next-line
  }, [t, navigate]);

  useEffect(() => {
    const fetchOutstanding = async () => {
      setLoadingOutstanding(true);
      if (!user || !user.role) {
        navigate('/login');
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/stats/outstanding_bills`, {
          credentials: 'include',
        });
        if (res.status === 401) {
          navigate('/login');
          return;
        }
        if (res.ok) {
          const data = await res.json();
          setOutstanding(data);
        }
      } catch (err) {
        // ignore
      }
      setLoadingOutstanding(false);
    };
    fetchOutstanding();
    // eslint-disable-next-line
  }, [user, navigate]);

  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Button onClick={() => navigate('/dashboard')} variant="contained" color="primary" style={{ color: '#fff', marginBottom: 16 }}>
          {t('backToDashboard')}
        </Button>
        <Typography variant="h3" component="h1" gutterBottom>
          {t('staffStats')}
        </Typography>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
        ) : error ? (
          <Alert severity="error" sx={{ mt: 4 }}>{error}</Alert>
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('totalBills')}
                </Typography>
                <Typography variant="h4">{stats.total_bills}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('completedBills')}
                </Typography>
                <Typography variant="h4">{stats.completed_bills}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('pendingBills')}
                </Typography>
                <Typography variant="h4">{stats.pending_bills}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('totalInvoiceAmount')}
                </Typography>
                <Typography variant="h4">{stats.total_invoice_amount}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('totalPaymentReceived')}
                </Typography>
                <Typography variant="h4">{stats.total_payment_received}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {t('totalPaymentOutstanding')}
                </Typography>
                <Typography variant="h4">{stats.total_payment_outstanding}</Typography>
              </Paper>
            </Grid>
          </Grid>
        )}
        <Box sx={{ mt: 6 }}>
          <Typography variant="h5" gutterBottom>{t('outstandingPayments')}</Typography>
          {loadingOutstanding ? (
            <CircularProgress />
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('id')}</TableCell>
                    <TableCell>{t('customerName')}</TableCell>
                    <TableCell>{t('blNumber')}</TableCell>
                    <TableCell>{t('ctnFee')}</TableCell>
                    <TableCell>{t('serviceFee')}</TableCell>
                    <TableCell>{t('total')}</TableCell>
                    <TableCell>{t('outstanding')}</TableCell> {/* 🔹 Add this */}
                    <TableCell>{t('invoicePDF')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {outstanding.sort((a, b) => a.id - b.id).map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>{row.id}</TableCell>
                      <TableCell>{row.customer_name}</TableCell>
                      <TableCell>{row.bl_number}</TableCell>
                      {/* CTN Fee */}
                      <TableCell>
                        ${row.ctn_fee ? Number(row.ctn_fee).toFixed(2) : '0.00'}
                      </TableCell>
                      {/* Service Fee */}
                      <TableCell>
                        ${row.service_fee ? Number(row.service_fee).toFixed(2) : '0.00'}
                      </TableCell>
                      {/* Total Invoice Amount (Full amount: CTN + Service) */}
                      <TableCell>
                        ${(
                          (Number(row.ctn_fee) || 0) +
                          (Number(row.service_fee) || 0)
                        ).toFixed(2)}
                      </TableCell>
                      {/* Outstanding Amount (Adjusted: 15% if Allinpay Unsettled) */}
                      <TableCell>
                        ${row.outstanding_amount !== undefined
                          ? Number(row.outstanding_amount).toFixed(2)
                          : (
                              (Number(row.ctn_fee) || 0) +
                              (Number(row.service_fee) || 0)
                            ).toFixed(2)
                        }
                      </TableCell>
                  {/* Invoice PDF Link */}
                  <TableCell>
                    {row.invoice_filename ? (
                      <Link
                        href={row.invoice_filename}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => console.log('[DEBUG] Opening invoice Cloudinary URL:', row.invoice_filename)}
                      >
                        {t('viewPDF')}
                      </Link>
                    ) : 'N/A'}
                  </TableCell>
                    </TableRow>
                  ))}
                </TableBody>

              </Table>
            </TableContainer>
          )}
        </Box>
      </Box>
    </Container>
  );
}

export default StaffStats;