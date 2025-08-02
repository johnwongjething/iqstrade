import React, { useEffect, useState, useContext } from 'react';
import { UserContext } from '../UserContext';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  TextField,
  Modal,
  List,
  ListItem,
  ListItemText,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  useMediaQuery,
  Chip,
  Tooltip,
  Alert,
  CircularProgress
} from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import { useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../utils/tokenUtils';
import { formatHKDateTimeShort } from '../utils/timezoneUtils';
import { API_BASE_URL } from '../config';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 600,
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 4,
  maxHeight: '90vh',
  overflowY: 'auto',
};

// Confidence score color mapping
const getConfidenceColor = (score) => {
  if (score >= 0.8) return 'success';
  if (score >= 0.6) return 'warning';
  return 'error';
};

const getConfidenceText = (score) => {
  if (score >= 0.9) return 'High';
  if (score >= 0.8) return 'Good';
  if (score >= 0.6) return 'Moderate';
  if (score >= 0.4) return 'Low';
  return 'Very Low';
};

export default function CustomerEmails({ t = x => x }) {
  console.log('📧 CustomerEmails component rendering - HOT RELOAD TEST');
  const [senderFilter, setSenderFilter] = useState('');
  const [blFilter, setBlFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [replyStatus, setReplyStatus] = useState('all');
  const [filterTimeout, setFilterTimeout] = useState(null);
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [selected, setSelected] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);
  const [refresh, setRefresh] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const { csrfToken } = useContext(UserContext);
  const isMobile = useMediaQuery('(max-width:600px)');
  // Add handler to process unprocessed payment emails
  const [processingPayments, setProcessingPayments] = useState(false);
  const [cannedResponses, setCannedResponses] = useState([]);
  const [blModalOpen, setBlModalOpen] = useState(false);
  const [selectedBL, setSelectedBL] = useState(null);
  const [blDetails, setBlDetails] = useState(null);
  const [loadingBL, setLoadingBL] = useState(false);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
      const [loading, setLoading] = useState(false);
    const [totalEmails, setTotalEmails] = useState(0);
    const [isIngesting, setIsIngesting] = useState(false);
    const [processorStatus, setProcessorStatus] = useState(null);
    const [initialLoading, setInitialLoading] = useState(true);
  
  // Real-time synchronization states
  const [emailLocks, setEmailLocks] = useState({});
  const [userActivity, setUserActivity] = useState({});
  const [currentUserActivity, setCurrentUserActivity] = useState(null);
  const [activityInterval, setActivityInterval] = useState(null);
  const [isPageActive, setIsPageActive] = useState(true);
  const [lastActivityUpdate, setLastActivityUpdate] = useState(0);
  const [activityUpdateCooldown] = useState(5000); // 5 seconds cooldown

  // Smart polling - only poll when page is active
  useEffect(() => {
    const handleVisibilityChange = () => {
      const wasActive = isPageActive;
      const newActive = !document.hidden;
      setIsPageActive(newActive);
      
      // If page becomes active, immediately update user activity (but respect rate limit)
      if (!wasActive && newActive) {
        updateUserActivity();
        // Only load user activity if enough time has passed
        const now = Date.now();
        if (now - lastActivityUpdate >= activityUpdateCooldown) {
          loadUserActivity();
        }
      }
    };

    const handleFocus = () => {
      if (!isPageActive) {
        setIsPageActive(true);
        updateUserActivity();
        // Only load user activity if enough time has passed
        const now = Date.now();
        if (now - lastActivityUpdate >= activityUpdateCooldown) {
          loadUserActivity();
        }
      }
    };
    
    const handleBlur = () => {
      // Don't immediately set inactive - wait a bit to avoid flickering
      setTimeout(() => {
        if (document.hidden) {
          setIsPageActive(false);
        }
      }, 5000); // 5 second delay
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [isPageActive, lastActivityUpdate, activityUpdateCooldown]);

  // Cleanup email locks on component unmount
  useEffect(() => {
    return () => {
      // Release any active email lock when component unmounts
      if (selected && selected.id) {
        console.log('🧹 Cleaning up email lock on unmount for email:', selected.id);
        releaseEmailLock(selected.id).catch(error => {
          console.error('Failed to cleanup email lock on unmount:', error);
        });
      }
    };
  }, [selected]);

  // Cleanup email locks when page becomes hidden
  useEffect(() => {
    const handlePageHide = () => {
      if (selected && selected.id) {
        console.log('🧹 Cleaning up email lock on page hide for email:', selected.id);
        releaseEmailLock(selected.id).catch(error => {
          console.error('Failed to cleanup email lock on page hide:', error);
        });
      }
    };

    window.addEventListener('beforeunload', handlePageHide);
    window.addEventListener('pagehide', handlePageHide);

    return () => {
      window.removeEventListener('beforeunload', handlePageHide);
      window.removeEventListener('pagehide', handlePageHide);
    };
  }, [selected]);

  useEffect(() => {
    fetchWithAuth(`${API_BASE_URL}/admin/canned-responses`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => setCannedResponses(data))
      .catch(err => console.error('Failed to fetch canned responses:', err));
  }, []);

  // Clean up existing locks on component mount
  useEffect(() => {
    cleanupExistingLocks();
  }, []);

  // Real-time activity tracking
  const updateUserActivity = async (emailId = null, action = null) => {
    // Rate limiting - only update every 10 seconds
    const now = Date.now();
    if (now - lastActivityUpdate < 10000) { // 10 seconds cooldown for activity updates
      return;
    }
    
    try {
      await fetchWithAuth(`${API_BASE_URL}/admin/email/activity`, { 
        method: 'GET',
        credentials: 'include' 
      });
    } catch (error) {
      console.error('Failed to update user activity:', error);
    }
  };

  const acquireEmailLock = async (emailId) => {
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/${emailId}/lock`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        return { success: true, data: result };
      } else {
        const error = await response.json();
        return { success: false, error: error.error || 'Failed to lock email' };
      }
    } catch (error) {
      return { success: false, error: 'Network error while locking email' };
    }
  };

  const releaseEmailLock = async (emailId) => {
    if (!emailId) {
      console.warn('No email ID provided for lock release');
      return;
    }

    const maxRetries = 3;
    let retryCount = 0;

    while (retryCount < maxRetries) {
      try {
        console.log(`🔓 Attempting to release email lock for email ${emailId} (attempt ${retryCount + 1})`);
        
        const response = await fetchWithAuth(
          `${API_BASE_URL}/admin/email/${emailId}/unlock`,
          {
            method: 'POST',
            credentials: 'include'
          }
        );

        if (response.ok) {
          console.log(`✅ Successfully released email lock for email ${emailId}`);
          return true;
        } else {
          const errorData = await response.json();
          console.warn(`⚠️ Failed to release email lock for email ${emailId}:`, errorData);
          
          if (response.status === 404) {
            // Email lock doesn't exist, consider it "released"
            console.log(`ℹ️ Email lock for email ${emailId} doesn't exist (already released)`);
            return true;
          }
        }
      } catch (error) {
        console.error(`❌ Error releasing email lock for email ${emailId} (attempt ${retryCount + 1}):`, error);
      }

      retryCount++;
      if (retryCount < maxRetries) {
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
      }
    }

    console.error(`❌ Failed to release email lock for email ${emailId} after ${maxRetries} attempts`);
    return false;
  };

  const checkEmailLockStatus = async (emailId) => {
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/${emailId}/lock/status`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to check email lock status:', error);
    }
    return { locked: false };
  };

  const loadUserActivity = async () => {
    // Rate limiting - only update every 5 seconds
    const now = Date.now();
    if (now - lastActivityUpdate < activityUpdateCooldown) {
      console.log('⏰ Skipping user activity update - rate limited');
      return;
    }
    
    try {
      console.log('🔄 Loading user activity...');
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/activity`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setUserActivity(data.active_users || {});
        setEmailLocks(data.email_locks || {});
        setLastActivityUpdate(now);
        console.log('✅ User activity updated successfully');
      } else {
        console.warn('⚠️ Failed to load user activity:', response.status);
      }
    } catch (error) {
      console.error('❌ Failed to load user activity:', error);
    }
  };

  // Helper to fetch new emails from IMAP and then fetch inbox
  const fetchAndUpdateEmails = async (showNotification = false) => {
    if (isIngesting) {
      console.log('Skipping refresh - ingestion in progress');
      return;
    }
    
    // Check if email processing is already running
    try {
      const statusRes = await fetchWithAuth(`${API_BASE_URL}/admin/email-processing-status`, {
        method: 'GET',
        credentials: 'include'
      });
      
      if (statusRes.ok) {
        const status = await statusRes.json();
        if (status.is_processing) {
          const message = `Email processing already in progress by ${status.started_by || 'background'} since ${status.started_at}`;
          console.log(message);
          if (showNotification) {
            setSnackbar({ open: true, message: message, severity: 'warning' });
          }
          return;
        }
      }
    } catch (e) {
      console.warn('Failed to check email processing status:', e);
    }
    
    setProcessingPayments(true);
    setIsIngesting(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/admin/ingest-emails`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken ? { 'X-CSRF-TOKEN': csrfToken } : undefined
      });
      if (res.status === 401) {
        console.warn('[DEBUG] Not authorized to ingest emails, skipping ingestion.');
      }

      // Load first page after ingestion with current filters
      // This will preserve the user's current filter selection
      await loadEmails(1, false);
      if (showNotification) {
        setSnackbar({ open: true, message: 'Emails refreshed successfully!', severity: 'success' });
      }
    } catch (e) {
      console.warn('IMAP ingestion or inbox fetch failed:', e);
      if (showNotification) {
        setSnackbar({ open: true, message: 'Failed to refresh emails.', severity: 'error' });
      }
    } finally {
      setProcessingPayments(false);
      setIsIngesting(false);
    }
  };

  // Load emails with pagination
  const loadEmails = async (pageNum = 1, append = false, filterOverride = null) => {
    if (isIngesting) {
      console.log('Skipping load - ingestion in progress');
      return;
    }
    
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams({
        page: pageNum,
        per_page: 50
      });
      
      if (senderFilter) params.append('sender', senderFilter);
      if (blFilter) params.append('bl_number', blFilter); // Search BL numbers field
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      // Use filterOverride if provided, otherwise use replyStatus state
      const currentReplyStatus = filterOverride !== null ? filterOverride : replyStatus;
      
      if (currentReplyStatus !== 'all') {
        params.append('reply_status', currentReplyStatus);
        console.log(`DEBUG: Frontend sending reply_status = '${currentReplyStatus}'`);
        console.log(`DEBUG: Full URL params: ${params.toString()}`);
      } else {
        console.log(`DEBUG: No reply_status filter (replyStatus = '${currentReplyStatus}')`);
      }
      
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/inbox?${params.toString()}`, 
        { credentials: 'include' }
      );
      const data = await response.json();
      
      // Debug: Log the received data
      console.log(`DEBUG: Received ${data.emails?.length || 0} emails from backend`);
      if (data.emails && data.emails.length > 0) {
        console.log(`DEBUG: First email data:`, {
          id: data.emails[0].id,
          has_replies: data.emails[0].has_replies,
          has_sent_replies: data.emails[0].has_sent_replies,
          reply_count: data.emails[0].reply_count,
          sent_count: data.emails[0].sent_count
        });
      }
      
      if (append) {
        setEmails(prev => [...prev, ...data.emails]);
      } else {
        setEmails(data.emails);
      }
      
      setHasMore(data.has_more);
      setPage(pageNum);
      setTotalEmails(data.total);
    } catch (error) {
      console.error('Failed to load emails:', error);
      setSnackbar({ open: true, message: 'Failed to load emails', severity: 'error' });
    } finally {
      setLoading(false);
      setInitialLoading(false);
    }
  };

  // Load more emails (infinite scroll)
  const loadMore = () => {
    if (!loading && hasMore && !isIngesting) {
      loadEmails(page + 1, true);
    }
  };

  // Load processor status
  const loadProcessorStatus = async () => {
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/processor/status`, 
        { credentials: 'include' }
      );
      const status = await response.json();
      setProcessorStatus(status);
    } catch (error) {
      console.error('Failed to load processor status:', error);
    }
  };

  useEffect(() => {
    loadEmails(1, false);
    loadProcessorStatus();
    loadUserActivity();
    
    const interval = setInterval(() => {
      if (!isIngesting && isPageActive) {
        fetchAndUpdateEmails();
      }
    }, 15 * 60 * 1000); // every 15 minutes, but only if not ingesting and page is active
    
    const statusInterval = setInterval(() => {
      if (isPageActive) {
        loadProcessorStatus();
      }
    }, 2 * 60 * 1000); // every 2 minutes (reduced from 30 seconds)
    
    // Real-time activity tracking - MORE FREQUENT for multi-user collaboration
    const activityInterval = setInterval(() => {
      // Always update user activity for collaboration, but less frequently when inactive
      if (isPageActive) {
        loadUserActivity();
      } else {
        // Even when inactive, check user activity every 2 minutes to maintain collaboration
        loadUserActivity();
      }
    }, isPageActive ? 30 * 1000 : 2 * 60 * 1000); // 30s when active, 2min when inactive
    
    // Email lock status - critical for multi-user collaboration
    const lockStatusInterval = setInterval(() => {
      // Always check lock status for collaboration, but less frequently when inactive
      if (isPageActive) {
        // Check locks for emails currently being viewed
        if (selected) {
          checkEmailLockStatus(selected.id);
        }
      }
    }, isPageActive ? 15 * 1000 : 60 * 1000); // 15s when active, 1min when inactive
    
    // Update user activity on component mount
    updateUserActivity();
    
    return () => {
      clearInterval(interval);
      clearInterval(statusInterval);
      clearInterval(activityInterval);
      clearInterval(lockStatusInterval); // Clear the new interval
      
      // Release any locks when component unmounts
      if (currentUserActivity && currentUserActivity.current_email_id) {
        releaseEmailLock(currentUserActivity.current_email_id);
      }
    };
  }, [refresh]);

  // Filtered emails - now handled by backend pagination
  const filteredEmails = emails;

  const openDetail = async (id) => {
    try {
      // Prevent multiple clicks by checking if already loading
      if (loadingEmail || (selected && selected.id === id && modalOpen)) {
        console.log('Email already loading or open, ignoring click');
        return;
      }

      setLoadingEmail(true);

      // Clean up any existing locks for the current user
      await cleanupExistingLocks();

      // Try to acquire lock before opening email
      const lockResult = await acquireEmailLock(id);
      
      if (!lockResult.success) {
        // Show warning but still allow opening the email
        setSnackbar({ 
          open: true, 
          message: `Warning: ${lockResult.error}. You can still view the email but editing may be limited.`, 
          severity: 'warning' 
        });
        // Continue with opening the email even if lock fails
      } else {
        console.log('✅ Email lock acquired successfully');
      }
      
      // Update user activity
      setCurrentUserActivity({ current_email_id: id, action: 'editing' });
      updateUserActivity(id, 'editing');
      
      const response = await fetchWithAuth(`${API_BASE_URL}/admin/email/${id}`, { credentials: 'include' });
      
      if (!response.ok) {
        throw new Error('Failed to fetch email details');
      }
      
      const data = await response.json();
      setSelected(data);
      setModalOpen(true);
      
      // Debug attachments
      console.log('📧 Email detail data received');
      
      // Additional debugging for attachment structure
      if (data.attachments) {
        data.attachments.forEach((att, index) => {
          console.log(`📎 Attachment ${index}:`, att);
        });
      }
      
      // Find the latest draft reply from OpenAI, fall back to latest reply if none
      const latestDraft = data.replies?.find(r => r.sender === 'openai_draft');
      const latestReply = (data.replies || []).length > 0 ? (data.replies || []).reduce((latest, current) =>  
        new Date(latest.created_at) > new Date(current.created_at) ? latest : current
      ) : null;
      setReply(latestDraft ? latestDraft.body : (latestReply ? latestReply.body : ''));
      console.log('📧 Email detail fetched');
      
    } catch (err) {
      console.error('Failed to fetch email detail:', err);
      // Release lock on error
      await releaseEmailLock(id);
      setCurrentUserActivity(null);
      setSnackbar({ open: true, message: 'Failed to load email details', severity: 'error' });
    } finally {
      setLoadingEmail(false);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) return [];
    
    setUploadingFiles(true);
    const uploadedUrls = [];
    
    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        
        // For file uploads, we need to use fetch directly to avoid Content-Type override
        const response = await fetch(`${API_BASE_URL}/admin/upload`, {
          method: 'POST',
          body: formData,
          credentials: 'include'  // This sends cookies with the request
        });
        
        if (response.status === 401) {
          // Try to refresh the access token
          const refreshRes = await fetch('/api/refresh', { 
            method: 'POST', 
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
          });
          
          if (refreshRes.ok) {
            // Retry the original request with refreshed cookies
            const retryResponse = await fetch(`${API_BASE_URL}/admin/upload`, {
              method: 'POST',
              body: formData,
              credentials: 'include'
            });
            
            if (!retryResponse.ok) {
              const errorData = await retryResponse.json().catch(() => ({}));
              throw new Error(errorData.error || `Failed to upload ${file.name}`);
            }
            
            const data = await retryResponse.json();
            uploadedUrls.push(data.url);
          } else {
            throw new Error('Session expired');
          }
        } else if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `Failed to upload ${file.name}`);
        } else {
          const data = await response.json();
          uploadedUrls.push(data.url);
        }
      }
    } catch (error) {
      console.error('File upload error:', error);
      setSnackbar({ open: true, message: `File upload failed: ${error.message}`, severity: 'error' });
      setUploadingFiles(false);
      return [];
    }
    
    setUploadingFiles(false);
    return uploadedUrls;
  };

  const handleReply = async () => {
    if (!selected) return;
    
    setSending(true);
    
    try {
      // Upload files first
      const uploadedUrls = await uploadFiles();
      
      // Send reply with attachments
      const response = await fetchWithAuth(`${API_BASE_URL}/admin/email/${selected.id}/reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRF-TOKEN': csrfToken } : {})
        },
        credentials: 'include',
        body: JSON.stringify({ 
          body: reply,
          attachments: uploadedUrls
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send reply');
      }
      
      const data = await response.json();
      setSending(false);
      setReply('');
      setSelectedFiles([]);
      setRefresh(r => !r);
      setModalOpen(false);
      
      // Release lock after successful reply
      if (selected) {
        releaseEmailLock(selected.id);
        setCurrentUserActivity(null);
        updateUserActivity();
      }
      
      setSnackbar({ open: true, message: 'Email sent successfully!', severity: 'success' });
      
    } catch (err) {
      setSending(false);
      setSnackbar({ open: true, message: `Failed to send reply: ${err.message}`, severity: 'error' });
      console.error('Reply error:', err);
    }
  };

  const handleCloseModal = async () => {
    // Release lock when modal is closed
    if (selected) {
      await releaseEmailLock(selected.id);
      setCurrentUserActivity(null);
      updateUserActivity();
    }
    setModalOpen(false);
    setSelected(null);
    setReply('');
    setSelectedFiles([]);
  };

  const renderConfidenceChip = (reply) => {
    if (!reply.confidence_score) return null;
    
    return (
      <Tooltip title={`Confidence: ${(reply.confidence_score * 100).toFixed(1)}%`}>
        <Chip
          label={`${getConfidenceText(reply.confidence_score)} (${(reply.confidence_score * 100).toFixed(0)}%)`}
          color={getConfidenceColor(reply.confidence_score)}
          size="small"
          sx={{ ml: 1 }}
        />
      </Tooltip>
    );
  };

  const renderAutoSendChip = (reply) => {
    if (reply.auto_sent) {
      return <Chip label="Auto-Sent" color="success" size="small" sx={{ ml: 1 }} />;
    }
    if (reply.auto_send_recommended) {
      return <Chip label="Auto-Send Recommended" color="warning" size="small" sx={{ ml: 1 }} />;
    }
    return null;
  };

  // Consolidate the handler to just call the main fetch function
  const handleProcessUnprocessedPayments = () => {
    fetchAndUpdateEmails(true); // Pass true to show notification
  };

  const handleViewBLDetails = async (blNumber) => {
    setSelectedBL(blNumber);
    setLoadingBL(true);
    setBlModalOpen(true);
    
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/api/bills?bl_number=${blNumber}`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.bills && data.bills.length > 0) {
          setBlDetails(data.bills[0]); // Get the first matching bill
        } else {
          setBlDetails(null);
        }
      } else {
        setBlDetails(null);
      }
    } catch (error) {
      console.error('Failed to fetch BL details:', error);
      setBlDetails(null);
    } finally {
      setLoadingBL(false);
    }
  };

  const handleCloseBLModal = () => {
    setBlModalOpen(false);
    setSelectedBL(null);
    setBlDetails(null);
  };

  // Add manual unlock function
  const handleManualUnlock = async (emailId) => {
    try {
      console.log(`🔓 Manually unlocking email ${emailId}`);
      const success = await releaseEmailLock(emailId);
      if (success) {
        setSnackbar({ open: true, message: 'Email unlocked successfully!', severity: 'success' });
        // Refresh the email list to update lock status
        await loadUserActivity();
      } else {
        setSnackbar({ open: true, message: 'Failed to unlock email. It will be automatically cleaned up.', severity: 'warning' });
      }
    } catch (error) {
      console.error('Manual unlock failed:', error);
      setSnackbar({ open: true, message: 'Error unlocking email', severity: 'error' });
    }
  };

  // Clean up any existing locks for current user
  const cleanupExistingLocks = async () => {
    try {
      console.log('🧹 Cleaning up any existing locks for current user');
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/activity`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        const currentUserId = data.current_user_id;
        
        if (data.email_locks && currentUserId) {
          let cleanedCount = 0;
          for (const [emailId, lockInfo] of Object.entries(data.email_locks)) {
            if (lockInfo.user_id === currentUserId) {
              console.log(`🧹 Cleaning up stale lock for email ${emailId}`);
              await releaseEmailLock(emailId);
              cleanedCount++;
            }
          }
          if (cleanedCount > 0) {
            console.log(`✅ Cleaned up ${cleanedCount} stale locks`);
          }
        }
      }
    } catch (error) {
      console.error('Failed to cleanup existing locks:', error);
    }
  };

  // Force unlock specific email
  const forceUnlockEmail = async (emailId) => {
    try {
      console.log(`🔓 Force unlocking email ${emailId}`);
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/${emailId}/force-unlock`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Email ${emailId} force unlocked successfully`, 
          severity: 'success' 
        });
        
        // Refresh the email list
        await loadUserActivity();
      } else {
        const error = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Error: ${error.error || 'Failed to force unlock email'}`, 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error(`Failed to force unlock email ${emailId}:`, error);
      setSnackbar({ 
        open: true, 
        message: 'Error force unlocking email', 
        severity: 'error' 
      });
    }
  };

  // Force unlock all emails (for admin use)
  const forceUnlockAll = async () => {
    try {
      console.log('🔓 Force unlocking all emails');
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/email/force-unlock-all`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Successfully unlocked ${result.deleted_locks} emails`, 
          severity: 'success' 
        });
        
        // Refresh the email list
        await loadUserActivity();
      } else {
        const error = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Error: ${error.error || 'Failed to force unlock all emails'}`, 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Failed to force unlock all emails:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error unlocking emails', 
        severity: 'error' 
      });
    }
  };

  // Process emails without replies
  const processEmailsWithoutReplies = async () => {
    try {
      console.log('🤖 Processing emails without replies...');
      setSnackbar({ 
        open: true, 
        message: 'Processing emails without replies...', 
        severity: 'info' 
      });
      
      const response = await fetchWithAuth(
        `${API_BASE_URL}/admin/process-emails-without-replies`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Successfully processed ${result.processed_count} emails`, 
          severity: 'success' 
        });
        
        // Refresh the email list
        await loadEmails(1, false);
      } else {
        const error = await response.json();
        setSnackbar({ 
          open: true, 
          message: `Error: ${error.error || 'Failed to process emails'}`, 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Failed to process emails without replies:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error processing emails', 
        severity: 'error' 
      });
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {isMobile ? (
        <Box sx={{ width: '100%', p: 2 }}>
          {(filteredEmails || []).map((email, idx) => (
            <Box key={email.id || idx} sx={{ border: '1px solid #ccc', borderRadius: 2, p: 2, mb: 2, backgroundColor: '#f9f9f9' }}>
              <Typography><b>Sender:</b> {email.sender}</Typography>
              <Typography><b>Subject:</b> {email.subject}</Typography>
              <Typography><b>Date:</b> {email.created_at}</Typography>
              <Button 
                size="small" 
                variant="contained" 
                sx={{ mt: 1, fontSize: '0.7rem', px: 1.5, py: 0.5 }} 
                onClick={() => openDetail(email.id)}
                disabled={loadingEmail}
                startIcon={loadingEmail ? <CircularProgress size={12} /> : null}
              >
                {loadingEmail ? 'Loading...' : 'View/Reply'}
              </Button>
            </Box>
          ))}
        </Box>
      ) : (
        <>
          {/* Sidebar for filters */}
          <Box sx={{ width: 260, bgcolor: '#f5f5f5', p: 2 }}>
            <Typography variant="h6" gutterBottom>{t('filters')}</Typography>
            
            {/* Real-time User Activity */}
            <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
              <Typography variant="subtitle2" gutterBottom>
                👥 Active Users ({Object.keys(userActivity || {}).length})
                <Box component="span" sx={{ 
                  ml: 1, 
                  fontSize: '0.7rem', 
                  color: isPageActive ? 'success.main' : 'warning.main',
                  display: 'inline-flex',
                  alignItems: 'center'
                }}>
                  {isPageActive ? '🟢 Live' : '🟡 Reduced'}
                </Box>
              </Typography>
              {Object.keys(userActivity || {}).length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {Object.entries(userActivity || {}).map(([userId, activity]) => (
                    <Box key={userId} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ 
                        width: 8, 
                        height: 8, 
                        borderRadius: '50%', 
                        bgcolor: 'success.main',
                        animation: 'pulse 2s infinite'
                      }} />
                      <Typography variant="caption">
                        User {userId}
                        {activity.current_email_id && (
                          <span style={{ color: 'text.secondary' }}>
                            {' '}(Email #{activity.current_email_id})
                          </span>
                        )}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="caption" color="text.secondary">
                  No active users
                </Typography>
              )}
            </Box>
            
            <TextField label={t('sender')} value={senderFilter} onChange={e => {
              clearTimeout(filterTimeout);
              const val = e.target.value;
              setFilterTimeout(setTimeout(() => {
                setSenderFilter(val);
                loadEmails(1, false); // Reload with new filter
              }, 500));
            }} fullWidth margin="dense" />
            <TextField label={t('blNumber')} value={blFilter} onChange={e => {
              clearTimeout(filterTimeout);
              const val = e.target.value;
              setFilterTimeout(setTimeout(() => {
                setBlFilter(val);
                loadEmails(1, false); // Reload with new filter
              }, 500));
            }} fullWidth margin="dense" />
            <TextField label={t('dateFrom')} type="date" value={dateFrom} onChange={e => {
              setDateFrom(e.target.value);
              loadEmails(1, false); // Reload with new filter
            }} fullWidth margin="dense" InputLabelProps={{ shrink: true }} />
            <TextField label={t('dateTo')} type="date" value={dateTo} onChange={e => {
              setDateTo(e.target.value);
              loadEmails(1, false); // Reload with new filter
            }} fullWidth margin="dense" InputLabelProps={{ shrink: true }} />
            <FormControl fullWidth margin="dense">
              <InputLabel>{t('replyStatus')}</InputLabel>
              <Select value={replyStatus} label={t('replyStatus')} onChange={e => {
                const newValue = e.target.value;
                console.log(`DEBUG: Dropdown changed to '${newValue}'`);
                console.log(`DEBUG: Previous replyStatus was '${replyStatus}'`);
                console.log(`DEBUG: Current filter state:`, { replyStatus, senderFilter, blFilter, dateFrom, dateTo });
                setReplyStatus(newValue);
                console.log(`DEBUG: About to call loadEmails with new filter '${newValue}'`);
                // Use the new value directly instead of relying on state
                loadEmails(1, false, newValue); // Pass the new filter value
              }}>
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="sent">Sent</MenuItem>
                <MenuItem value="ai_ready">AI Reply Ready</MenuItem>
                <MenuItem value="no_reply">No AI Reply</MenuItem>
              </Select>
            </FormControl>
          </Box>
          {/* Main content */}
          <Box sx={{ flex: 1, p: 2 }}>
            <Box mb={2}>
              <Button variant="contained" onClick={() => navigate('/dashboard')}>{t('backToDashboard')}</Button>
              <Button variant="contained" color="success" onClick={handleProcessUnprocessedPayments} disabled={processingPayments} sx={{ ml: 2 }}>
                {processingPayments ? 'Processing...' : 'Process New Payment Emails'}
              </Button>
              <Button variant="outlined" color="warning" onClick={forceUnlockAll} sx={{ ml: 2 }}>
                🔓 Force Unlock All
              </Button>
              <Button variant="outlined" color="info" onClick={processEmailsWithoutReplies} sx={{ ml: 2 }}>
                🤖 Process Emails Without Replies
              </Button>
              
              {/* Email Processor Status */}
              {processorStatus && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    📧 Email Processor Status
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Chip 
                      label={processorStatus.is_running ? '🔄 Running' : '⏸️ Stopped'} 
                      color={processorStatus.is_running ? 'success' : 'default'}
                      size="small"
                    />
                    <Chip 
                      label={`Batch #${processorStatus.current_batch || 0}`} 
                      variant="outlined"
                      size="small"
                    />
                    <Chip 
                      label={`${processorStatus.emails_processed || 0} processed`} 
                      variant="outlined"
                      size="small"
                    />
                    {processorStatus.last_completion && (
                      <Chip 
                        label={`Last: ${new Date(processorStatus.last_completion).toLocaleTimeString()}`} 
                        variant="outlined"
                        size="small"
                      />
                    )}
                  </Box>
                </Box>
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h4" gutterBottom sx={{ flexGrow: 1 }}>
                📬 {t('customerEmails')} 
                {loading && <CircularProgress size={20} sx={{ ml: 2 }} />}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                 Showing {(emails || []).length} of {totalEmails} emails (50 per page)
              </Typography>
            </Box>
            <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 200px)' }}>
              {initialLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
                  <CircularProgress />
                  <Typography sx={{ ml: 2 }}>Loading emails...</Typography>
                </Box>
              ) : (
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Sender</TableCell>
                      <TableCell>Subject</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(filteredEmails || []).map((email) => {
                      const isLocked = (emailLocks || {})[email.id];
                      const isLockedByMe = isLocked && isLocked.user_id === currentUserActivity?.user_id;
                      const usersOnEmail = Object.values(userActivity || {}).filter(
                        activity => activity.current_email_id === email.id
                      );
                      
                      return (
                        <TableRow 
                          key={email.id} 
                          sx={{ 
                            backgroundColor: isLocked ? '#fff3e0' : 'inherit',
                            '&:hover': { backgroundColor: isLocked ? '#ffe0b2' : '#f5f5f5' }
                          }}
                        >
                          <TableCell>{email.id}</TableCell>
                          <TableCell>{email.sender}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {email.subject}
                              {isLocked && (
                                <Chip 
                                  label={isLockedByMe ? "🔒 You're editing" : "🔒 Locked"} 
                                  size="small" 
                                  color={isLockedByMe ? "primary" : "warning"}
                                  variant="outlined"
                                />
                              )}
                                                             {(usersOnEmail || []).length > 0 && !isLocked && (
                                <Chip 
                                                                     label={`👥 ${(usersOnEmail || []).length} viewing`}  
                                  size="small" 
                                  color="info"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{formatHKDateTimeShort(email.created_at)}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {(() => {
                                // Debug: Log the status calculation for this email
                                const status = email.has_replies ? 
                                  (email.has_sent_replies ? "Sent" : "AI Reply Ready") : 
                                  "No AI Reply";
                                console.log(`DEBUG: Email ${email.id} status: has_replies=${email.has_replies}, has_sent_replies=${email.has_sent_replies} → ${status}`);
                                
                                // Check if this is a draft reply (AI generated but not sent)
                                const isDraftReply = email.has_replies && !email.has_sent_replies;
                                const isSentReply = email.has_replies && email.has_sent_replies;
                                const hasNoReply = !email.has_replies;
                                
                                if (isDraftReply) {
                                  return <Chip label="AI Reply Ready" color="success" size="small" />;
                                } else if (isSentReply) {
                                  return <Chip label="Sent" color="primary" size="small" />;
                                } else {
                                  return <Chip label="No AI Reply" color="error" size="small" />;
                                }
                              })()}
                              {email.reply_count > 0 && (
                                <Chip label={`${email.reply_count} replies`} size="small" variant="outlined" />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              <Button 
                                size="small" 
                                variant="contained" 
                                onClick={() => openDetail(email.id)}
                                disabled={loadingEmail || (isLocked && !isLockedByMe)}
                                startIcon={loadingEmail ? <CircularProgress size={12} /> : null}
                                sx={{ 
                                  fontSize: '0.7rem', 
                                  px: 1.5, 
                                  py: 0.5,
                                  opacity: (isLocked && !isLockedByMe) || loadingEmail ? 0.5 : 1
                                }}
                              >
                                {loadingEmail ? 'Loading...' : (isLocked && !isLockedByMe ? 'Locked' : 'View/Reply')}
                              </Button>
                              
                              {/* Manual unlock button for emails locked by current user */}
                              {isLocked && isLockedByMe && (
                                <Button 
                                  size="small" 
                                  variant="outlined" 
                                  color="warning"
                                  onClick={() => handleManualUnlock(email.id)}
                                  sx={{ 
                                    fontSize: '0.7rem', 
                                    px: 1.5, 
                                    py: 0.5
                                  }}
                                >
                                  🔓 Unlock
                                </Button>
                              )}
                              
                              {/* Force unlock button for any locked email (admin) */}
                              {isLocked && !isLockedByMe && (
                                <Button 
                                  size="small" 
                                  variant="outlined" 
                                  color="error"
                                  onClick={() => forceUnlockEmail(email.id)}
                                  sx={{ 
                                    fontSize: '0.7rem', 
                                    px: 1.5, 
                                    py: 0.5
                                  }}
                                >
                                  ⚡ Force Unlock
                                </Button>
                              )}
                            </Box>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </TableContainer>
            
            {/* Load More Button */}
            {hasMore && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button 
                  variant="outlined" 
                  onClick={loadMore} 
                  disabled={loading || isIngesting}
                  startIcon={loading ? <CircularProgress size={16} /> : null}
                >
                  {loading ? 'Loading...' : 'Load More Emails'}
                </Button>
              </Box>
            )}
            
            {/* No more emails message */}
                         {!hasMore && (emails || []).length > 0 && (
              <Box sx={{ textAlign: 'center', mt: 2, color: 'text.secondary' }}>
                <Typography variant="body2">
                  No more emails to load
                </Typography>
              </Box>
            )}
          </Box>
        </>
      )}
      {/* Modal for email detail */}
      <Modal open={modalOpen} onClose={handleCloseModal}>
        <Box sx={modalStyle}>
          {selected && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Email Detail</Typography>
                
                {/* Collaboration Status */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {(emailLocks || {})[selected.id] && (
                    <Chip 
                                              label={`🔒 Locked by User ${(emailLocks || {})[selected.id].user_id}`}  
                      color="warning" 
                      size="small"
                    />
                  )}
                                     {(Object.values(userActivity || {}).filter(
                     activity => activity.current_email_id === selected.id
                   ) || []).length > 0 && (
                    <Chip 
                                             label={`👥 ${(Object.values(userActivity || {}).filter(
                         activity => activity.current_email_id === selected.id
                       ) || []).length} users viewing`}  
                      color="info" 
                      size="small"
                    />
                  )}
                </Box>
              </Box>
              
              <Typography><strong>From:</strong> {selected.sender}</Typography>
              <Typography><strong>Subject:</strong> {selected.subject}</Typography>
              <Typography><strong>Date:</strong> {selected.created_at}</Typography>
              <Typography><strong>Body:</strong></Typography>
              <Box sx={{ 
                maxHeight: 200, 
                overflowY: 'auto', 
                border: '1px solid #ccc', 
                p: 1, 
                mb: 2,
                bgcolor: '#f9f9f9'
              }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {selected.body}
                </Typography>
              </Box>
              
              {/* Customer Attachments Display */}
              {selected && selected.attachments && Array.isArray(selected.attachments) && selected.attachments.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">{t('customerAttachments') || 'Customer Attachments'}</Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
                                         Found {((selected && selected.attachments) || []).length} attachment(s)
                  </Typography>
                  <List>
                    {((selected && selected.attachments) || []).map((attachment, i) => {
                      const isUrl = typeof attachment === 'string' && (attachment.startsWith('http') || attachment.startsWith('https'));
                      const isCloudinary = isUrl && attachment.includes('cloudinary');
                      const fileName = typeof attachment === 'string' ? attachment.split('/').pop() || attachment : `Attachment ${i + 1}`;
                      
                      return (
                        <ListItem key={i}>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <span>📎 {fileName}</span>
                                {isUrl && (
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    onClick={() => window.open(attachment, '_blank')}
                                  >
                                    View
                                  </Button>
                                )}
                              </Box>
                            }
                            secondary={
                              <Box>
                                <span>{isCloudinary ? 'Cloudinary URL' : isUrl ? 'External URL' : 'Local file'}</span>
                                {!isUrl && (
                                  <Typography variant="caption" sx={{ display: 'block', color: 'warning.main' }}>
                                    Local file path - may not be accessible
                                  </Typography>
                                )}
                                <Typography variant="caption" sx={{ display: 'block', color: 'info.main', fontSize: '0.7rem' }}>
                                  Raw: {JSON.stringify(attachment)}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                      );
                    })}
                  </List>
                </Box>
              )}
              
              {/* Debug info for attachments */}
                             {selected && (!selected.attachments || ((selected && selected.attachments) || []).length === 0) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    No attachments found for this email
                  </Typography>
                </Box>
              )}
              
              {/* BL Number Buttons - Moved to prominent location */}
              {selected && selected.bl_numbers && selected.bl_numbers.length > 0 && (
                <Box sx={{ mt: 2, p: 2, bgcolor: '#f0f8ff', borderRadius: 1, border: '1px solid #e3f2fd' }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, color: 'primary.main' }}>
                    📋 BL Numbers Found in This Email:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selected.bl_numbers.map((blNumber, index) => (
                      <Button
                        key={index}
                        size="small"
                        variant="contained"
                        onClick={() => handleViewBLDetails(blNumber)}
                        sx={{ 
                          fontSize: '0.8rem', 
                          px: 2, 
                          py: 1,
                          bgcolor: 'primary.main',
                          '&:hover': { bgcolor: 'primary.dark' }
                        }}
                      >
                        📋 {blNumber}
                      </Button>
                    ))}
                  </Box>
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2">{t('replies')}</Typography>
              <List>
                {((selected && selected.replies) || []).map(r => (
                  <ListItem key={r.id} alignItems="flex-start">
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <span>{r.sender}</span>
                          {renderConfidenceChip(r)}
                          {renderAutoSendChip(r)}
                        </Box>
                      }
                      secondary={<>
                        <span style={{ whiteSpace: 'pre-line' }}>{r.body}</span><br />
                        <span style={{ fontSize: 12, color: '#888' }}>{formatHKDateTimeShort(r.created_at)}</span>
                        {r.auto_sent && (
                          <Alert severity="success" sx={{ mt: 1, fontSize: '0.75rem' }}>
                            This email was automatically sent by AI (Confidence: {(r.confidence_score * 100).toFixed(1)}%)
                          </Alert>
                        )}
                      </>}
                    />
                  </ListItem>
                ))}
              </List>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Quick Replies:</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {(cannedResponses || []).map((response, index) => (
                    <Chip
                      key={index}
                      label={response.title}
                      onClick={() => setReply(response.body)}
                      variant="outlined"
                      clickable
                      size="small"
                    />
                  ))}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column', width: '100%' }}>
                <TextField
                  label={t('reply')}
                  multiline
                  minRows={2}
                  fullWidth
                  value={reply}
                  onChange={e => setReply(e.target.value)}
                />
                
                {/* File Upload Section */}
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                  <input
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
                    style={{ display: 'none' }}
                    id="file-upload"
                    multiple
                    type="file"
                    onChange={handleFileSelect}
                  />
                  <label htmlFor="file-upload">
                    <Button
                      variant="outlined"
                      component="span"
                      disabled={uploadingFiles}
                      startIcon={<AttachFileIcon />}
                    >
                      {uploadingFiles ? 'Uploading...' : 'Attach Files'}
                    </Button>
                  </label>
                  
                  <Button 
                    variant="contained" 
                    onClick={handleReply} 
                    disabled={sending || !reply.trim() || uploadingFiles}
                  >
                    {sending ? t('sending') : t('send')}
                  </Button>
                </Box>
                
                {/* Selected Files Preview */}
                {selectedFiles.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      Selected Files ({selectedFiles.length}):
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
                      {selectedFiles.map((file, index) => (
                        <Chip
                          key={index}
                          label={file.name}
                          onDelete={() => handleRemoveFile(index)}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
              {/* Outgoing Attachments Preview */}
              {selected && selected.attachments && Array.isArray(selected.attachments) && ((selected && selected.attachments) || []).length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">{t('outgoingAttachments')}</Typography>
                  <List>
                    {((selected && selected.attachments) || []).map((url, i) => (
                      <ListItem key={i}>
                        <a href={url} target="_blank" rel="noopener noreferrer">{t('attachment')} {i + 1}</a>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </>
          )}
        </Box>
      </Modal>
      
      {/* BL Details Modal */}
      <Modal open={blModalOpen} onClose={handleCloseBLModal}>
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '95%',
          maxWidth: 1200,
          maxHeight: '95vh',
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 4,
          overflow: 'auto'
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              📋 BL Details: {selectedBL}
            </Typography>
            <Button onClick={handleCloseBLModal} variant="outlined" size="small">
              Close
            </Button>
          </Box>
          
          {loadingBL ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Loading BL details...</Typography>
            </Box>
          ) : blDetails ? (
            <Box>
              {/* PDF Viewer Section - Most Important */}
              {blDetails.pdf_filename ? (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>📄 Bill of Lading Document</Typography>
                  <Box sx={{ 
                    border: '1px solid #ddd', 
                    borderRadius: 1, 
                    overflow: 'hidden',
                    mb: 2
                  }}>
                    <iframe
                      src={blDetails.pdf_filename}
                      width="100%"
                      height="500px"
                      style={{ border: 'none' }}
                      title="Bill of Lading PDF Preview"
                    />
                  </Box>
                  <Button
                    variant="contained"
                    size="small"
                    href={blDetails.pdf_filename}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ mr: 1 }}
                  >
                    Open in New Tab
                  </Button>
                </Box>
              ) : (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#fff3cd', borderRadius: 1, border: '1px solid #ffeaa7' }}>
                  <Typography variant="body2" color="warning.main">
                    ⚠️ No Bill of Lading PDF available for this BL number.
                  </Typography>
                </Box>
              )}
              
              <Typography variant="subtitle1" gutterBottom>Bill Information</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 3 }}>
                <Box>
                  <Typography variant="body2"><strong>BL Number:</strong> {blDetails.bl_number}</Typography>
                  <Typography variant="body2"><strong>Status:</strong> {blDetails.status}</Typography>
                  <Typography variant="body2"><strong>Service Fee:</strong> ${blDetails.service_fee || 0}</Typography>
                  <Typography variant="body2"><strong>CTN Fee:</strong> ${blDetails.ctn_fee || 0}</Typography>
                  <Typography variant="body2"><strong>Container Numbers:</strong> {blDetails.container_numbers || 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Flight/Vessel:</strong> {blDetails.flight_or_vessel || 'N/A'}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2"><strong>Container Count:</strong> {blDetails.container_count || 0}</Typography>
                  <Typography variant="body2"><strong>Total Weight:</strong> {blDetails.total_weight_kg || 0} kg</Typography>
                  <Typography variant="body2"><strong>Shipment Type:</strong> {blDetails.shipment_type || 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Unique Number:</strong> {blDetails.unique_number || 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Port of Loading:</strong> {blDetails.port_of_loading || 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Port of Discharge:</strong> {blDetails.port_of_discharge || 'N/A'}</Typography>
                </Box>
              </Box>
              
              {/* Shipping Details */}
              {(blDetails.shipper || blDetails.consignee || blDetails.notify_party) && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>Shipping Details</Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    {blDetails.shipper && (
                      <Box>
                        <Typography variant="body2"><strong>Shipper:</strong></Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>
                          {blDetails.shipper}
                        </Typography>
                      </Box>
                    )}
                    {blDetails.consignee && (
                      <Box>
                        <Typography variant="body2"><strong>Consignee:</strong></Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>
                          {blDetails.consignee}
                        </Typography>
                      </Box>
                    )}
                    {blDetails.notify_party && (
                      <Box sx={{ gridColumn: '1 / -1' }}>
                        <Typography variant="body2"><strong>Notify Party:</strong></Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>
                          {blDetails.notify_party}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Box>
              )}
              
              {/* Product Description */}
              {blDetails.product_description && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>Product Description</Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>
                    {blDetails.product_description}
                  </Typography>
                </Box>
              )}
              
              {/* Invoice Section */}
              {blDetails.invoice_filename && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>📄 Invoice</Typography>
                  <Button
                    variant="contained"
                    size="small"
                    href={blDetails.invoice_filename}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ mr: 1 }}
                  >
                    View Invoice
                  </Button>
                </Box>
              )}
              
              {/* Receipt Section */}
              {blDetails.receipt_filename && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>🧾 Receipt</Typography>
                  <Button
                    variant="contained"
                    size="small"
                    href={blDetails.receipt_filename}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ mr: 1 }}
                  >
                    View Receipt
                  </Button>
                </Box>
              )}
              
              {/* Customer Documents */}
              {blDetails.customer_invoice && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>📋 Customer Documents</Typography>
                  <Button
                    variant="contained"
                    size="small"
                    href={blDetails.customer_invoice}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ mr: 1 }}
                  >
                    View Customer Invoice
                  </Button>
                </Box>
              )}
              
              {blDetails.customer_packing_list && (
                <Button
                  variant="contained"
                  size="small"
                  href={blDetails.customer_packing_list}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ mr: 1 }}
                >
                  View Packing List
                </Button>
              )}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', p: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No details found for BL: {selectedBL}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                This BL number may not exist in the system or may not have been processed yet.
              </Typography>
            </Box>
          )}
        </Box>
      </Modal>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
