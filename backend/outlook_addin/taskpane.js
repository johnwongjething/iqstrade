// IQS Trade AI Assistant - Outlook Add-in
// Handles communication with the backend API and Outlook

let currentEmailData = null;
let currentDraft = null;
const API_BASE_URL = 'http://192.168.50.244:5000/api/outlook';

Office.onReady((info) => {
    if (info.host === Office.HostType.Outlook) {
        document.getElementById('sideload-msg').style.display = 'none';
        document.getElementById('app-body').style.display = 'flex';
        
        // Initialize the add-in
        initializeAddIn();
    }
});

function initializeAddIn() {
    // Load current email data
    loadCurrentEmail();
    
    // Load AI drafts
    loadDrafts();
}

function loadCurrentEmail() {
    Office.context.mailbox.item.getAsync((result) => {
        if (result.status === Office.AsyncResultStatus.Succeeded) {
            const item = result.value;
            
            currentEmailData = {
                subject: item.subject || 'No Subject',
                from: item.from?.emailAddress || 'Unknown',
                body: item.body?.text || '',
                messageId: item.itemId || '',
                attachments: []
            };
            
            // Update UI
            document.getElementById('email-from').textContent = currentEmailData.from;
            document.getElementById('email-subject').textContent = currentEmailData.subject;
            
            // Get attachments if any
            if (item.attachments && item.attachments.length > 0) {
                currentEmailData.attachments = item.attachments.map(att => att.name);
            }
            
        } else {
            console.error('Failed to get email data:', result.error);
            showError('Failed to load email data');
        }
    });
}

function loadDrafts() {
    showLoading();
    
    // First, try to find drafts for the current email
    if (currentEmailData) {
        findDraftsForCurrentEmail();
    } else {
        // Fallback: load all drafts
        loadAllDrafts();
    }
}

function findDraftsForCurrentEmail() {
    // This would need to be implemented based on your database structure
    // For now, we'll load all drafts and filter by subject/sender
    loadAllDrafts();
}

function loadAllDrafts() {
    fetch(`${API_BASE_URL}/fetch-drafts?limit=20`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displayDrafts(data.data);
            } else {
                showError(data.message || 'Failed to load drafts');
            }
        })
        .catch(error => {
            console.error('Error loading drafts:', error);
            hideLoading();
            showError('Network error: ' + error.message);
        });
}

function displayDrafts(drafts) {
    const draftsList = document.getElementById('drafts-list');
    const noDrafts = document.getElementById('no-drafts');
    
    if (drafts.length === 0) {
        draftsList.innerHTML = '';
        noDrafts.style.display = 'block';
        return;
    }
    
    noDrafts.style.display = 'none';
    
    // Filter drafts for current email if possible
    let relevantDrafts = drafts;
    if (currentEmailData) {
        relevantDrafts = drafts.filter(draft => 
            draft.subject === currentEmailData.subject ||
            draft.from_addr === currentEmailData.from
        );
        
        // If no exact matches, show all drafts
        if (relevantDrafts.length === 0) {
            relevantDrafts = drafts;
        }
    }
    
    draftsList.innerHTML = relevantDrafts.map(draft => `
        <div class="draft-item" onclick="viewDraft(${draft.reply_id})">
            <div class="draft-header">
                <div class="draft-subject">${escapeHtml(draft.subject)}</div>
                <div class="draft-date">${formatDate(draft.draft_date)}</div>
            </div>
            <div class="draft-from">From: ${escapeHtml(draft.from_addr)}</div>
            <div class="draft-preview">${escapeHtml(draft.draft_content.substring(0, 100))}...</div>
            <div class="draft-actions">
                <button class="ms-Button ms-Button--primary" onclick="event.stopPropagation(); viewDraft(${draft.reply_id})">
                    View
                </button>
                <button class="ms-Button ms-Button--primary" onclick="event.stopPropagation(); sendDraft(${draft.reply_id})">
                    Send
                </button>
            </div>
        </div>
    `).join('');
}

