import React, { useEffect, useState, useContext, useRef } from 'react';
import {
  Container, Typography, Paper, Box, Table, TableHead, TableRow, TableCell,
  TableBody, CircularProgress, Alert, Button, Modal, TextField
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';
import { fetchWithAuth } from '../utils/tokenUtils';

function ManagementDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [ingestErrors, setIngestErrors] = useState([]);
  const [emailModalData, setEmailModalData] = useState(null);
  const [deleteModalData, setDeleteModalData] = useState(null);
  const [unmatchedRecords, setUnmatchedRecords] = useState([]);
  const [blinkReceipts, setBlinkReceipts] = useState(false);
  const [blinkBols, setBlinkBols] = useState(false);
  const ingestRef = useRef(0);
  const bolsRef = useRef(0);
  const { csrfToken } = useContext(UserContext);
  const navigate = useNavigate();

  // Helper to get CSRF token from cookie
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  const fetchUnmatched = async () => {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/admin/unmatched-receipts`);
      if (!response.ok) throw new Error('Failed to fetch unmatched receipts');
      const data = await response.json();
      setUnmatchedRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      setUnmatchedRecords([]);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetchWithAuth(`${API_BASE_URL}/api/management/overview`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const json = await res.json();
        if (res.ok) {
          setData(json);
          if (json.bills && json.bills.length !== bolsRef.current) {
            setBlinkBols(true);
            bolsRef.current = json.bills.length;
          }
        } else {
          setError(json.error || 'Failed to load');
        }
      } catch (e) {
        setError('Failed to load');
      } finally {
        setLoading(false);
      }
    };

    const fetchIngestErrors = async () => {
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/admin/email-ingest-errors`, {
          credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to fetch ingest errors');
        const data = await response.json();
        setIngestErrors(Array.isArray(data) ? data : []);
      } catch (err) {
        setIngestErrors([]);
      }
    };

    fetchData();
    fetchIngestErrors();
    fetchUnmatched();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [csrfToken]);

  useEffect(() => {
    if (activeTab === 'email') setBlinkReceipts(false);
    if (activeTab === 'bols') setBlinkBols(false);
  }, [activeTab]);

  const deleteItem = async (type, id) => {
    const endpoint = type === 'ingest' ? 'email-ingest-errors' : 'unmatched-receipts';
    // Always get the latest CSRF token from the cookie
    const csrfToken = getCookie('csrf_access_token');
    if (!csrfToken) {
      alert('CSRF token missing. Please refresh and try again.');
      return;
    }
    // Debug: log the CSRF token being sent
    // CSRF token sent
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/admin/${endpoint}/${id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-CSRF-TOKEN': csrfToken
        }
      });
      if (response.status === 200) {
        if (type === 'ingest') setIngestErrors(Array.isArray(ingestErrors) ? ingestErrors.filter(e => e.id !== id) : []);
        if (type === 'receipt') setUnmatchedRecords(Array.isArray(unmatchedRecords) ? unmatchedRecords.filter(r => r.id !== id) : []);
        setDeleteModalData(null);
      } else if (response.status === 404) {
        alert('Entry already deleted or not found.');
        if (type === 'ingest') setIngestErrors(Array.isArray(ingestErrors) ? ingestErrors.filter(e => e.id !== id) : []);
        if (type === 'receipt') setUnmatchedRecords(Array.isArray(unmatchedRecords) ? unmatchedRecords.filter(r => r.id !== id) : []);
        setDeleteModalData(null);
      } else {
        alert('Delete failed. Please try again.');
        setDeleteModalData(null);
      }
    } catch (err) {
      alert('Delete failed. Please try again.');
      setDeleteModalData(null);
    }
  };

  const metrics = data?.metrics || {};
  const ocrIssues = (data?.flags?.ocr_missing) || [];
  const tabs = [
    { key: 'overview', label: '📊 Dashboard' },
    { key: 'ocr', label: `🧾 OCR Issues (${ocrIssues.length})` },
    { key: 'email', label: `📧 Email Ingest (${ingestErrors.length})${blinkReceipts ? ' 🔴' : ''}` },
    { key: 'receipts', label: `💳 Unmatched Receipts${blinkReceipts ? ' 🔴' : ''}` },
    { key: 'bols', label: `📂 All B/L Records${blinkBols ? ' 🔴' : ''}` }
  ];

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <div style={{ display: 'flex' }}>
      <div style={{ width: '220px', background: '#f5f5f5', padding: '20px' }}>
        <h3>📋 Menu</h3>
        {tabs.map(tab => (
          <div
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{ cursor: 'pointer', padding: '8px 0', color: activeTab === tab.key ? 'blue' : 'black' }}>
            {tab.label}
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: '20px' }}>
        <Box mb={2}>
          <Button variant="contained" onClick={() => navigate('/dashboard')}>Back To Dashboard</Button>
        </Box>
        <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

        {activeTab === 'overview' && (
          <Paper sx={{ p: 2 }}>
            <Box display="flex" flexWrap="wrap" gap={2}>
              <Box><strong>Total B/L records:</strong> {metrics.total_bills}</Box>
              <Box><strong>Pending:</strong> {metrics.pending_bills}</Box>
              <Box><strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in}</Box>
              <Box><strong>Completed:</strong> {metrics.completed_bills}</Box>
              <Box><strong>Paid:</strong> {metrics.paid_bills}</Box>
              <Box><strong>Sum Invoice:</strong> {metrics.sum_invoice_amount}</Box>
              <Box><strong>Sum Paid:</strong> {metrics.sum_paid_amount}</Box>
              <Box><strong>Outstanding:</strong> {metrics.sum_outstanding_amount}</Box>
            </Box>
          </Paper>
        )}

        {activeTab === 'ocr' && (
          <>
            <h2>🧾 OCR Issues</h2>
            {ocrIssues.length > 0 ? (
              <Table size="small">
                <TableHead><TableRow><TableCell>BL</TableCell><TableCell>ID</TableCell><TableCell>Missing</TableCell></TableRow></TableHead>
                <TableBody>
                  {ocrIssues.map((i, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{i.bl_number}</TableCell>
                      <TableCell>{i.id}</TableCell>
                      <TableCell>{i.missing.join(', ')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : <p>No OCR issues found.</p>}
          </>
        )}

        {activeTab === 'email' && (
          <>
            <h2>📧 Email Ingest Errors</h2>
            <Table size="small">
              <TableHead><TableRow><TableCell>ID</TableCell><TableCell>Filename</TableCell><TableCell>Reason</TableCell></TableRow></TableHead>
              <TableBody>
                {(Array.isArray(ingestErrors) ? ingestErrors : []).map((err) => (
                  <TableRow key={err.id} onClick={() => setDeleteModalData({ type: 'ingest', id: err.id, detail: err })} style={{ cursor: 'pointer' }}>
                    <TableCell>{err.id}</TableCell>
                    <TableCell>{err.filename}</TableCell>
                    <TableCell>{err.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}

        {activeTab === 'receipts' && (
          <>
            <h2>💳 Unmatched Bank Records</h2>
            <Table size="small">
              <TableHead><TableRow>
                <TableCell>ID</TableCell><TableCell>Date</TableCell><TableCell>Description</TableCell>
                <TableCell>Amount</TableCell><TableCell>Reason</TableCell><TableCell>Created At</TableCell>
              </TableRow></TableHead>
              <TableBody>
                {(Array.isArray(unmatchedRecords) ? unmatchedRecords : []).map(row => (
                  <TableRow key={row.id} onClick={() => setDeleteModalData({ type: 'receipt', id: row.id, detail: row })} style={{ cursor: 'pointer' }}>
                    <TableCell>{row.id}</TableCell>
                    <TableCell>{row.date}</TableCell>
                    <TableCell>{row.description}</TableCell>
                    <TableCell>{row.amount}</TableCell>
                    <TableCell>{row.reason}</TableCell>
                    <TableCell>{row.created_at}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}

        {activeTab === 'bols' && (
          <>
            <h2>📂 All B/L Records</h2>
            <Table size="small">
              <TableHead><TableRow>
                <TableCell>ID</TableCell><TableCell>Customer</TableCell><TableCell>BL Number</TableCell>
                <TableCell>Status</TableCell><TableCell>Invoice</TableCell><TableCell>Email</TableCell>
              </TableRow></TableHead>
              <TableBody>
                {data.bills.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>{b.id}</TableCell>
                    <TableCell>{b.customer_name}</TableCell>
                    <TableCell>{b.bl_number}</TableCell>
                    <TableCell>{b.status}</TableCell>
                    <TableCell>{b.ctn_fee + b.service_fee}</TableCell>
                    <TableCell>
                      <Button onClick={() => setEmailModalData({ to: b.customer_email, subject: `Regarding B/L ${b.bl_number}`, body: `Dear ${b.customer_name},\n\nWe would like to inform you regarding B/L ${b.bl_number}...` })}>
                        📧
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}

        <Modal open={!!emailModalData} onClose={() => setEmailModalData(null)}>
          <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 500, bgcolor: 'white', p: 3 }}>
            <h3>Email Draft (Test Mode)</h3>
            <p><strong>To:</strong> {emailModalData?.to}</p>
            <p><strong>Subject:</strong> {emailModalData?.subject}</p>
            <TextField fullWidth multiline rows={6} value={emailModalData?.body} variant="outlined" />
          </Box>
        </Modal>

        <Modal open={!!deleteModalData} onClose={() => setDeleteModalData(null)}>
          <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'white', p: 3 }}>
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete this {deleteModalData?.type} entry?</p>
            <Box mt={2} display="flex" justifyContent="flex-end" gap={1}>
              <Button onClick={() => setDeleteModalData(null)}>Cancel</Button>
              <Button color="error" variant="contained" onClick={() => deleteItem(deleteModalData.type, deleteModalData.id)}>Delete</Button>
            </Box>
          </Box>
        </Modal>

      </div>
    </div>
  );
}

export default ManagementDashboard;

