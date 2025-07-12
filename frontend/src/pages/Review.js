import React, { useEffect, useState, useContext } from 'react';
import { Button, Input, Modal, Upload, Table, Select, Pagination } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { UserContext } from '../UserContext';
import { Snackbar, Alert } from '@mui/material';
import LoadingModal from '../components/LoadingModal';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

function Review({ t = x => x }) {
  const [bills, setBills] = useState([]);
  const [selected, setSelected] = useState(null);
  const [fields, setFields] = useState({});
  const [serviceFee, setServiceFee] = useState('');
  const [ctnFee, setCtnFee] = useState('');
  const [paymentLink, setPaymentLink] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [uniqueNumber, setUniqueNumber] = useState('');
  const [blSearch, setBlSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [emailModalVisible, setEmailModalVisible] = useState(false);
  const [emailBody, setEmailBody] = useState('');
  const [emailTo, setEmailTo] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailPdfUrl, setEmailPdfUrl] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [uniqueEmailModalVisible, setUniqueEmailModalVisible] = useState(false);
  const [uniqueEmailBody, setUniqueEmailBody] = useState('');
  const [uniqueEmailTo, setUniqueEmailTo] = useState('');
  const [uniqueEmailSubject, setUniqueEmailSubject] = useState('');
  const [uniqueSending, setUniqueSending] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [pdfZoom, setPdfZoom] = useState(1.2); // Default zoom to fill area
  const [numPages, setNumPages] = useState(null);
  const navigate = useNavigate();
  const { user, fetchUserIfNeeded, csrfToken } = useContext(UserContext);

  // Security: Ensure user is authenticated
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

  // Fetch bills
  useEffect(() => {
    fetchBills({ page: 1 });
    // eslint-disable-next-line
  }, []);

  const fetchBills = async (params = {}) => {
    setLoading(true);
    try {
      const query = new URLSearchParams({
        page: params.page || page,
        page_size: params.pageSize || pageSize,
        bl_number: params.blSearch !== undefined ? params.blSearch : blSearch,
        status: params.statusFilter !== undefined ? params.statusFilter : statusFilter
      });
      const response = await fetch(`${API_BASE_URL}/api/bills?${query.toString()}`, {
        credentials: 'include',
      });
      if (response.status === 401) {
        navigate('/login');
        return;
      }
      const data = await response.json();
      setBills(data.bills || []);
      setTotal(data.total || 0);
      setPage(data.page || 1);
      setPageSize(data.page_size || 50);
    } catch {
      setBills([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // Show edit modal
  const showModal = (record) => {
    setSelected(record);
    setFields({
      shipper: record.shipper || '',
      consignee: record.consignee || '',
      port_of_loading: record.port_of_loading || '',
      port_of_discharge: record.port_of_discharge || '',
      bl_number: record.bl_number || '',
      container_numbers: record.container_numbers || '',
      flight_or_vessel: record.flight_or_vessel || '',
      product_description: record.product_description || '',
    });
    setServiceFee(record.service_fee || '');
    setCtnFee(record.ctn_fee || '');
    setPaymentLink(record.payment_link || '');
    setUniqueNumber(record.unique_number || '');
    setModalVisible(true);
  };

  // Handle field change
  const handleFieldChange = (key, value) => {
    setFields({ ...fields, [key]: value });
  };

  // --- Input validation helpers ---
  const isValidNumber = val => /^\d+(\.\d{1,2})?$/.test(val);
  const isNonEmptyString = val => typeof val === 'string' && val.trim().length > 0;

  // Save changes
  const handleOk = async () => {
    // Input validation
    if (!isNonEmptyString(fields.shipper)) {
      setSnackbar({ open: true, message: 'Shipper is required.', severity: 'error' });
      return;
    }
    if (!isNonEmptyString(fields.consignee)) {
      setSnackbar({ open: true, message: 'Consignee is required.', severity: 'error' });
      return;
    }
    if (!isValidNumber(ctnFee)) {
      setSnackbar({ open: true, message: 'CTN Fee must be a valid number.', severity: 'error' });
      return;
    }
    if (!isValidNumber(serviceFee)) {
      setSnackbar({ open: true, message: 'Service Fee must be a valid number.', severity: 'error' });
      return;
    }
    setSaving(true);
    try {
      // Always use the latest generated payment link, never fallback to old DB value
      const updateData = {
        ...fields,
        service_fee: serviceFee === '' ? null : Number(serviceFee),
        ctn_fee: ctnFee === '' ? null : Number(ctnFee),
        payment_link: paymentLink, // Only use the latest generated link
        unique_number: uniqueNumber,
        payment_method: selected?.payment_method || '',
        payment_status: selected?.payment_status || '',
        reserve_status: selected?.reserve_status || ''
      };
      const res = await fetch(`${API_BASE_URL}/api/bill/${selected.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
        credentials: 'include',
        body: JSON.stringify(updateData)
      });
      if (res.status === 401) {
        navigate('/login');
        return;
      }
      setModalVisible(false);
      fetchBills();
    } catch (err) {
      // Optionally show error
    } finally {
      setSaving(false);
    }
  };

  // --- Email modal handlers ---
  const showEmailModal = (record) => {
    setEmailTo(record.customer_email);
    setEmailSubject(t('invoiceSubject'));
    const ctnFeeVal = record.ctn_fee || 0;
    const serviceFeeVal = record.service_fee || 0;
    const total = (parseFloat(ctnFeeVal) + parseFloat(serviceFeeVal)).toFixed(2);
    setEmailBody(
      `Dear ${record.customer_name},\n\nPlease find your invoice attached.\nCTN Fee: $${ctnFeeVal}\nService Fee: $${serviceFeeVal}\nTotal Amount: $${total}\n\nPlease follow the below link to make the payment:\n${record.payment_link || ''}\n\nThank you!`
    );
    setEmailPdfUrl(record.invoice_filename);
    setSelected(record);
    setEmailModalVisible(true);
  };
  const handleSendInvoiceEmail = async () => {
    setSendingEmail(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/send_invoice_email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
        credentials: 'include',
        body: JSON.stringify({
          to_email: emailTo,
          subject: emailSubject,
          body: emailBody,
          pdf_url: emailPdfUrl,
          bill_id: selected.id
        })
      });
      const data = await res.json();
      if (res.ok) {
        setSnackbar({ open: true, message: t('emailSent'), severity: 'success' });
        setEmailModalVisible(false);
        fetchBills();
      } else {
        setSnackbar({ open: true, message: data.error || t('emailFailed'), severity: 'error' });
      }
    } catch (err) {
      setSnackbar({ open: true, message: t('emailFailed'), severity: 'error' });
    } finally {
      setSendingEmail(false);
    }
  };
  // --- Unique number email modal handlers ---
  const showUniqueEmailModal = (record) => {
    setSelected(record);
    setUniqueEmailTo(record.customer_email);
    setUniqueEmailSubject(t('uniqueNumberSubject'));
    setUniqueEmailBody(t('uniqueNumberBody', { name: record.customer_name, number: record.unique_number }));
    setUniqueEmailModalVisible(true);
  };
  const handleSendUniqueEmail = async () => {
    setUniqueSending(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/send_unique_number_email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
        credentials: 'include',
        body: JSON.stringify({
          to_email: uniqueEmailTo,
          subject: uniqueEmailSubject,
          body: uniqueEmailBody,
          bill_id: selected.id
        })
      });
      const data = await res.json();
      if (res.ok) {
        setSnackbar({ open: true, message: t('uniqueEmailSent'), severity: 'success' });
        setUniqueEmailModalVisible(false);
      } else {
        setSnackbar({ open: true, message: data.error || t('emailFailed'), severity: 'error' });
      }
    } catch (err) {
      setSnackbar({ open: true, message: t('emailFailed'), severity: 'error' });
    } finally {
      setUniqueSending(false);
    }
  };
  const handleSendUniqueNumber = (record) => {
    showUniqueEmailModal(record);
  };
  // --- Upload receipt handler ---
  const handleUpload = async (file, record) => {
    const formData = new FormData();
    formData.append('file', file);
    await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: { 'X-CSRF-TOKEN': csrfToken },
      credentials: 'include',
      body: formData
    });
    setSnackbar({ open: true, message: t('receiptUploadSuccess'), severity: 'success' });
    fetchBills();
  };

  // Table columns
  const columns = [
    { title: t('customerName'), dataIndex: 'customer_name', key: 'customer_name' },
    { title: t('blNumber'), dataIndex: 'bl_number', key: 'bl_number' },
    {
      title: t('shipperConsignee'),
      key: 'shipperConsignee',
      render: (_, record) => (
        <div>
          <div>{record.shipper}</div>
          <div>{record.consignee}</div>
        </div>
      ),
    },
    { title: t('status'), dataIndex: 'status', key: 'status' },
    {
      title: t('edit'),
      key: 'edit',
      width: 80,
      render: (_, record) => (
        <Button size="small" onClick={() => showModal(record)}>{t('edit')}</Button>
      ),
    },
    {
      title: t('invoice'),
      key: 'invoice',
      width: 120,
      render: (_, record) => record.invoice_filename ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <a
            href={record.invoice_filename}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="small">{t('viewInvoice')}</Button>
          </a>
          <Button
            size="small"
            type="primary"
            onClick={() => showEmailModal(record)}
          >
            {t('sendInvoice')}
          </Button>
        </div>
      ) : t('noInvoice'),
    },
    {
      title: t('ctnServiceFee'),
      key: 'ctnServiceFee',
      render: (_, record) => (
        <span>{record.ctn_fee || 0} / {record.service_fee || 0}</span>
      ),
    },
    {
      title: t('uploadReceipt'),
      key: 'uploadReceipt',
      width: 120,
      render: (_, record) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Upload
            showUploadList={false}
            customRequest={({ file, onSuccess, onError }) => {
              handleUpload(file, record)
                .then(() => onSuccess && onSuccess())
                .catch(onError);
            }}
          >
            <Button size="small">{t('uploadReceipt')}</Button>
          </Upload>
          {record.receipt_filename && (
            <a
              href={record.receipt_filename}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="small">{t('viewReceipt')}</Button>
            </a>
          )}
        </div>
      ),
    },
    {
      title: t('ctnNumber'),
      dataIndex: 'unique_number',
      key: 'unique_number',
      width: 120,
      render: (text, record) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>{text}</span>
          <Button
            size="small"
            onClick={() => handleSendUniqueNumber(record)}
          >
            {t('sendCtnNumber')}
          </Button>
        </div>
      ),
    },
    {
      title: <span>Customer<br/>Document</span>,
      key: 'customerDocument',
      width: 120,
      render: (_, record) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Button
            size="small"
            disabled={!record.customer_invoice}
            href={record.customer_invoice || undefined}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('invoice')}
          </Button>
          <Button
            size="small"
            disabled={!record.customer_packing_list}
            href={record.customer_packing_list || undefined}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('packingList')}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Button
          type="primary"
          style={{ color: '#fff', backgroundColor: '#1976d2' }}
          onClick={() => navigate('/dashboard')}
        >
          {t('backToDashboard')}
        </Button>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Input
            placeholder={t('blNumber')}
            value={blSearch}
            onChange={e => setBlSearch(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Button type="primary" onClick={() => fetchBills({ page: 1, blSearch })}>{t('search')}</Button>
          <Button onClick={() => { setBlSearch(''); fetchBills({ page: 1 }); }}>{t('cancel')}</Button>
          <Select
            placeholder={t('filterByStatus')}
            style={{ width: 180 }}
            value={statusFilter || undefined}
            onChange={value => { setStatusFilter(value); fetchBills({ page: 1, statusFilter: value }); }}
            allowClear
            options={[
              { label: t('pending'), value: t('pending') },
              { label: t('invoiceSent'), value: t('invoiceSent') },
              { label: t('awaitingBankIn'), value: t('awaitingBankIn') },
              { label: t('paidAndCtnValid'), value: t('paidAndCtnValid') },
            ]}
          />
        </div>
      </div>
      <h2>{t('billReview')}</h2>
      <Table dataSource={bills} columns={columns} rowKey="id" pagination={false} loading={loading} />
      <Pagination
        current={page}
        pageSize={pageSize}
        total={total}
        showSizeChanger
        onChange={(newPage, newPageSize) => { setPage(newPage); setPageSize(newPageSize); fetchBills({ page: newPage, pageSize: newPageSize }); }}
        style={{ marginTop: 16, textAlign: 'right' }}
      />
      <Modal
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleOk}
        okText={t('save')}
        cancelText={t('cancel')}
        title={t('editBill')}
        width={1100}
        confirmLoading={saving}
      >
        {selected && selected.pdf_filename ? (
          <div style={{ display: 'flex', gap: 24 }}>
            <div style={{ width: '60%', minWidth: 400, background: '#f5f5f5', padding: 12, borderRadius: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 8, gap: 8 }}>
                <Button size="small" onClick={() => setPdfZoom(z => Math.max(z - 0.2, 0.4))}>-</Button>
                <span style={{ minWidth: 40, textAlign: 'center' }}>{Math.round(pdfZoom * 100)}%</span>
                <Button size="small" onClick={() => setPdfZoom(z => Math.min(z + 0.2, 3))}>+</Button>
              </div>
              <div style={{ width: '100%', flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 600 }}>
                <Document
                  file={selected.pdf_filename}
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                  loading={<div>Loading PDF...</div>}
                  error={<div>Failed to load PDF.</div>}
                >
                  <Page
                    pageNumber={1}
                    width={Math.max(400, 0.6 * 1100) * pdfZoom}
                    renderAnnotationLayer={false}
                    renderTextLayer={true}
                  />
                </Document>
              </div>
              {numPages && (
                <div style={{ marginTop: 8, fontSize: 13, color: '#888' }}>1 of {numPages}</div>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <div>
                <b>{t('shipper')}:</b>
                <Input.TextArea
                  value={fields.shipper}
                  onChange={e => handleFieldChange('shipper', e.target.value)}
                  autoSize={{ minRows: 2, maxRows: 4 }}
                />
              </div>
              <div>
                <b>{t('consignee')}:</b>
                <Input.TextArea
                  value={fields.consignee}
                  onChange={e => handleFieldChange('consignee', e.target.value)}
                  autoSize={{ minRows: 2, maxRows: 4 }}
                />
              </div>
              <div>
                <b>{t('portOfLoading')}:</b>
                <Input
                  value={fields.port_of_loading}
                  onChange={e => handleFieldChange('port_of_loading', e.target.value)}
                />
              </div>
              <div>
                <b>{t('portOfDischarge')}:</b>
                <Input
                  value={fields.port_of_discharge}
                  onChange={e => handleFieldChange('port_of_discharge', e.target.value)}
                />
              </div>
              <div>
                <b>{t('blNumber')}:</b>
                <Input
                  value={fields.bl_number}
                  onChange={e => handleFieldChange('bl_number', e.target.value)}
                />
              </div>
              <div>
                <b>{t('containerNumbers')}:</b>
                <Input
                  value={fields.container_numbers}
                  onChange={e => handleFieldChange('container_numbers', e.target.value)}
                />
              </div>
              <div>
                <b>{t('flightOrVessel') || 'Flight or Vessel'}:</b>
                <Input
                  value={fields.flight_or_vessel}
                  onChange={e => handleFieldChange('flight_or_vessel', e.target.value)}
                />
              </div>
              <div>
                <b>{t('productDescription') || 'Product Description'}:</b>
                <Input.TextArea
                  value={fields.product_description}
                  onChange={e => handleFieldChange('product_description', e.target.value)}
                  autoSize={{ minRows: 2, maxRows: 4 }}
                />
              </div>
              <Input
                style={{ width: 200, marginTop: 16 }}
                addonBefore={t('ctnFee') + '(USD)'}
                value={ctnFee}
                onChange={e => setCtnFee(e.target.value)}
              />
              <Input
                style={{ width: 200, marginTop: 16 }}
                addonBefore={t('serviceFee') + '(USD)'}
                value={serviceFee}
                onChange={e => setServiceFee(e.target.value)}
              />
              <Input
                value={uniqueNumber}
                onChange={e => setUniqueNumber(e.target.value)}
                placeholder={t('ctnNumber')}
              />
              <div style={{ marginTop: 16 }}>
                <b>{t('paymentLink') || 'Payment Link'}:</b>{' '}
                {fields.payment_link ? (
                  <span style={{ color: 'green' }}>{t('paymentLinkGenerated') || 'Payment link generated'}</span>
                ) : (
                  <Button type="primary" onClick={async () => {
                    if (!selected || !uniqueNumber) {
                      setSnackbar({ open: true, message: 'Please enter a CTN number.', severity: 'error' });
                      return;
                    }
                    if (!isValidNumber(ctnFee) || !isValidNumber(serviceFee)) {
                      setSnackbar({ open: true, message: 'Fees must be valid numbers.', severity: 'error' });
                      return;
                    }
                    try {
                      const res = await fetch(`${API_BASE_URL}/api/generate_payment_link/${selected.id}`,
                        {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
                          credentials: 'include',
                          body: JSON.stringify({
                            amount: 0,
                            currency: 'USD',
                            customer_email: selected.customer_email,
                            description: `Reserve payment for CTN ${uniqueNumber}`,
                            success_url: 'https://yourdomain.com/success',
                            cancel_url: 'https://yourdomain.com/cancel',
                            ctn_fee: ctnFee,
                            service_fee: serviceFee,
                          })
                        });
                      const data = await res.json();
                      if (res.ok && data.payment_link) {
                        setFields(prev => ({ ...prev, payment_link: data.payment_link }));
                        setPaymentLink(data.payment_link);
                        setSnackbar({ open: true, message: 'Payment link generated successfully.', severity: 'success' });
                      } else {
                        setSnackbar({ open: true, message: `Failed to generate payment link: ${data.error}`, severity: 'error' });
                      }
                    } catch (err) {
                      setSnackbar({ open: true, message: `Error generating link: ${err.message}`, severity: 'error' });
                    }
                  }}>
                    {t('generatePaymentLink') || 'Generate Payment Link'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div>{t('noDocument')}</div>
        )}
      </Modal>
      <Modal
        open={emailModalVisible}
        onCancel={() => setEmailModalVisible(false)}
        onOk={handleSendInvoiceEmail}
        okText={t('send')}
        cancelText={t('cancel')}
        title={t('verifyInvoiceEmail')}
        confirmLoading={sendingEmail}
      >
        <div>
          <div><strong>{t('to')}:</strong> {emailTo}</div>
          <div><strong>{t('subject')}:</strong> {emailSubject}</div>
          <div style={{ margin: '12px 0' }}>
            <strong>{t('emailBody')}:</strong>
            <Input.TextArea
              value={emailBody}
              onChange={e => setEmailBody(e.target.value)}
              autoSize={{ minRows: 6 }}
            />
          </div>
          <div>
            <a 
              href={emailPdfUrl}
              target="_blank" 
              rel="noopener noreferrer"
              style={{ textDecoration: 'none' }}
            >
              <Button size="small">
                {t('previewPDF')}
              </Button>
            </a>
          </div>
        </div>
      </Modal>
      <Modal
        open={uniqueEmailModalVisible}
        onCancel={() => setUniqueEmailModalVisible(false)}
        onOk={handleSendUniqueEmail}
        okText={t('send')}
        cancelText={t('cancel')}
        title={t('verifyUniqueNumberEmail')}
        confirmLoading={uniqueSending}
      >
        <div>
          <div><strong>{t('to')}:</strong> {uniqueEmailTo}</div>
          <div><strong>{t('subject')}:</strong> {uniqueEmailSubject}</div>
          <div style={{ margin: '12px 0' }}>
            <strong>{t('emailBody')}:</strong>
            <Input.TextArea
              value={uniqueEmailBody}
              onChange={e => setUniqueEmailBody(e.target.value)}
              autoSize={{ minRows: 6 }}
            />
          </div>
        </div>
      </Modal>
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
      <LoadingModal open={loading} message={t('loadingData')} />
      <LoadingModal open={saving} message={t('savingData')} />
      <LoadingModal open={sendingEmail} message={t('sendingEmail')} />
      <LoadingModal open={uniqueSending} message={t('sendingEmail')} />
    </div>
  );
}

export default Review;