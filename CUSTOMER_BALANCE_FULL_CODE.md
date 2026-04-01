# Customer Balance Full Code - Save for Tomorrow

## File: frontend/src/pages/CustomerBalance.js

```javascript
import React, { useState, useEffect, useContext } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Modal,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  History as HistoryIcon,
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import { UserContext } from '../UserContext';
import { useNavigate } from 'react-router-dom';

const CustomerBalance = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  
  // State management
  const [searchTerm, setSearchTerm] = useState('');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerBalance, setCustomerBalance] = useState(null);
  const [transactionHistory, setTransactionHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Modal states
  const [adjustmentModalOpen, setAdjustmentModalOpen] = useState(false);
  const [adjustmentAmount, setAdjustmentAmount] = useState('');
  const [adjustmentType, setAdjustmentType] = useState('credit');
  const [adjustmentReason, setAdjustmentReason] = useState('');
  const [adjustmentLoading, setAdjustmentLoading] = useState(false);
  
  // History modal state
  const [historyModalOpen, setHistoryModalOpen] = useState(false);

  // Check authentication
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    // Only allow staff and admin users
    if (user.role !== 'staff' && user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
  }, [user, navigate]);

  // Search customers
  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setError('Please enter a search term');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/balance/search?q=${encodeURIComponent(searchTerm)}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to search customers');
      }
      
      const data = await response.json();
      setCustomers(data.customers || []);
      
      if (data.customers && data.customers.length === 0) {
        setError('No customers found matching your search');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load customer balance
  const loadCustomerBalance = async (username) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/balance/${username}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to load customer balance');
      }
      
      const data = await response.json();
      setCustomerBalance(data);
      setSelectedCustomer(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load transaction history
  const loadTransactionHistory = async (username) => {
    try {
      const response = await fetch(`/api/balance/${username}/history`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to load transaction history');
      }
      
      const data = await response.json();
      setTransactionHistory(data.transactions || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle customer selection
  const handleCustomerSelect = async (customer) => {
    setSelectedCustomer(customer);
    await loadCustomerBalance(customer.username);
    await loadTransactionHistory(customer.username);
  };

  // Handle balance adjustment
  const handleAdjustment = async () => {
    if (!selectedCustomer || !adjustmentAmount || !adjustmentReason) {
      setError('Please fill in all fields');
      return;
    }

    const amount = parseFloat(adjustmentAmount);
    if (isNaN(amount) || amount <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setAdjustmentLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/balance/${selectedCustomer.username}/adjust`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          amount: adjustmentType === 'debit' ? -amount : amount,
          reason: adjustmentReason,
          type: 'adjustment'
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to adjust balance');
      }
      
      const data = await response.json();
      setSuccess(`Balance adjusted successfully. New balance: $${data.new_balance.toFixed(2)}`);
      setAdjustmentModalOpen(false);
      setAdjustmentAmount('');
      setAdjustmentType('credit');
      setAdjustmentReason('');
      
      // Reload customer balance
      await loadCustomerBalance(selectedCustomer.username);
      await loadTransactionHistory(selectedCustomer.username);
      
      setTimeout(() => setSuccess(''), 5000);
    } catch (err) {
      setError(err.message);
    } finally {
      setAdjustmentLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  // Get transaction type color
  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'credit':
        return 'success';
      case 'debit':
        return 'error';
      case 'adjustment':
        return 'warning';
      case 'application':
        return 'info';
      default:
        return 'default';
    }
  };

  // Get transaction type icon
  const getTransactionTypeIcon = (type) => {
    switch (type) {
      case 'credit':
        return <TrendingUpIcon />;
      case 'debit':
        return <TrendingDownIcon />;
      case 'adjustment':
        return <EditIcon />;
      case 'application':
        return <AccountBalanceIcon />;
      default:
        return null;
    }
  };

  if (!user || (user.role !== 'staff' && user.role !== 'admin')) {
    return null;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <AccountBalanceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Customer Balance Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search and manage customer balances, view transaction history, and make manual adjustments.
        </Typography>
      </Box>

      {/* Search Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Search Customers
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              fullWidth
              label="Search by customer name or username"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Enter customer name or username..."
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
            >
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Error and Success Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Search Results */}
      {customers.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Search Results ({customers.length} customers)
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Username</TableCell>
                    <TableCell>Customer Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Current Balance</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {customers.map((customer) => (
                    <TableRow 
                      key={customer.username}
                      hover
                      onClick={() => handleCustomerSelect(customer)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{customer.username}</TableCell>
                      <TableCell>{customer.customer_name || 'N/A'}</TableCell>
                      <TableCell>{customer.email || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip
                          label={formatCurrency(customer.balance_amount || 0)}
                          color={customer.balance_amount >= 0 ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton size="small">
                            <AccountBalanceIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Selected Customer Details */}
      {selectedCustomer && customerBalance && (
        <Grid container spacing={3}>
          {/* Customer Balance Card */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Customer Balance
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Username: {selectedCustomer.username}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Name: {selectedCustomer.customer_name || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Email: {selectedCustomer.email || 'N/A'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h4" sx={{ mr: 2 }}>
                    {formatCurrency(customerBalance.balance_amount || 0)}
                  </Typography>
                  <Chip
                    label={customerBalance.balance_amount >= 0 ? 'Credit' : 'Debit'}
                    color={customerBalance.balance_amount >= 0 ? 'success' : 'error'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Last Updated: {formatDate(customerBalance.last_updated)}
                </Typography>
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setAdjustmentModalOpen(true)}
                  >
                    Adjust Balance
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<HistoryIcon />}
                    onClick={() => setHistoryModalOpen(true)}
                  >
                    View History
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Transactions */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Transactions
                </Typography>
                {transactionHistory.length > 0 ? (
                  <Box>
                    {transactionHistory.slice(0, 5).map((transaction) => (
                      <Box
                        key={transaction.id}
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          py: 1,
                          borderBottom: '1px solid #eee'
                        }}
                      >
                        <Box>
                          <Typography variant="body2">
                            {transaction.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(transaction.created_at)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Chip
                            icon={getTransactionTypeIcon(transaction.transaction_type)}
                            label={formatCurrency(Math.abs(transaction.amount))}
                            color={getTransactionTypeColor(transaction.transaction_type)}
                            size="small"
                          />
                        </Box>
                      </Box>
                    ))}
                    {transactionHistory.length > 5 && (
                      <Button
                        variant="text"
                        size="small"
                        onClick={() => setHistoryModalOpen(true)}
                        sx={{ mt: 1 }}
                      >
                        View All ({transactionHistory.length} transactions)
                      </Button>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No transactions found
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Balance Adjustment Modal */}
      <Modal
        open={adjustmentModalOpen}
        onClose={() => setAdjustmentModalOpen(false)}
        aria-labelledby="adjustment-modal-title"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 4,
        }}>
          <Typography id="adjustment-modal-title" variant="h6" gutterBottom>
            Adjust Customer Balance
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Adjustment Type</InputLabel>
              <Select
                value={adjustmentType}
                onChange={(e) => setAdjustmentType(e.target.value)}
                label="Adjustment Type"
              >
                <MenuItem value="credit">Credit (Add Money)</MenuItem>
                <MenuItem value="debit">Debit (Subtract Money)</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Amount"
              type="number"
              value={adjustmentAmount}
              onChange={(e) => setAdjustmentAmount(e.target.value)}
              placeholder="Enter amount"
            />
            <TextField
              fullWidth
              label="Reason"
              multiline
              rows={3}
              value={adjustmentReason}
              onChange={(e) => setAdjustmentReason(e.target.value)}
              placeholder="Enter reason for adjustment"
            />
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                onClick={() => setAdjustmentModalOpen(false)}
                disabled={adjustmentLoading}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleAdjustment}
                disabled={adjustmentLoading}
                startIcon={adjustmentLoading ? <CircularProgress size={20} /> : null}
              >
                {adjustmentLoading ? 'Processing...' : 'Apply Adjustment'}
              </Button>
            </Box>
          </Box>
        </Box>
      </Modal>

      {/* Transaction History Modal */}
      <Modal
        open={historyModalOpen}
        onClose={() => setHistoryModalOpen(false)}
        aria-labelledby="history-modal-title"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90%',
          maxWidth: 800,
          maxHeight: '90%',
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 4,
          overflow: 'auto',
        }}>
          <Typography id="history-modal-title" variant="h6" gutterBottom>
            Transaction History - {selectedCustomer?.username}
          </Typography>
          {transactionHistory.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Reference</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactionHistory.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>{formatDate(transaction.created_at)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getTransactionTypeIcon(transaction.transaction_type)}
                          label={transaction.transaction_type}
                          color={getTransactionTypeColor(transaction.transaction_type)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          color={transaction.amount >= 0 ? 'success.main' : 'error.main'}
                          fontWeight="bold"
                        >
                          {formatCurrency(Math.abs(transaction.amount))}
                        </Typography>
                      </TableCell>
                      <TableCell>{transaction.description}</TableCell>
                      <TableCell>{transaction.payment_source || 'Manual'}</TableCell>
                      <TableCell>
                        {transaction.reference_type && transaction.reference_id ? (
                          `${transaction.reference_type} #${transaction.reference_id}`
                        ) : (
                          'N/A'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No transaction history found
            </Typography>
          )}
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={() => setHistoryModalOpen(false)}>
              Close
            </Button>
          </Box>
        </Box>
      </Modal>
    </Container>
  );
};

export default CustomerBalance;
```

## Notes for Tomorrow

1. **Current Issue**: The component was simplified to debug the 404 error. This is the full version that needs to be restored.

2. **Features Included**:
   - Customer search by name or username
   - Display customer balance and details
   - Manual balance adjustments (credit/debit)
   - Transaction history viewing
   - Responsive design with Material-UI components
   - Proper error handling and loading states
   - Authentication and authorization checks

3. **Dependencies**: Make sure all Material-UI icons are imported correctly

4. **API Endpoints Used**:
   - `GET /api/balance/search?q={searchTerm}`
   - `GET /api/balance/{username}`
   - `GET /api/balance/{username}/history`
   - `POST /api/balance/{username}/adjust`

5. **Restoration Steps**:
   - Replace the simplified `CustomerBalance.js` with this full code
   - Test all functionality after restoration
   - Verify the 404 issue is resolved first 