import React, { useState, useEffect, useContext } from 'react';
import { Button, DatePicker, Table, Typography, Space } from 'antd';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router-dom';
import LoadingModal from '../components/LoadingModal';
import { UserContext } from '../UserContext';
import { fetchWithAuth } from '../utils/tokenUtils';
import { useMediaQuery } from '@mui/material';
import { Box } from '@mui/material';

const { Title } = Typography;

const AccountPage = ({ t = x => x }) => {
  const [date, setDate] = useState(null);
  const [month, setMonth] = useState(null); // For month search
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState({
    totalEntries: 0,
    totalCtnFee: 0,
    totalServiceFee: 0,
    bankTotal: 0,
    allinpay85Total: 0,
    reserveTotal: 0,
    totalCreditDebit: 0
  });
  const navigate = useNavigate();
  const { user, fetchUserIfNeeded, csrfToken } = useContext(UserContext);
  const isMobile = useMediaQuery('(max-width:600px)');

  useEffect(() => {
    const checkUser = async () => {
      const ok = await fetchUserIfNeeded();
      if (!ok || !user || !user.role) {
        navigate('/login');
        return false;
      }
      return true;
    };
    checkUser();
    // eslint-disable-next-line
  }, [navigate]);

  // Restored original columns for output table
  const columns = [
    {
      title: t('blNumber'),
      dataIndex: 'bl_number',
      key: 'bl_number',
    },
    {
      title: t('receiptPDF'),
      key: 'receiptPDF',
      render: (_, record) => record.receipt_filename ? (
        <a
          href={record.receipt_filename}
          target="_blank"
          rel="noopener noreferrer"
                                  onClick={() => {}}
        >
          {t('viewReceipt')}
        </a>
      ) : t('N/A'),
    },
    {
      title: t('ctnFee'),
      dataIndex: 'display_ctn_fee',
      key: 'display_ctn_fee',
      render: (value) => `$${value}`,
    },
    {
      title: t('serviceFee'),
      dataIndex: 'display_service_fee',
      key: 'display_service_fee',
      render: (value) => `$${value}`,
    },
    {
      title: 'Balance Applied',
      dataIndex: 'balance_applied',
      key: 'balance_applied',
      render: (value) => `$${Number(value || 0).toFixed(2)}`,
    },
    {
      title: t('total'),
      key: 'total',
      render: (_, record) =>
        `$${(Number(record.display_ctn_fee) + Number(record.display_service_fee) - Number(record.balance_applied || 0)).toFixed(2)}`,
    },
    {
      title: t('customerName'),
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: t('paymentType'),
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (value) => value === 'Allinpay' ? t('allinpay') : t('bankTransfer'),
    },
    {
      title: t('date'),
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (value) => value ? new Date(value).toLocaleString('en-HK', { timeZone: 'Asia/Hong_Kong' }) : '',
    },
  ];

  // Accepts either a date string (YYYY-MM-DD) or a month string (YYYY-MM)
  const fetchAccountBills = async (searchDateString = null, searchMonthString = null) => {
    setLoading(true);
    try {
      let url = '';
      if (searchDateString) {
        url = `${API_BASE_URL}/api/account_bills?completed_at=${searchDateString}`;
      } else if (searchMonthString) {
        url = `${API_BASE_URL}/api/account_bills_monthly?completed_month=${searchMonthString}`;
      } else {
        url = `${API_BASE_URL}/api/account_bills`;
      }
      const response = await fetchWithAuth(url, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setBills(data.bills || []);
        // If backend does not return summary for monthly, calculate it here
        let summaryData = data.summary;
        if (!summaryData) {
          // Calculate summary from bills
          let totalEntries = (data.bills || []).length;
          let totalCtnFee = 0, totalServiceFee = 0, bankTotal = 0, allinpay85Total = 0, reserveTotal = 0, totalCreditDebit = 0;
          (data.bills || []).forEach(bill => {
            totalCtnFee += Number(bill.display_ctn_fee || bill.ctn_fee || 0);
            totalServiceFee += Number(bill.display_service_fee || bill.service_fee || 0);
            totalCreditDebit += Number(bill.balance_applied || 0);
            if (bill.payment_method === 'Allinpay') {
              allinpay85Total += Number(bill.display_service_fee || bill.service_fee || 0);
              reserveTotal += Number(bill.display_ctn_fee || bill.ctn_fee || 0);
            } else {
              bankTotal += Number(bill.display_service_fee || bill.service_fee || 0) + Number(bill.display_ctn_fee || bill.ctn_fee || 0);
            }
          });
          summaryData = {
            totalEntries,
            totalCtnFee,
            totalServiceFee,
            bankTotal,
            allinpay85Total,
            reserveTotal,
            totalCreditDebit
          };
        }
        setSummary({
          totalEntries: summaryData.totalEntries || 0,
          totalCtnFee: summaryData.totalCtnFee || 0,
          totalServiceFee: summaryData.totalServiceFee || 0,
          bankTotal: summaryData.bankTotal || 0,
          allinpay85Total: summaryData.allinpay85Total || 0,
          reserveTotal: summaryData.reserveTotal || 0,
          totalCreditDebit: summaryData.totalCreditDebit || 0
        });
      }
    } catch (error) {
      setBills([]);
      setSummary({
        totalEntries: 0,
        totalCtnFee: 0,
        totalServiceFee: 0,
        bankTotal: 0,
        allinpay85Total: 0,
        reserveTotal: 0,
        totalCreditDebit: 0
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAccountBills(); }, []);


  const handleDateSearch = () => {
    if (date) {
      const hkDateString = date.format('YYYY-MM-DD');
      fetchAccountBills(hkDateString, null);
    }
  };

  const handleMonthSearch = () => {
    if (month) {
      const monthString = month.format('YYYY-MM');
      fetchAccountBills(null, monthString);
    }
  };

  const handleClearSearch = () => {
    setDate(null);
    setMonth(null);
    fetchAccountBills(null, null);
  };

  const handleExportPDF = () => {
    const doc = new jsPDF();
    const title = date
      ? `${t('accountPageReport')} - ${date.format('YYYY-MM-DD')}`
      : `${t('accountPageReport')} - ${t('allCompletedBills')}`;
    doc.setFontSize(16);
    doc.text(title, 20, 20);
    doc.setFontSize(12);
    doc.text(`${t('totalEntries')}: ${summary.totalEntries}`, 20, 35);
    doc.text(`${t('totalCtnFees')}: $${summary.totalCtnFee}`, 20, 45);
    doc.text(`${t('totalServiceFee')}: $${summary.totalServiceFee}`, 20, 55);
    doc.text(`Credit/Debit: $${(summary.totalCreditDebit || 0).toFixed(2)}`, 20, 65);
    doc.text(`${t('bankTransfer')}: $${summary.bankTotal}`, 20, 75);
    doc.text(`${t('allinpay85')}: $${summary.allinpay85Total}`, 20, 85);
    doc.text(`${t('allinpayReserve')}: $${summary.reserveTotal}`, 20, 95);

    const tableColumn = [
      t('blNumber'),
      t('ctnFee'),
      t('serviceFee'),
      'Balance Applied',
      t('total'),
      t('customerName'),
      t('paymentType'),
      t('date')
    ];

    const tableRows = bills.map(bill => [
      bill.bl_number || '',
      `$${bill.display_ctn_fee || 0}`,
      `$${bill.display_service_fee || 0}`,
      `$${Number(bill.balance_applied || 0).toFixed(2)}`,
      `$${(parseFloat(bill.display_ctn_fee || 0) + parseFloat(bill.display_service_fee || 0) - parseFloat(bill.balance_applied || 0)).toFixed(2)}`,
      bill.customer_name || '',
      bill.payment_method === 'Allinpay' ? t('allinpay') : t('bankTransfer'),
      bill.completed_at ? new Date(bill.completed_at).toLocaleString('en-HK', { timeZone: 'Asia/Hong_Kong' }) : ''
    ]);
    
    
    // const tableRows = bills.map(bill => [
    //   bill.bl_number || '',
    //   `$${bill.ctn_fee || 0}`,
    //   `$${bill.service_fee || 0}`,
    //   `$${parseFloat(bill.ctn_fee || 0) + parseFloat(bill.service_fee || 0)}`,
    //   bill.customer_name || '',
    //   bill.payment_type || '',
    //   bill.date ? new Date(bill.date).toLocaleString('en-HK', { timeZone: 'Asia/Hong_Kong' }) : ''
    // ]);

    doc.autoTable({
      head: [tableColumn],
      body: tableRows,
      startY: 100,
      styles: {
        fontSize: 10,
        cellPadding: 4,
        lineWidth: 0.5,
        lineColor: [0, 0, 0],
        halign: 'center',
        valign: 'middle',
      },
      headStyles: {
        fillColor: [41, 128, 185],
        textColor: 255,
        fontStyle: 'bold',
        lineWidth: 0.5,
        lineColor: [0, 0, 0],
      },
      alternateRowStyles: { fillColor: [245, 245, 245] },
      tableLineWidth: 0.5,
      tableLineColor: [0, 0, 0],
      theme: 'grid',
    });
    doc.save('account_page.pdf');
  };

  // Add no-op handlers to fix ESLint errors if not implemented
  const handleView = () => {};
  const handleDownload = () => {};

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Button variant="contained" color="primary" style={{ color: '#fff', backgroundColor: '#1976d2' }} onClick={() => navigate('/dashboard')}>
          {t('backToDashboard')}
        </Button>
        <Button type="link" onClick={handleExportPDF} style={{ fontWeight: 'bold' }}>
          {t('exportToPDF')}
        </Button>
      </div>

      <h2 style={{ margin: 0, textAlign: 'center' }}>{t('completedBillsAccountPage')}</h2>


      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '16px 0', gap: 8 }}>
        {/* Daily search */}
        <DatePicker value={date} onChange={setDate} style={{ marginRight: 0 }} allowClear placeholder={t('selectDate')}/>
        <Button type="primary" onClick={handleDateSearch}>{t('search')}</Button>

        {/* Monthly search */}
        <DatePicker
          picker="month"
          value={month}
          onChange={setMonth}
          allowClear
          placeholder={t('selectMonth') || 'Select month'}
        />
        <Button onClick={handleMonthSearch}>{t('monthlySearch') || 'Monthly Search'}</Button>

        <Button onClick={handleClearSearch}>{t('clearSearch')}</Button>
      </div>

      <div className="summary" style={{ display: 'flex', justifyContent: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 32 }}>
        <div style={{ textAlign: 'center' }}><h3>{t('totalEntries')}</h3><div style={{ fontSize: 24 }}>{summary.totalEntries}</div></div>
        <div style={{ textAlign: 'center' }}><h3>{t('totalCtnFees')}</h3><div style={{ fontSize: 24 }}>${summary.totalCtnFee}</div></div>
        <div style={{ textAlign: 'center' }}><h3>{t('totalServiceFee')}</h3><div style={{ fontSize: 24 }}>${summary.totalServiceFee}</div></div>
        <div style={{ textAlign: 'center' }}><h3>Credit/Debit</h3><div style={{ fontSize: 24 }}>${(summary.totalCreditDebit || 0).toFixed(2)}</div></div>
        <div style={{ textAlign: 'center' }}><h3>{t('bankTransfer')}</h3><div style={{ fontSize: 24 }}>${summary.bankTotal}</div></div>
        <div style={{ textAlign: 'center' }}><h3>{t('allinpay85')}</h3><div style={{ fontSize: 24 }}>${summary.allinpay85Total}</div></div>
        <div style={{ textAlign: 'center' }}><h3>{t('allinpayReserve')}</h3><div style={{ fontSize: 24 }}>${summary.reserveTotal}</div></div>
      </div>

      <Table dataSource={bills} columns={columns} rowKey="id" loading={loading} />
      <LoadingModal open={loading} message={t('loadingData')} />
    </div>
  );
};

export default AccountPage;
