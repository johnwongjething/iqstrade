import React, { useState, useEffect, useContext } from 'react';
import { TextField, Button, Typography, Snackbar, Alert, CircularProgress, Container, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import LoadingModal from '../components/LoadingModal';
import { UserContext } from '../UserContext';

function UploadForm({ t = x => x }) {
  const [billFiles, setBillFiles] = useState([]);
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [packingFile, setPackingFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formValues, setFormValues] = useState({ name: '', email: '', phone: '' });
  const navigate = useNavigate();
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const { csrfToken } = useContext(UserContext);

  // Move fetchCustomerInfo to a regular function
  async function fetchCustomerInfo() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/me`, {
        credentials: 'include', // Send cookies (for JWT)
      });
      if (res.ok) {
        const data = await res.json();
        setFormValues({
          name: data.customer_name || '',
          email: data.customer_email || '',
          phone: data.customer_phone || ''
        });
      }
    } catch (err) {}
  }

  useEffect(() => {
    fetchCustomerInfo();
  }, []);

  const handleInputChange = (e) => {
    setFormValues({ ...formValues, [e.target.name]: e.target.value });
  };

  const handleBillFileChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => file.type === 'application/pdf');
    if (validFiles.length !== files.length) {
      setSnackbar({ open: true, message: t('onlyPDF'), severity: 'error' });
    }
    setBillFiles(validFiles);
  };
  const handleInvoiceFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type !== 'application/pdf') {
      setSnackbar({ open: true, message: t('onlyPDF'), severity: 'error' });
      setInvoiceFile(null);
    } else {
      setInvoiceFile(file);
    }
  };
  const handlePackingFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type !== 'application/pdf') {
      setSnackbar({ open: true, message: t('onlyPDF'), severity: 'error' });
      setPackingFile(null);
    } else {
      setPackingFile(file);
    }
  };

  const onFinish = async (e) => {
    e.preventDefault();
    if (csrfToken === undefined) {
      setSnackbar({ open: true, message: 'Security token not ready. Please wait and try again.', severity: 'error' });
      return;
    }
    if (billFiles.length === 0 && !invoiceFile && !packingFile) {
      setSnackbar({ open: true, message: t('pleaseUpload'), severity: 'error' });
      return;
    }
    if (!invoiceFile || !packingFile) {
      let msg = t('confirmOptionalFiles') || 'Invoice and/or Packing List not uploaded. Do you want to continue?';
      if (!msg || msg === 'confirmOptionalFiles') msg = 'Invoice and/or Packing List not uploaded. Do you want to continue?';
      if (!window.confirm(msg)) return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('name', formValues.name);
    formData.append('email', formValues.email);
    formData.append('phone', formValues.phone);
    billFiles.forEach((file, idx) => formData.append('bill_pdf', file));
    if (invoiceFile) formData.append('invoice_pdf', invoiceFile);
    if (packingFile) formData.append('packing_pdf', packingFile);
    try {
      const headers = {};
      if (csrfToken) headers['X-CSRF-TOKEN'] = csrfToken;
      const res = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
        headers
      });
      const data = await res.json();
      if (!res.ok) {
        setSnackbar({ open: true, message: data.error || t('failed'), severity: 'error' });
      } else {
        setSnackbar({ open: true, message: t('success'), severity: 'success' });
        setBillFiles([]);
        setInvoiceFile(null);
        setPackingFile(null);
        setFormValues({ name: '', email: '', phone: '' });
      }
    } catch (err) {
      setSnackbar({ open: true, message: t('failed'), severity: 'error' });
    }
    setLoading(false);
  };

  // Debug: log selected files
  useEffect(() => {
    if (billFiles.length > 0) {
      billFiles.forEach(file => console.log('[DEBUG] Selected bill PDF for upload:', file.name));
    }
    if (invoiceFile) console.log('[DEBUG] Selected invoice PDF for upload:', invoiceFile.name);
    if (packingFile) console.log('[DEBUG] Selected packing PDF for upload:', packingFile.name);
  }, [billFiles, invoiceFile, packingFile]);
  // Conditional rendering for loading state
  if (!csrfToken && csrfToken !== null) {
    return <div>Loading...</div>;
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 4, p: { xs: 2, sm: 4 }, bgcolor: '#fff', borderRadius: 2, boxShadow: 2 }}>
        <Button onClick={() => navigate('/dashboard')} variant="contained" color="primary" sx={{ mb: 2 }}>
          {t('backToDashboard')}
        </Button>
        <Typography variant="h5" gutterBottom>{t('uploadTitle')}</Typography>
        <form onSubmit={onFinish}>
          <TextField label={t('name')} name="name" value={formValues.name} onChange={handleInputChange} required fullWidth margin="normal" />
          <TextField label={t('email')} name="email" value={formValues.email} onChange={handleInputChange} required type="email" fullWidth margin="normal" />
          <TextField label={t('phone')} name="phone" value={formValues.phone} onChange={handleInputChange} required fullWidth margin="normal" />
          <Box sx={{ my: 2 }}>
            <Button variant="outlined" component="label" fullWidth>
              {t('selectPDFBill')}
              <input type="file" accept="application/pdf" hidden multiple onChange={handleBillFileChange} />
            </Button>
            <Typography variant="caption" sx={{ mt: 1, color: 'text.secondary', display: 'block' }}>
              {t('uploadLimit') !== 'uploadLimit' ? t('uploadLimit') : 'You can upload up to 5 files.'}
            </Typography>
            {billFiles.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {billFiles.map((file, idx) => <Typography key={idx} variant="body2">{file.name}</Typography>)}
              </Box>
            )}
          </Box>
          <Box sx={{ my: 2 }}>
            <Button variant="outlined" component="label" fullWidth>
              {t('selectPDFInvoice')}
              <input type="file" accept="application/pdf" hidden onChange={handleInvoiceFileChange} />
            </Button>
            {invoiceFile && <Typography variant="body2" sx={{ mt: 1 }}>{invoiceFile.name}</Typography>}
          </Box>
          <Box sx={{ my: 2 }}>
            <Button variant="outlined" component="label" fullWidth>
              {t('selectPDFPacking')}
              <input type="file" accept="application/pdf" hidden onChange={handlePackingFileChange} />
            </Button>
            {packingFile && <Typography variant="body2" sx={{ mt: 1 }}>{packingFile.name}</Typography>}
            <Typography variant="caption" sx={{ mt: 1, color: 'text.secondary', display: 'block' }}>
              Maximum file size: 10MB per upload.
            </Typography>
          </Box>
          <Button type="submit" variant="contained" color="primary" fullWidth disabled={loading}>
            {loading ? <CircularProgress size={24} /> : t('submit')}
          </Button>
        </form>
        <LoadingModal 
          open={loading} 
          message={t('uploadingFiles')} 
        />
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

export default UploadForm;