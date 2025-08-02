# 📱 iPad Setup Guide for AI Drafts Viewer

## 🎯 **Overview**
This guide will help you access your AI-generated email drafts from your iPad using a simple web interface.

## 🔧 **Step 1: Start Your Backend Server**

First, make sure your main backend server is running:

```bash
cd backend
python run_local.py
```

Your backend should be running on `http://localhost:5000`

## 🔧 **Step 2: Start the Test Interface**

In a new terminal window, start the test interface:

```bash
cd backend
python outlook_test_interface.py
```

This will start a web server on port 5001.

## 🌐 **Step 3: Find Your Computer's IP Address**

### **On Windows:**
1. Open Command Prompt
2. Type: `ipconfig`
3. Look for "IPv4 Address" under your active network adapter
4. Note the IP address (e.g., `192.168.1.100`)

### **On Mac:**
1. Open System Preferences → Network
2. Select your active connection
3. Note the IP address

## 📱 **Step 4: Access from iPad**

1. **On your iPad**, open Safari
2. **Go to:** `http://YOUR_COMPUTER_IP:5001`
   - Example: `http://192.168.1.100:5001`
3. **You should see** the AI Drafts Viewer interface

## 🎯 **What You Can Do:**

### **View System Status:**
- See how many emails have been processed
- View available AI drafts
- Check sent replies count

### **Browse AI Drafts:**
- See all AI-generated email responses
- View original emails and AI drafts
- Check confidence scores

### **Manage Drafts:**
- View full draft content
- Mark drafts as sent
- Track response status

## 🔄 **Testing the Full Workflow:**

### **1. Send Test Emails:**
```bash
cd backend
python simple_email_sender.py
```

### **2. Process Emails:**
```bash
python email_ingestor.py
```

### **3. View Results on iPad:**
- Refresh the web interface
- See new AI drafts appear
- Review and manage responses

## 🛠 **Troubleshooting:**

### **Can't Access from iPad:**
1. **Check Firewall:** Make sure port 5001 is open
2. **Check Network:** Ensure iPad and computer are on same WiFi
3. **Try Different Browser:** Use Chrome or Firefox if Safari doesn't work

### **No Drafts Showing:**
1. **Check Backend:** Make sure `run_local.py` is running
2. **Check Email Processing:** Run `email_ingestor.py` to process emails
3. **Check Database:** Verify emails are being processed

### **Connection Errors:**
1. **Update IP Address:** Your computer's IP might have changed
2. **Restart Servers:** Stop and restart both servers
3. **Check Ports:** Make sure ports 5000 and 5001 are available

## 📋 **API Endpoints Available:**

- `GET /api/outlook/status` - System status
- `GET /api/outlook/fetch-drafts` - List all drafts
- `GET /api/outlook/get-draft-content?replyId=X` - Get specific draft
- `POST /api/outlook/send-draft` - Mark draft as sent

## 🎉 **Success Indicators:**

✅ **Backend running** - No errors in terminal  
✅ **Test interface accessible** - Can open in browser  
✅ **iPad can connect** - Interface loads on iPad  
✅ **Drafts appear** - AI-generated responses show up  
✅ **Can view details** - Click on drafts to see content  

## 🔮 **Next Steps:**

Once this is working, you can:
1. **Create a proper Outlook add-in** using the API
2. **Add more features** like draft editing
3. **Integrate with Outlook** for seamless workflow
4. **Add authentication** for security

## 📞 **Need Help?**

If you encounter issues:
1. Check the terminal output for error messages
2. Verify your network configuration
3. Test with a different device first
4. Check that all required services are running 