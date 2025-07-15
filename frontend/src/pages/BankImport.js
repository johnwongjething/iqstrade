import React, { useState } from 'react';
import { Container, Typography, Box, Button, Snackbar, Alert, TextField } from '@mui/material';
import axios from 'axios';

function BankImport() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [entryCount, setEntryCount] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setSnackbar({ open: true, message: 'Please select a CSV file.', severity: 'error' });
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      // Count entries in CSV before upload
      const text = await file.text();
      const lines = text.split(/\r?\n/).filter(l => l.trim());
      // Remove header if present
      let count = lines.length;
      if (lines[0].toLowerCase().includes('date') && lines[0].toLowerCase().includes('description')) count -= 1;
      setEntryCount(count);

      const res = await axios.post('/admin/import-bank-statement', formData);
      setResults(res.data.results || []);
      setSnackbar({ open: true, message: res.data.message || 'Import complete.', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Import failed.', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };


  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h4" gutterBottom>
          Import Bank Statement
        </Typography>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mb: 2, float: 'left' }}
          href="/dashboard"
        >
          Back to Dashboard
        </Button>
        <Box sx={{ clear: 'both' }} />
        <>
          <form onSubmit={handleSubmit}>
            <TextField
              type="file"
              inputProps={{ accept: '.csv' }}
              onChange={handleFileChange}
              fullWidth
              sx={{ mb: 2 }}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              sx={{ mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Importing...' : 'Import CSV'}
            </Button>
          </form>
          {entryCount > 0 && (
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              There are {entryCount} entries in your uploaded CSV File
            </Typography>
          )}
          {results.length > 0 && (
            <Box sx={{ mt: 3, textAlign: 'left' }}>
              <Typography variant="h6">Results:</Typography>
              <ul>
                {/* Matched entries */}
                {results.filter(r => r.status === 'Matched and marked Paid').map((r, i) => (
                  <li key={i}>{r.bl_number}: {r.status}</li>
                ))}
              </ul>
              {/* Unmatched entries */}
              {results.some(r => r.status !== 'Matched and marked Paid') && (
                <>
                  <Typography variant="subtitle1" sx={{ mt: 2 }}>Unmatched Entries:</Typography>
                  <ul>
                    {results.filter(r => r.status !== 'Matched and marked Paid').map((r, i) => (
                      <li key={i}>
                        {r.description ? r.description : 'No Description'} | Amount: {r.amount !== undefined ? r.amount : 'N/A'}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Box>
          )}
        </>
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
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

export default BankImport;
