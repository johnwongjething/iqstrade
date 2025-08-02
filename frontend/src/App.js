import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import NavBar from './pages/NavBar';
import Home from './pages/Home';
import About from './pages/About';
import Services from './pages/Services';
import Contact from './pages/Contact';
import Login from './pages/Login';
import Register from './pages/Register';
import StaffStats from './pages/StaffStats';
import UserApproval from './pages/UserApproval';
import Review from './pages/Review';
import UploadForm from './pages/UploadForm';
import BillSearch from './pages/BillSearch';
import WhatsAppButton from './pages/WhatsAppButton';
import WeChatButton from './pages/WeChatButton';
import Dashboard from './pages/Dashboard';
import FAQ from './pages/FAQ';
import EditBill from './pages/EditBill';
import EditDeleteBills from './pages/EditDeleteBills';
import translations from './pages/translations';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import AccountPage from './pages/AccountPage';
import NotFound from './pages/NotFound';
import AccountingReview from './pages/AccountingReview';
import BankImport from './pages/BankImport';
import UnmatchedBankRecords from './pages/UnmatchedBankRecords';
import CustomerEmails from './pages/CustomerEmails';
import ManagementDashboard from './pages/ManagementDashboard';
import ForgotUsername from './pages/ForgotUsername';
import TestPage from './pages/TestPage';
import TestPageNew from './pages/TestPageNew';
import NotificationTest3 from './pages/NotificationTest3';
import FCMSetup from './pages/FCMSetup';
import TestFCMSetup from './pages/TestFCMSetup';
import MinimalTest from './pages/MinimalTest';
// import NotificationTestSimple from './pages/NotificationTestSimple';
// import NotificationTest2 from './pages/NotificationTest2';
// import SimpleNotificationTest from './pages/SimpleNotificationTest';

import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  console.log('🔍 App component is rendering');
  
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'en');
  const [notificationPermission, setNotificationPermission] = useState('default');
  
  const t = (key, params) => {
    let str = translations[lang][key] || key;
    if (params) {
      Object.keys(params).forEach(k => {
        str = str.replace(new RegExp(`{${k}}`, 'g'), params[k]);
      });
    }
    return str;
  };

  // Initialize FCM notifications
  useEffect(() => {
    console.log('🔍 App useEffect is running');
    const initializeNotifications = async () => {
      try {
        // Check if notifications are supported
        if ('Notification' in window) {
          console.log('🔔 Setting up FCM foreground listener...');
          
          // Wait a moment for Firebase to be fully initialized
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Import Firebase functions dynamically to ensure proper initialization
          const { setupForegroundListener } = await import('./firebase');
          
          // Set up foreground message listener
          setupForegroundListener((payload) => {
            console.log('🔔 Foreground FCM message received:', payload);
          });
          
          console.log('✅ FCM foreground listener set up successfully');
        }
      } catch (error) {
        console.error('Error initializing notifications:', error);
      }
    };

    initializeNotifications();
  }, []);

  console.log('🔍 App component is about to return JSX');
  console.log('🔍 Routes being rendered:', [
    '/fcm-setup',
    '/test-fcm-setup',
    '/simple-test',
    '/minimal'
  ]);
  console.log('🔍 Current location:', window.location.pathname);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <NavBar lang={lang} setLang={setLang} t={t} />
                  <Routes>
            <Route path="/fcm-setup" element={<FCMSetup />} />
            <Route path="/test-fcm-setup" element={<TestFCMSetup />} />
            <Route path="/simple-test" element={<div>Simple Test Route Working!</div>} />
            <Route path="/minimal" element={<MinimalTest />} />
            <Route path="/" element={<Home t={t} />} />
            <Route path="/about" element={<About t={t} />} />
            <Route path="/services" element={<Services t={t} />} />
            <Route path="/contact" element={<Contact t={t} />} />
            <Route path="/login" element={<Login t={t} />} />
            <Route path="/register" element={<Register t={t} />} />
            <Route path="/staff-stats" element={<StaffStats t={t} />} />
            <Route path="/user-approval" element={<UserApproval t={t} />} />
            <Route path="/review" element={<Review t={t} />} />
            <Route path="/upload" element={<UploadForm t={t} />} />
            <Route path="/search" element={<BillSearch t={t} />} />
            <Route path="/dashboard" element={<Dashboard t={t} />} />
            <Route path="/faq" element={<FAQ t={t} />} />
            <Route path="/edit-bill/:id" element={<EditBill t={t} />} />
            <Route path="/edit-delete-bills" element={<EditDeleteBills t={t} />} />
            <Route path="/account-page" element={<AccountPage t={t} />} />
            <Route path="/forgot-password" element={<ForgotPassword t={t} />} />
            <Route path="/reset-password/:token" element={<ResetPassword t={t} />} />
            <Route path="/accounting-review" element={<AccountingReview t={t} />} />
            <Route path="/bank-import" element={<BankImport t={t} />} />
            <Route path="/unmatched-bank-records" element={<UnmatchedBankRecords t={t} />} />
            <Route path="/customer-emails" element={<CustomerEmails t={t} />} />
            <Route path="/management-dashboard" element={<ManagementDashboard t={t} />} />
            <Route path="/forgot-username" element={<ForgotUsername t={t} />} />
            <Route path="/test" element={<TestPage />} />
            <Route path="/test-new" element={<TestPageNew />} />
            <Route path="/notification-test3" element={<NotificationTest3 />} />

            {/* <Route path="/minimal" element={<MinimalTest />} /> */}
            {/* <Route path="/notification-simple" element={<NotificationTestSimple />} /> */}
            {/* <Route path="/notification-test2" element={<NotificationTest2 />} /> */}
            {/* <Route path="/simple-test" element={<SimpleNotificationTest />} /> */}
            
            {/* Catch-all route must be last */}
            <Route path="*" element={<NotFound t={t} />} />
          </Routes>
          <WeChatButton />
          <WhatsAppButton />
        </div>
    </ThemeProvider>
  );
}

export default App; 