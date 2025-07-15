import React, { useEffect, useState, useContext } from 'react';
import {
  Container, Typography, Paper, Box, Table, TableHead,
  TableRow, TableCell, TableBody, CircularProgress, Alert, Button
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
  const { csrfToken } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    let intervalId;
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/management/overview`, {
          credentials: 'include',
          headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        const json = await res.json();
        if (res.ok) {
          setData(json);
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
      } catch (e) {
        setIngestErrors([]);
      } finally {
        setIngestLoading(false);
      }
    };

    fetchData();
    fetchIngestErrors();
    intervalId = setInterval(fetchData, 10000);

    return () => clearInterval(intervalId);
  }, [csrfToken]);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  const metrics = data.metrics || {};
  const ocrIssues = (data.flags?.ocr_missing) || [];
  const emailErrors = ingestErrors || [];

  const tabs = [
    { key: 'overview', label: '📊 Dashboard' },
    { key: 'ocr', label: `🧾 OCR Issues (${ocrIssues.length})` },
    { key: 'email', label: `📧 Email Ingest (${emailErrors.length})` },
    { key: 'receipts', label: '💳 Unmatched Receipts' },
    { key: 'bols', label: '📂 All B/L Records' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <div style={{ width: '220px', background: '#f5f5f5', padding: '20px' }}>
        <h3 style={{ marginBottom: '16px' }}>📋 Menu</h3>
        {tabs.map(tab => (
          <div
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 0',
              cursor: 'pointer',
              color: activeTab === tab.key ? 'blue' : 'black',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal',
            }}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '20px' }}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
          <Button variant="contained" onClick={() => navigate('/dashboard')}>Back To Dashboard</Button>
        </Box>
        <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

        {/* 📊 Overview */}
        {activeTab === 'overview' && (
          <>
            <h2>📊 System Metrics</h2>
            <Box sx={{ my: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box><strong>Total B/L records:</strong> {metrics.total_bills}</Box>
                  <Box><strong>Pending:</strong> {metrics.pending_bills}</Box>
                  <Box><strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in}</Box>
                  <Box><strong>Completed:</strong> {metrics.completed_bills}</Box>
                  <Box><strong>Paid:</strong> {metrics.paid_bills}</Box>
                  <Box><strong>Sum of invoice amounts:</strong> {metrics.sum_invoice_amount}</Box>
                  <Box><strong>Sum of paid:</strong> {metrics.sum_paid_amount}</Box>
                  <Box><strong>Sum of outstanding:</strong> {metrics.sum_outstanding_amount}</Box>
                </Box>
              </Paper>
            </Box>
          </>
        )}

        {/* 🧾 OCR Issues */}
        {activeTab === 'ocr' && (
          <>
            <h2>🧾 OCR Issues</h2>
            {ocrIssues.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>BL Number</th>
                    <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>ID</th>
                    <th style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>Missing Fields</th>
                  </tr>
                </thead>
                <tbody>
                  {ocrIssues.map((issue, index) => (
                    <tr key={index} style={{ background: index % 2 === 0 ? '#f9f9f9' : 'white' }}>
                      <td style={{ padding: '6px' }}>{issue.bl_number}</td>
                      <td style={{ padding: '6px' }}>{issue.id}</td>
                      <td style={{ padding: '6px' }}>{issue.missing.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p>No OCR issues found.</p>}
          </>
        )}

        {/* 📧 Email Ingestion Errors */}
        {activeTab === 'email' && (
          <>
            <h2>📧 Email Ingestion Errors</h2>
            <Box sx={{ my: 2 }}>
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
                    } catch (e) {
                      setIngestErrors([]);
                    } finally {
                      setIngestLoading(false);
                    }
                  }}
                  disabled={ingestLoading}
                  sx={{ mb: 2 }}
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
                    {emailErrors.map(err => (
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
          </>
        )}

        {/* 💳 Unmatched Bank Records */}
        {activeTab === 'receipts' && (
          <>
            <h2>💳 Unmatched Bank Records</h2>
            <UnmatchedBankRecords />
          </>
        )}

        {/* 📂 All B/L Records */}
        {activeTab === 'bols' && (
          <>
            <h2>📂 All B/L Records</h2>
            <Box sx={{ my: 2 }}>
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
                      <TableCell>Total Invoice Amount</TableCell>
                      <TableCell>NEW</TableCell>
                      <TableCell>OVERDUE</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.bills.map((b) => (
                      <TableRow key={b.id}>
                        <TableCell>{b.id}</TableCell>
                        <TableCell>{b.customer_name}</TableCell>
                        <TableCell>{b.bl_number}</TableCell>
                        <TableCell>{b.status}</TableCell>
                        <TableCell>{b.invoice_filename ? <a href={b.invoice_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                        <TableCell>{b.receipt_filename ? <a href={b.receipt_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
                        <TableCell>{b.total_invoice_amount}</TableCell>
                        <TableCell>{b.is_new ? <span style={{ color: 'green', fontWeight: 'bold' }}>NEW</span> : ''}</TableCell>
                        <TableCell>{b.is_overdue ? <span style={{ color: 'red', fontWeight: 'bold' }}>OVERDUE</span> : ''}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </Box>
          </>
        )}
      </div> {/* Close Main Content */}
    </div>  // Close Sidebar + Layout
  );
}

export default ManagementDashboard;


// import React, { useEffect, useState, useContext } from 'react';
// // ✅ Tab logic setup (insert under your imports or existing useState)

// import { Container, Typography, Paper, Box, Table, TableHead, TableRow, TableCell, TableBody, CircularProgress, Alert, Button } from '@mui/material';
// import { useNavigate } from 'react-router-dom';
// import { API_BASE_URL } from '../config';
// import { UserContext } from '../UserContext';
// import UnmatchedBankRecords from './UnmatchedBankRecords';

// function ManagementDashboard() {
//   // Tab state and tab list
//   const [activeTab, setActiveTab] = useState('overview');

//   // Extract OCR issues and email errors for tab counts
//   const ocrIssues = (data && data.flags && data.flags.ocr_missing) ? data.flags.ocr_missing : [];
//   const emailErrors = ingestErrors || [];

//   const tabs = [
//     { key: 'overview', label: '📊 Dashboard' },
//     { key: 'ocr', label: `🧾 OCR Issues (${ocrIssues?.length || 0})` },
//     { key: 'email', label: `📧 Email Ingest (${emailErrors?.length || 0})` },
//     { key: 'receipts', label: '💳 Unmatched Receipts' },
//     { key: 'bols', label: '📂 All B/L Records' },
//   ];
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
//       console.log('[DEBUG] Polling: fetching management overview');
//       try {
//         const res = await fetch(`${API_BASE_URL}/api/management/overview`, {
//           credentials: 'include',
//           headers: { 'X-CSRF-TOKEN': csrfToken }
//         });
//         const json = await res.json();
//         if (res.ok) {
//           setData(json);
//           console.log("[DEBUG] Management overview data:", json);
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
//         console.log('[DEBUG] Fetched ingest errors', errors);
//       } catch (e) {
//         setIngestErrors([]);
//       } finally {
//         setIngestLoading(false);
//       }
//     };
//     fetchData();
//     fetchIngestErrors();
//     intervalId = setInterval(fetchData, 10000); // 10 seconds
//     return () => {
//       clearInterval(intervalId);
//       console.log('[DEBUG] Polling interval cleared');
//     };
//   }, [csrfToken]);

//   if (loading) return <CircularProgress />;
//   if (error) return <Alert severity="error">{error}</Alert>;

//   // Debug log for rendering
//   console.log('[DEBUG] Rendering ManagementDashboard', data);

//   // Metrics section
//   const metrics = data.metrics || {};

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

//       {/* Main Content Area */}
//       <div style={{ flex: 1, padding: '20px' }}>
//         <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', mb: 2 }}>
//           <Button variant="contained" color="primary" onClick={() => navigate('/dashboard')}>
//             Back To Dashboard
//           </Button>
//         </Box>
//         <Typography variant="h4" gutterBottom>Management Dashboard</Typography>

//         {/* 📊 System Metrics Tab */}
//         {activeTab === 'overview' && (
//           <>
//             <h2>📊 System Metrics</h2>
//             <Box sx={{ my: 2 }}>
//               <Paper sx={{ p: 2 }}>
//                 <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
//                   <Box> <strong>Total B/L records:</strong> {metrics.total_bills} </Box>
//                   <Box> <strong>Pending:</strong> {metrics.pending_bills} </Box>
//                   <Box> <strong>Awaiting Bank In:</strong> {metrics.awaiting_bank_in} </Box>
//                   <Box> <strong>Completed:</strong> {metrics.completed_bills} </Box>
//                   <Box> <strong>Paid:</strong> {metrics.paid_bills} </Box>
//                   <Box> <strong>Sum of invoice amounts:</strong> {metrics.sum_invoice_amount} </Box>
//                   <Box> <strong>Sum of paid:</strong> {metrics.sum_paid_amount} </Box>
//                   <Box> <strong>Sum of outstanding:</strong> {metrics.sum_outstanding_amount} </Box>
//                 </Box>
//               </Paper>
//             </Box>
//           </>
//         )}

//         {/* 🧾 OCR Issues Tab - compact table */}
//         {activeTab === 'ocr' && (
//           <>
//             <h2>🧾 OCR Issues</h2>
//             {ocrIssues && ocrIssues.length > 0 ? (
//               <table style={{ width: '100%', borderCollapse: 'collapse' }}>
//                 <thead>
//                   <tr>
//                     <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc', padding: '8px' }}>BL Number</th>
//                     <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc', padding: '8px' }}>ID</th>
//                     <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc', padding: '8px' }}>Missing Fields</th>
//                   </tr>
//                 </thead>
//                 <tbody>
//                   {ocrIssues.map((issue, index) => (
//                     <tr key={index} style={{ backgroundColor: index % 2 === 0 ? '#f9f9f9' : 'white' }}>
//                       <td style={{ padding: '6px' }}>{issue.bl_number}</td>
//                       <td style={{ padding: '6px' }}>{issue.id}</td>
//                       <td style={{ padding: '6px' }}>{issue.missing.join(', ')}</td>
//                     </tr>
//                   ))}
//                 </tbody>
//               </table>
//             ) : (
//               <p>No OCR issues found.</p>
//             )}
//           </>
//         )}

//         {/* 📧 Email Ingestion Errors Tab */}
//         {activeTab === 'email' && (
//           <>
//             <h2>📧 Email Ingestion Errors</h2>
//             <Box sx={{ my: 2 }}>
//               <Paper sx={{ p: 2 }}>
//                 <Button variant="outlined" size="small" onClick={async () => {
//                   setIngestLoading(true);
//                   try {
//                     const res = await fetch(`${API_BASE_URL}/admin/email-ingest-errors`, {
//                       credentials: 'include',
//                       headers: { 'X-CSRF-TOKEN': csrfToken }
//                     });
//                     const errors = await res.json();
//                     setIngestErrors(errors);
//                     console.log('[DEBUG] Refreshed ingest errors', errors);
//                   } catch (e) {
//                     setIngestErrors([]);
//                   } finally {
//                     setIngestLoading(false);
//                   }
//                 }} disabled={ingestLoading} sx={{ mb: 2 }}>Refresh</Button>
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
//                     {ingestErrors.map((err) => (
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

//         {/* 💳 Unmatched Bank Records Tab */}
//         {activeTab === 'receipts' && (
//           <>
//             <h2>💳 Unmatched Bank Records</h2>
//             <UnmatchedBankRecords />
//           </>
//         )}

//         {/* 📂 All B/L Records Tab */}
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
//                     {data.bills.map((b) => {
//                       console.log('[DEBUG] Rendering bill row', b);
//                       return (
//                         <TableRow key={b.id}>
//                           <TableCell>{b.id}</TableCell>
//                           <TableCell>{b.customer_name}</TableCell>
//                           <TableCell>{b.bl_number}</TableCell>
//                           <TableCell>{b.status}</TableCell>
//                           <TableCell>{b.invoice_filename ? <a href={b.invoice_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
//                           <TableCell>{b.receipt_filename ? <a href={b.receipt_filename} target="_blank" rel="noreferrer">View</a> : 'N/A'}</TableCell>
//                           <TableCell>{b.total_invoice_amount}</TableCell>
//                           <TableCell>{b.is_new ? <span style={{color:'green',fontWeight:'bold'}}>NEW</span> : ''}</TableCell>
//                           <TableCell>{b.is_overdue ? <span style={{color:'red',fontWeight:'bold'}}>OVERDUE</span> : ''}</TableCell>
//                         </TableRow>
//                       );
//                     })}
//                   </TableBody>
//                 </Table>
//               </Paper>
//             </Box>
//           </>
//         )}

//        </div> {/* Close sidebar + layout container */}
//      </div> {/* Close flex wrapper */}
//    </div>
//  );
// }

// export default ManagementDashboard;

