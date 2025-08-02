#!/usr/bin/env python3
"""
Simple Web Interface for Testing Outlook API
Accessible from iPad browser to view AI drafts
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuration - Update with your actual backend URL
BACKEND_URL = "http://localhost:5000"  # Change to your actual backend URL

# HTML Template for the interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IQS Trade - AI Drafts Viewer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #6c757d;
            font-size: 14px;
            margin-top: 5px;
        }
        .drafts-list {
            margin-top: 20px;
        }
        .draft-item {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .draft-item:hover {
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .draft-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .draft-subject {
            font-weight: 600;
            color: #333;
            font-size: 16px;
        }
        .draft-date {
            color: #6c757d;
            font-size: 14px;
        }
        .draft-from {
            color: #495057;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .draft-preview {
            color: #6c757d;
            font-size: 14px;
            line-height: 1.4;
            max-height: 60px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .draft-actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: #000;
        }
        .draft-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        .original-email {
            background: #e9ecef;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Drafts Viewer</h1>
            <p>View and manage AI-generated email drafts</p>
        </div>
        
        <div class="content">
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="processed-count">-</div>
                    <div class="stat-label">Processed Emails</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="draft-count">-</div>
                    <div class="stat-label">Available Drafts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sent-count">-</div>
                    <div class="stat-label">Sent Replies</div>
                </div>
            </div>
            
            <div id="drafts-container">
                <div class="loading">Loading drafts...</div>
            </div>
        </div>
    </div>
    
    <!-- Modal for viewing draft details -->
    <div id="draftModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2 id="modal-title">Draft Details</h2>
            <div id="modal-content"></div>
        </div>
    </div>
    
    <script>
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
        });
        
        function loadData() {
            // Load status
            fetch('{{ url_for("get_status") }}')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('processed-count').textContent = data.data.processed_emails;
                        document.getElementById('draft-count').textContent = data.data.available_drafts;
                        document.getElementById('sent-count').textContent = data.data.sent_replies;
                    }
                })
                .catch(error => {
                    console.error('Error loading status:', error);
                });
            
            // Load drafts
            fetch('{{ url_for("get_drafts") }}')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayDrafts(data.data);
                    } else {
                        document.getElementById('drafts-container').innerHTML = 
                            '<div class="error">Error loading drafts: ' + data.message + '</div>';
                    }
                })
                .catch(error => {
                    console.error('Error loading drafts:', error);
                    document.getElementById('drafts-container').innerHTML = 
                        '<div class="error">Error loading drafts: ' + error.message + '</div>';
                });
        }
        
        function displayDrafts(drafts) {
            const container = document.getElementById('drafts-container');
            
            if (drafts.length === 0) {
                container.innerHTML = '<div class="loading">No drafts available</div>';
                return;
            }
            
            container.innerHTML = drafts.map(draft => `
                <div class="draft-item" onclick="viewDraft(${draft.reply_id})">
                    <div class="draft-header">
                        <div class="draft-subject">${draft.subject || 'No Subject'}</div>
                        <div class="draft-date">${formatDate(draft.draft_date)}</div>
                    </div>
                    <div class="draft-from">From: ${draft.from_addr}</div>
                    <div class="draft-preview">${draft.draft_content.substring(0, 150)}...</div>
                    <div class="draft-actions">
                        <button class="btn btn-primary" onclick="event.stopPropagation(); viewDraft(${draft.reply_id})">View</button>
                        <button class="btn btn-success" onclick="event.stopPropagation(); markAsSent(${draft.reply_id})">Mark as Sent</button>
                    </div>
                </div>
            `).join('');
        }
        
        function viewDraft(replyId) {
            fetch(`{{ url_for("get_draft_content") }}?replyId=${replyId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const modal = document.getElementById('draftModal');
                        const modalContent = document.getElementById('modal-content');
                        
                        modalContent.innerHTML = `
                            <div class="draft-content">${data.data.draft_content}</div>
                            <div class="original-email">
                                <strong>Original Email:</strong><br>
                                <strong>Subject:</strong> ${data.data.original_email.subject}<br>
                                <strong>From:</strong> ${data.data.original_email.from_addr}<br>
                                <strong>Date:</strong> ${formatDate(data.data.original_email.created_at)}<br><br>
                                ${data.data.original_email.body}
                            </div>
                            <div class="draft-actions">
                                <button class="btn btn-success" onclick="markAsSent(${replyId})">Mark as Sent</button>
                                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                            </div>
                        `;
                        
                        modal.style.display = 'block';
                    } else {
                        alert('Error loading draft: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error loading draft:', error);
                    alert('Error loading draft: ' + error.message);
                });
        }
        
        function markAsSent(replyId) {
            if (confirm('Mark this draft as sent?')) {
                fetch('{{ url_for("mark_draft_sent") }}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        replyId: replyId,
                        sentBy: 'web_interface'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Draft marked as sent successfully!');
                        closeModal();
                        loadData(); // Refresh the list
                    } else {
                        alert('Error marking draft as sent: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error marking draft as sent:', error);
                    alert('Error marking draft as sent: ' + error.message);
                });
            }
        }
        
        function closeModal() {
            document.getElementById('draftModal').style.display = 'none';
        }
        
        function formatDate(dateString) {
            if (!dateString) return 'Unknown';
            const date = new Date(dateString);
            return date.toLocaleString();
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('draftModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main interface page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """Get system status from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/outlook/status")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to backend: {str(e)}'
        })

@app.route('/api/drafts')
def get_drafts():
    """Get drafts from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/outlook/fetch-drafts")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to backend: {str(e)}'
        })

@app.route('/api/draft-content')
def get_draft_content():
    """Get specific draft content from backend"""
    try:
        reply_id = request.args.get('replyId')
        response = requests.get(f"{BACKEND_URL}/api/outlook/get-draft-content?replyId={reply_id}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to backend: {str(e)}'
        })

@app.route('/api/mark-sent', methods=['POST'])
def mark_draft_sent():
    """Mark draft as sent via backend"""
    try:
        data = request.get_json()
        response = requests.post(f"{BACKEND_URL}/api/outlook/send-draft", json=data)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to backend: {str(e)}'
        })

if __name__ == '__main__':
    print("🚀 Starting Outlook Test Interface...")
    print(f"📱 Access from your iPad at: http://YOUR_COMPUTER_IP:5001")
    print("💡 Make sure your backend is running on port 5000")
    app.run(host='0.0.0.0', port=5001, debug=True) 