function viewDraft(replyId) {
    fetch(`${API_BASE_URL}/get-draft-content?replyId=${replyId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentDraft = data.data;
                showDraftModal(data.data);
            } else {
                showError(data.message || 'Failed to load draft content');
            }
        })
        .catch(error => {
            console.error('Error loading draft content:', error);
            showError('Network error: ' + error.message);
        });
}

function showDraftModal(draftData) {
    const modal = document.getElementById('draft-modal');
    const content = document.getElementById('draft-content');
    
    content.innerHTML = `
        <div class="draft-full-content">
            <pre>${escapeHtml(draftData.draft_content)}</pre>
        </div>
        <div class="draft-meta">
            <p><strong>Confidence Score:</strong> ${draftData.confidence_score || 'N/A'}</p>
            <p><strong>Original Email:</strong></p>
            <div class="original-email">
                <p><strong>Subject:</strong> ${escapeHtml(draftData.original_email.subject)}</p>
                <p><strong>From:</strong> ${escapeHtml(draftData.original_email.from_addr)}</p>
                <p><strong>Date:</strong> ${formatDate(draftData.original_email.created_at)}</p>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('draft-modal').style.display = 'none';
    currentDraft = null;
}

function sendDraft(replyId) {
    if (!replyId && currentDraft) {
        // Get reply ID from current draft
        replyId = currentDraft.reply_id;
    }
    
    if (!replyId) {
        showError('No draft selected');
        return;
    }
    
    // Mark draft as sent in backend
    fetch(`${API_BASE_URL}/send-draft`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            replyId: replyId,
            sentBy: 'outlook_addin'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Send the email through Outlook
            sendEmailThroughOutlook(replyId);
        } else {
            showError(data.message || 'Failed to mark draft as sent');
        }
    })
    .catch(error => {
        console.error('Error sending draft:', error);
        showError('Network error: ' + error.message);
    });
}

function sendEmailThroughOutlook(replyId) {
    // Get the draft content
    fetch(`${API_BASE_URL}/get-draft-content?replyId=${replyId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const draftContent = data.data.draft_content;
                
                // Create a new email with the draft content
                Office.context.mailbox.displayReplyForm(draftContent, (result) => {
                    if (result.status === Office.AsyncResultStatus.Succeeded) {
                        showSuccess('Email prepared for sending!');
                        closeModal();
                        loadDrafts(); // Refresh the list
                    } else {
                        showError('Failed to create reply: ' + result.error.message);
                    }
                });
            } else {
                showError('Failed to get draft content');
            }
        })
        .catch(error => {
            console.error('Error getting draft content:', error);
            showError('Network error: ' + error.message);
        });
}

function processCurrentEmail() {
    if (!currentEmailData) {
        showError('No email data available');
        return;
    }
    
    showLoading();
    
    // Send current email to backend for AI processing
    fetch(`${API_BASE_URL}/process-email`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            subject: currentEmailData.subject,
            body: currentEmailData.body,
            from: currentEmailData.from,
            messageId: currentEmailData.messageId,
            attachments: currentEmailData.attachments,
            userId: 'outlook_user'
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showSuccess('Email processed! Check for new AI drafts.');
            loadDrafts(); // Refresh the list
        } else {
            showError(data.message || 'Failed to process email');
        }
    })
    .catch(error => {
        console.error('Error processing email:', error);
        hideLoading();
        showError('Network error: ' + error.message);
    });
}

// UI Helper Functions
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('content').style.display = 'block';
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error').style.display = 'block';
    document.getElementById('loading').style.display = 'none';
    document.getElementById('content').style.display = 'none';
}

function showSuccess(message) {
    // Simple success message - you could enhance this with a toast notification
    alert(message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('draft-modal');
    if (event.target === modal) {
        closeModal();
    }
} 