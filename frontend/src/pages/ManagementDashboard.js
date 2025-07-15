import React, { useEffect, useState, useContext } from 'react';
import { Container, Typography, Paper, Box, Table, TableHead, TableRow, TableCell, TableBody, CircularProgress, Alert, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';
import UnmatchedBankRecords from './UnmatchedBankRecords';

function ManagementDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [ingestErrors, setIngestErrors] = useState([]);
  const [ingestLoading, setIngestLoading] = useState(false);
  const { csrfToken } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    let intervalId;
    const fetchData = async () => {
      console.log('[DEBUG] Polling: fetching management overview');
      try {
        const res = await fetch(`${API_BASE_URL}/api/management/overview`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const json = await res.json();
        if (res.ok) {
          setData(json);
          console.log("[DEBUG] Management overview data:", json);
        } else {
          setError(json.error || "Failed to load");
        }
      } catch (e) {
        setError("Failed to load");
      } finally {
        setLoading(false);
      }
    };
    const fetchIngestErrors = async () => {
      setIngestLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const errors = await res.json();
        setIngestErrors(errors);
        console.log('[DEBUG] Fetched ingest errors', errors);
      } catch (e) {
        setIngestErrors([]);
      } finally {
        setIngestLoading(false);
      }
    };
    fetchData();
    fetchIngestErrors();
    intervalId = setInterval(fetchData, 10000); // 10 seconds
    return () => {
      clearInterval(intervalId);
      console.log('[DEBUG] Polling interval cleared');
    };
  }, [csrfToken]);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  // Debug log for rendering
  console.log('[DEBUG] Rendering ManagementDashboard', data);

  // Metrics section
  const metrics = data.metrics || {};

  return (
    <Container>
      {/* Back To Dashboard button, top left */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', mb: 2 }}>
        <Button variant="contained" color="primary" onClick={() => navigate('/dashboard')}>
          Back To Dashboard
        </Button>
      </Box>
      <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

      {/* Metrics Section */}
      <Box sx={{ my: 2 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">System Metrics</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Box> <strong>Total B/L records:</strong> {metrics.total_bills} </Box>
            <Box> <strong>Pending:</strong> {metrics.pending_bills} </Box>
            <Box> <strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in} </Box>
            <Box> <strong>Completed:</strong> {metrics.completed_bills} </Box>
            <Box> <strong>Paid:</strong> {metrics.paid_bills} </Box>
            <Box> <strong>Sum of invoice amounts:</strong> {metrics.sum_invoice_amount} </Box>
            <Box> <strong>Sum of paid:</strong> {metrics.sum_paid_amount} </Box>
            <Box> <strong>Sum of outstanding:</strong> {metrics.sum_outstanding_amount} </Box>
          </Box>
        </Paper>
      </Box>

      <Box sx={{ my: 2 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">OCR Issues</Typography>
          <pre>{JSON.stringify(data.flags.ocr_missing, null, 2)}</pre>
        </Paper>
      </Box>

      <Box sx={{ my: 2 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">Email Ingestion Errors</Typography>
          <Button variant="outlined" size="small" onClick={async () => {
            setIngestLoading(true);
            try {
              const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
                credentials: 'include',
                headers: { 'X-CSRF-TOKEN': csrfToken }
              });
              const errors = await res.json();
              setIngestErrors(errors);
              console.log('[DEBUG] Refreshed ingest errors', errors);
            } catch (e) {
              setIngestErrors([]);
            } finally {
              setIngestLoading(false);
            }
          }} disabled={ingestLoading} sx={{ mb: 2 }}>Refresh</Button>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Reason</TableCell>
                <TableCell>Timestamp</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {ingestErrors.map((err) => (
                <TableRow key={err.id}>
                  <TableCell>{err.id}</TableCell>
                  <TableCell>{err.filename || 'N/A'}</TableCell>
                  <TableCell>{err.reason}</TableCell>
                  <TableCell>{err.created_at}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      </Box>

      <Box sx={{ my: 2 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">All B/L Records</Typography>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Customer</TableCell>
                <TableCell>BL Number</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Invoice</TableCell>
                <TableCell>Receipt</TableCell>
                <TableCell>Total Invoice Amount</TableCell>
                <TableCell>NEW</TableCell>
                <TableCell>OVERDUE</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.bills.map((b) => {
                console.log('[DEBUG] Rendering bill row', b);
                return (
                  <TableRow key={b.id}>
                    <TableCell>{b.id}</TableCell>
                    <TableCell>{b.customer_name}</TableCell>
                    <TableCell>{b.bl_number}</TableCell>
                    <TableCell>{b.status}</TableCell>
                    <TableCell>{b.invoice_filename ? <a href={b.invoice_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                    <TableCell>{b.receipt_filename ? <a href={b.receipt_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                    <TableCell>{b.total_invoice_amount}</TableCell>
                    <TableCell>{b.is_new ? <span style={{color:'green',fontWeight:'bold'}}>NEW</span> : ''}</TableCell>
                    <TableCell>{b.is_overdue ? <span style={{color:'red',fontWeight:'bold'}}>OVERDUE</span> : ''}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Paper>
      </Box>

      {/* Unmatched Bank Records Section */}
      <UnmatchedBankRecords />
    </Container>
  );
}

export default ManagementDashboard;
