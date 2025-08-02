# 📧 Outlook Add-in Setup Guide for Company Users

## 🎯 **Overview**
This guide will help you install and use the IQS Trade AI Assistant add-in in Outlook, allowing company users to view and send AI-generated email responses directly from Outlook.

## 🚀 **What the Add-in Does:**

✅ **Shows AI drafts** for the current email you're viewing  
✅ **One-click send** AI-generated responses  
✅ **Process emails** with AI if no draft exists  
✅ **Seamless integration** with Outlook interface  

## 📋 **Prerequisites:**

1. **Outlook Desktop** (Windows/Mac) or **Outlook Web**
2. **Admin access** to install add-ins (for first-time setup)
3. **Backend server running** (`python run_local.py`)
4. **Test interface running** (`python outlook_test_interface.py`)

## 🔧 **Step 1: Prepare Your Server**

### **Start Backend Server:**
```bash
cd backend
python run_local.py
```

### **Start Test Interface:**
```bash
python outlook_test_interface.py
```

### **Verify URLs are accessible:**
- Backend: `http://192.168.50.244:5000`
- Test Interface: `http://192.168.50.244:5001`
- Add-in Files: `http://192.168.50.244:5000/outlook_addin/manifest.xml`

## 🔧 **Step 2: Install Add-in in Outlook**

### **For Outlook Desktop (Windows/Mac):**

1. **Open Outlook**
2. **Go to:** File → Manage Add-ins
3. **Click:** "Add from File" or "Add from URL"
4. **Enter URL:** `http://192.168.50.244:5000/outlook_addin/manifest.xml`
5. **Click:** Install
6. **Restart Outlook** if prompted

### **For Outlook Web:**

1. **Open Outlook Web** in browser
2. **Click:** Settings (gear icon) → View all Outlook settings
3. **Go to:** Mail → Customize actions → Add-ins
4. **Click:** "Add from URL"
5. **Enter URL:** `http://192.168.50.244:5000/outlook_addin/manifest.xml`
6. **Click:** Install

### **For Organization Deployment:**

1. **Admin Center:** Go to Microsoft 365 Admin Center
2. **Settings:** Organization profile → Add-ins
3. **Upload:** Upload the manifest.xml file
4. **Deploy:** Assign to users or groups

## 🎯 **Step 3: Using the Add-in**

### **View AI Drafts:**
1. **Open any email** in Outlook
2. **Look for:** "AI Assistant" button in the ribbon
3. **Click:** AI Assistant button
4. **View:** AI-generated responses in the taskpane

### **Send AI Response:**
1. **Click:** "View" on any draft
2. **Review:** The AI-generated content
3. **Click:** "Send Response"
4. **Confirm:** The email will be prepared for sending

### **Process New Email:**
1. **If no drafts exist** for an email
2. **Click:** "Process Email with AI"
3. **Wait:** For AI to generate a response
4. **View:** The new draft appears

## 🛠 **Troubleshooting:**

### **Add-in Not Appearing:**
1. **Check manifest URL:** `http://192.168.50.244:5000/outlook_addin/manifest.xml`
2. **Verify server running:** Both backend and test interface
3. **Check network:** Ensure Outlook can access your server
4. **Restart Outlook:** Sometimes required after installation

### **Add-in Not Loading:**
1. **Check browser console** for errors
2. **Verify API endpoints:** Test `http://192.168.50.244:5000/api/outlook/status`
3. **Check CORS settings:** Ensure your server allows Outlook domains
4. **Update IP address:** If your computer's IP changed

### **No Drafts Showing:**
1. **Check backend:** Ensure `run_local.py` is running
2. **Process emails:** Run `python email_ingestor.py` to create drafts
3. **Check database:** Verify emails are being processed
4. **Refresh add-in:** Close and reopen the taskpane

## 🔒 **Security Considerations:**

### **For Production:**
1. **Use HTTPS:** Deploy with SSL certificates
2. **Domain verification:** Register your domain with Microsoft
3. **User authentication:** Add login requirements
4. **Rate limiting:** Prevent abuse of AI processing

### **For Development:**
1. **Local network only:** Keep on internal network
2. **Test users only:** Limit to development team
3. **Monitor usage:** Track API calls and errors

## 📱 **User Experience:**

### **What Users See:**
- **AI Assistant button** in Outlook ribbon
- **Taskpane with drafts** when viewing emails
- **One-click send** for AI responses
- **Processing status** for new emails

### **Workflow:**
1. **Receive email** → Open in Outlook
2. **Click AI Assistant** → View available drafts
3. **Review draft** → Click "Send Response"
4. **Confirm send** → AI response is sent

## 🎉 **Success Indicators:**

✅ **Add-in appears** in Outlook ribbon  
✅ **Taskpane opens** when clicking AI Assistant  
✅ **Drafts load** from your database  
✅ **Send function** works properly  
✅ **New emails** can be processed  

## 🔮 **Next Steps:**

### **For Company Deployment:**
1. **Create proper icons** (replace placeholder files)
2. **Deploy to production** server with HTTPS
3. **Train users** on the add-in functionality
4. **Monitor usage** and gather feedback

### **For Development:**
1. **Test with real emails** and scenarios
2. **Add more features** like draft editing
3. **Improve UI/UX** based on user feedback
4. **Add analytics** and usage tracking

## 📞 **Support:**

If users encounter issues:
1. **Check this guide** for troubleshooting steps
2. **Verify server status** and network connectivity
3. **Test API endpoints** directly
4. **Check Outlook add-in logs** for errors

---

**🎯 The add-in is now ready for company users to view and send AI drafts directly from Outlook!** 