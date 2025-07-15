import React, { useEffect, useState, useContext } from 'react';
import {
  Typography, Paper, Box, Table, TableHead, TableRow, TableCell,
  TableBody, CircularProgress, Alert, Button, Modal, TextField
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';
import UnmatchedBankRecords from './UnmatchedBankRecords';

function ManagementDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [ingestErrors, setIngestErrors] = useState([]);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [emailModalData, setEmailModalData] = useState(null);
  const { csrfToken } = useContext(UserContext);
  const navigate = useNavigate();

  const [hasNewUnmatched, setHasNewUnmatched] = useState(false);
  const [hasNewBOL, setHasNewBOL] = useState(false);
  const [prevUnmatchedCount, setPrevUnmatchedCount] = useState(0);
  const [prevBOLCount, setPrevBOLCount] = useState(0);

  const ocrIssues = (data?.flags?.ocr_missing || []);
  const emailErrors = ingestErrors || [];

  const tabs = [
    { key: 'overview', label: '📊 Dashboard' },
    { key: 'ocr', label: `🧾 OCR Issues (${ocrIssues.length})` },
    { key: 'email', label: `📧 Email Ingest (${emailErrors.length})` },
    {
      key: 'receipts',
      label: (
        <span style={hasNewUnmatched && activeTab !== 'receipts' ? {
          animation: 'blinker 1s linear infinite', color: 'red'
        } : {}}>
          💳 Unmatched Receipts
        </span>
      )
    },
    {
      key: 'bols',
      label: (
        <span style={hasNewBOL && activeTab !== 'bols' ? {
          animation: 'blinker 1s linear infinite', color: 'red'
        } : {}}>
          📂 All B/L Records
        </span>
      )
    },
  ];

  useEffect(() => {
    if (activeTab === 'receipts') setHasNewUnmatched(false);
    if (activeTab === 'bols') setHasNewBOL(false);
  }, [activeTab]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/management/overview`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const json = await res.json();
        if (res.ok) {
          setData(json);
          const newUnmatched = json.unmatched_receipts?.length || 0;
          if (newUnmatched > prevUnmatchedCount) setHasNewUnmatched(true);
          setPrevUnmatchedCount(newUnmatched);

          const newBOLs = json.bills?.length || 0;
          if (newBOLs > prevBOLCount) setHasNewBOL(true);
          setPrevBOLCount(newBOLs);
        } else {
          setError(json.error || 'Failed to load');
        }
      } catch {
        setError('Failed to load');
      } finally {
        setLoading(false);
      }
    };

    const fetchIngestErrors = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const errors = await res.json();
        setIngestErrors(errors);
      } catch {
        setIngestErrors([]);
      }
    };

    fetchData();
    fetchIngestErrors();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [csrfToken]);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  const metrics = data?.metrics || {};

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <div style={{ width: '220px', background: '#f5f5f5', padding: '20px' }}>
        <h3>📋 Menu</h3>
        {tabs.map(tab => (
          <div
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 0',
              cursor: 'pointer',
              color: activeTab === tab.key ? 'blue' : 'black',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal'
            }}
          >
            {tab.label}
          </div>
        ))}
      </div>

      <div style={{ flex: 1, padding: '20px' }}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
          <Button variant="contained" onClick={() => navigate('/dashboard')}>
            Back To Dashboard
          </Button>
        </Box>
        <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

        {activeTab === 'overview' && (
          <>
            <h2>📊 System Metrics</h2>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box><strong>Total B/L records:</strong> {metrics.total_bills}</Box>
                <Box><strong>Pending:</strong> {metrics.pending_bills}</Box>
                <Box><strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in}</Box>
                <Box><strong>Completed:</strong> {metrics.completed_bills}</Box>
                <Box><strong>Paid:</strong> {metrics.paid_bills}</Box>
                <Box><strong>Sum invoice:</strong> {metrics.sum_invoice_amount}</Box>
                <Box><strong>Sum paid:</strong> {metrics.sum_paid_amount}</Box>
                <Box><strong>Sum outstanding:</strong> {metrics.sum_outstanding_amount}</Box>
              </Box>
            </Paper>
          </>
        )}

        {activeTab === 'ocr' && (
          <>
            <h2>🧾 OCR Issues</h2>
            {ocrIssues.length > 0 ? (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>BL Number</TableCell>
                    <TableCell>ID</TableCell>
                    <TableCell>Missing Fields</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ocrIssues.map((issue, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{issue.bl_number}</TableCell>
                      <TableCell>{issue.id}</TableCell>
                      <TableCell>{issue.missing.join(', ')}</TableCell>
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
            <Paper sx={{ p: 2 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={async () => {
                  setIngestLoading(true);
                  try {
                    const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
                      credentials: 'include',
                      headers: { 'X-CSRF-TOKEN': csrfToken }
                    });
                    const errors = await res.json();
                    setIngestErrors(errors);
                  } catch {
                    setIngestErrors([]);
                  } finally {
                    setIngestLoading(false);
                  }
                }}
                disabled={ingestLoading}
              >
                Refresh
              </Button>
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
                    <TableRow key={err.id} onClick={() => setEmailModalData(err)} style={{ cursor: 'pointer' }}>
                      <TableCell>{err.id}</TableCell>
                      <TableCell>{err.filename || 'N/A'}</TableCell>
                      <TableCell>{err.reason}</TableCell>
                      <TableCell>{err.created_at}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </>
        )}

        {activeTab === 'receipts' && (
          <>
            <h2>💳 Unmatched Bank Records</h2>
            <UnmatchedBankRecords />
          </>
        )}

        {activeTab === 'bols' && (
          <>
            <h2>📂 All B/L Records</h2>
            <Paper sx={{ p: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell>BL Number</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Invoice</TableCell>
                    <TableCell>Receipt</TableCell>
                    <TableCell>Total</TableCell>
                    <TableCell>NEW</TableCell>
                    <TableCell>OVERDUE</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.bills.map(b => (
                    <TableRow key={b.id}>
                      <TableCell>{b.id}</TableCell>
                      <TableCell>{b.customer_name}</TableCell>
                      <TableCell>{b.bl_number}</TableCell>
                      <TableCell>{b.status}</TableCell>
                      <TableCell>{b.invoice_filename ? <a href={b.invoice_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                      <TableCell>{b.receipt_filename ? <a href={b.receipt_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                      <TableCell>{b.total_invoice_amount}</TableCell>
                      <TableCell>{b.is_new ? <span style={{ color: 'green' }}>NEW</span> : ''}</TableCell>
                      <TableCell>{b.is_overdue ? <span style={{ color: 'red' }}>OVERDUE</span> : ''}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </>
        )}
      </div>

      {/* Email Modal (Test Only) */}
      {emailModalData ? (
        <Modal open={!!emailModalData} onClose={() => setEmailModalData(null)}>
          <Box sx={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)', width: 500,
            bgcolor: 'white', p: 3
          }}>
            <h3>Email Draft (Test Mode)</h3>
            {emailModalData.error ? (
              <Alert severity="error">{emailModalData.error}</Alert>
            ) : (
              <>
                <p><strong>To:</strong> {emailModalData.to || ""}</p>
                <p><strong>Subject:</strong> {emailModalData.subject || ""}</p>
                <TextField
                  fullWidth multiline rows={6}
                  value={emailModalData.body || ""}
                  variant="outlined"
                />
              </>
            )}
          </Box>
        </Modal>
      ) : null}
    </div>
  );
}

export default ManagementDashboard;



// import React, { useEffect, useState, useContext } from 'react';
// import {
//   Container, Typography, Paper, Box, Table, TableHead,
//   TableRow, TableCell, TableBody, CircularProgress, Alert, Button
// } from '@mui/material';
// import { useNavigate } from 'react-router-dom';
// import { API_BASE_URL } from '../config';
// import { UserContext } from '../UserContext';
// import UnmatchedBankRecords from './UnmatchedBankRecords';

// function ManagementDashboard() {
//   const [activeTab, setActiveTab] = useState('overview');
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [data, setData] = useState(null);
//   const [ingestErrors, setIngestErrors] = useState([]);
//   const [ingestLoading, setIngestLoading] = useState(false);
//   const { csrfToken } = useContext(UserContext);
//   const navigate = useNavigate();

//   useEffect(() => {
//     let intervalId;
//     const fetchData = async () => {
//       try {
//         const res = await fetch(`${API_BASE_URL}/api/management/overview`, {
//           credentials: 'include',
//           headers: { 'X-CSRF-TOKEN': csrfToken }
//         });
//         const json = await res.json();
//         if (res.ok) {
//           setData(json);
//         } else {
//           setError(json.error || "Failed to load");
//         }
//       } catch (e) {
//         setError("Failed to load");
//       } finally {
//         setLoading(false);
//       }
//     };

//     const fetchIngestErrors = async () => {
//       setIngestLoading(true);
//       try {
//         const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
//           credentials: 'include',
//           headers: { 'X-CSRF-TOKEN': csrfToken }
//         });
//         const errors = await res.json();
//         setIngestErrors(errors);
//       } catch (e) {
//         setIngestErrors([]);
//       } finally {
//         setIngestLoading(false);
//       }
//     };

//     fetchData();
//     fetchIngestErrors();
//     intervalId = setInterval(fetchData, 10000);

//     return () => clearInterval(intervalId);
//   }, [csrfToken]);

//   if (loading) return <CircularProgress />;
//   if (error) return <Alert severity="error">{error}</Alert>;

//   const metrics = data.metrics || {};
//   const ocrIssues = (data.flags?.ocr_missing) || [];
//   const emailErrors = ingestErrors || [];

//   const tabs = [
//     { key: 'overview', label: '📊 Dashboard' },
//     { key: 'ocr', label: `🧾 OCR Issues (${ocrIssues.length})` },
//     { key: 'email', label: `📧 Email Ingest (${emailErrors.length})` },
//     { key: 'receipts', label: '💳 Unmatched Receipts' },
//     { key: 'bols', label: '📂 All B/L Records' },
//   ];

//   return (
//     <div style={{ display: 'flex', minHeight: '100vh' }}>
//       {/* Sidebar */}
//       <div style={{ width: '220px', background: '#f5f5f5', padding: '20px' }}>
//         <h3 style={{ marginBottom: '16px' }}>📋 Menu</h3>
//         {tabs.map(tab => (
//           <div
//             key={tab.key}
//             onClick={() => setActiveTab(tab.key)}
//             style={{
//               padding: '10px 0',
//               cursor: 'pointer',
//               color: activeTab === tab.key ? 'blue' : 'black',
//               fontWeight: activeTab === tab.key ? 'bold' : 'normal',
//             }}
//           >
//             {tab.label}
//           </div>
//         ))}
//       </div>

//       {/* Main Content */}
//       <div style={{ flex: 1, padding: '20px' }}>
//         <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
//           <Button variant="contained" onClick={() => navigate('/dashboard')}>Back To Dashboard</Button>
//         </Box>
//         <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

//         {/* 📊 Overview */}
//         {activeTab === 'overview' && (
//           <>
//             <h2>📊 System Metrics</h2>
//             <Box sx={{ my: 2 }}>
//               <Paper sx={{ p: 2 }}>
//                 <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
//                   <Box><strong>Total B/L records:</strong> {metrics.total_bills}</Box>
//                   <Box><strong>Pending:</strong> {metrics.pending_bills}</Box>
//                   <Box><strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in}</Box>
//                   <Box><strong>Completed:</strong> {metrics.completed_bills}</Box>
//                   <Box><strong>Paid:</strong> {metrics.paid_bills}</Box>
//                   <Box><strong>Sum of invoice amounts:</strong> {metrics.sum_invoice_amount}</Box>
//                   <Box><strong>Sum of paid:</strong> {metrics.sum_paid_amount}</Box>
//                   <Box><strong>Sum of outstanding:</strong> {metrics.sum_outstanding_amount}</Box>
//                 </Box>
//               </Paper>
//             </Box>
//           </>
//         )}

//         {/* 🧾 OCR Issues */}
//         {activeTab === 'ocr' && (
//           <>
//             <h2>🧾 OCR Issues</h2>
//             {ocrIssues.length > 0 ? (
//               <table style={{ width: '100%', borderCollapse: 'collapse' }}>
//                 <thead>
//                   <tr>
//                     <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>BL Number</th>
//                     <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>ID</th>
//                     <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>Missing Fields</th>
//                   </tr>
//                 </thead>
//                 <tbody>
//                   {ocrIssues.map((issue, index) => (
//                     <tr key={index} style={{ background: index % 2 === 0 ? '#f9f9f9' : 'white' }}>
//                       <td style={{ padding: '6px' }}>{issue.bl_number}</td>
//                       <td style={{ padding: '6px' }}>{issue.id}</td>
//                       <td style={{ padding: '6px' }}>{issue.missing.join(', ')}</td>
//                     </tr>
//                   ))}
//                 </tbody>
//               </table>
//             ) : <p>No OCR issues found.</p>}
//           </>
//         )}

//         {/* 📧 Email Ingestion Errors */}
//         {activeTab === 'email' && (
//           <>
//             <h2>📧 Email Ingestion Errors</h2>
//             <Box sx={{ my: 2 }}>
//               <Paper sx={{ p: 2 }}>
//                 <Button
//                   variant="outlined"
//                   size="small"
//                   onClick={async () => {
//                     setIngestLoading(true);
//                     try {
//                       const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
//                         credentials: 'include',
//                         headers: { 'X-CSRF-TOKEN': csrfToken }
//                       });
//                       const errors = await res.json();
//                       setIngestErrors(errors);
//                     } catch (e) {
//                       setIngestErrors([]);
//                     } finally {
//                       setIngestLoading(false);
//                     }
//                   }}
//                   disabled={ingestLoading}
//                   sx={{ mb: 2 }}
//                 >
//                   Refresh
//                 </Button>
//                 <Table>
//                   <TableHead>
//                     <TableRow>
//                       <TableCell>ID</TableCell>
//                       <TableCell>Filename</TableCell>
//                       <TableCell>Reason</TableCell>
//                       <TableCell>Timestamp</TableCell>
//                     </TableRow>
//                   </TableHead>
//                   <TableBody>
//                     {emailErrors.map(err => (
//                       <TableRow key={err.id}>
//                         <TableCell>{err.id}</TableCell>
//                         <TableCell>{err.filename || 'N/A'}</TableCell>
//                         <TableCell>{err.reason}</TableCell>
//                         <TableCell>{err.created_at}</TableCell>
//                       </TableRow>
//                     ))}
//                   </TableBody>
//                 </Table>
//               </Paper>
//             </Box>
//           </>
//         )}

//         {/* 💳 Unmatched Bank Records */}
//         {activeTab === 'receipts' && (
//           <>
//             <h2>💳 Unmatched Bank Records</h2>
//             <UnmatchedBankRecords />
//           </>
//         )}

//         {/* 📂 All B/L Records */}
//         {activeTab === 'bols' && (
//           <>
//             <h2>📂 All B/L Records</h2>
//             <Box sx={{ my: 2 }}>
//               <Paper sx={{ p: 2 }}>
//                 <Table>
//                   <TableHead>
//                     <TableRow>
//                       <TableCell>ID</TableCell>
//                       <TableCell>Customer</TableCell>
//                       <TableCell>BL Number</TableCell>
//                       <TableCell>Status</TableCell>
//                       <TableCell>Invoice</TableCell>
//                       <TableCell>Receipt</TableCell>
//                       <TableCell>Total Invoice Amount</TableCell>
//                       <TableCell>NEW</TableCell>
//                       <TableCell>OVERDUE</TableCell>
//                     </TableRow>
//                   </TableHead>
//                   <TableBody>
//                     {data.bills.map((b) => (
//                       <TableRow key={b.id}>
//                         <TableCell>{b.id}</TableCell>
//                         <TableCell>{b.customer_name}</TableCell>
//                         <TableCell>{b.bl_number}</TableCell>
//                         <TableCell>{b.status}</TableCell>
//                         <TableCell>{b.invoice_filename ? <a href={b.invoice_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
//                         <TableCell>{b.receipt_filename ? <a href={b.receipt_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
//                         <TableCell>{b.total_invoice_amount}</TableCell>
//                         <TableCell>{b.is_new ? <span style={{ color: 'green', fontWeight: 'bold' }}>NEW</span> : ''}</TableCell>
//                         <TableCell>{b.is_overdue ? <span style={{ color: 'red', fontWeight: 'bold' }}>OVERDUE</span> : ''}</TableCell>
//                       </TableRow>
//                     ))}
//                   </TableBody>
//                 </Table>
//               </Paper>
//             </Box>
//           </>
//         )}
//       </div> {/* Close Main Content */}
//     </div>  // Close Sidebar + Layout
//   );
// }

// export default ManagementDashboard;

