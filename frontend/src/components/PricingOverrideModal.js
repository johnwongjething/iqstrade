import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Alert,
  Divider,
  Typography,
  Space,
  Card,
  Row,
  Col
} from 'antd';
import { InfoCircleOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Text, Title } = Typography;

const PricingOverrideModal = ({ 
  visible, 
  onCancel, 
  onSave, 
  billData, 
  loading = false 
}) => {
  const [form] = Form.useForm();
  const [overrideReason, setOverrideReason] = useState('');
  const [showConfidence, setShowConfidence] = useState(true);

  useEffect(() => {
    if (visible && billData) {
      form.setFieldsValue({
        shipment_type: billData.shipment_type || 'ocean',
        container_type: billData.container_type || '20ft',
        container_count: billData.container_count || 1,
        total_weight_kg: billData.total_weight_kg || 0,
        weight_unit: billData.weight_unit || 'kg',
        pricing_method: billData.pricing_method || 'container',
        ctn_fee: billData.calculated_ctn_fee || billData.ctn_fee || 100,
        service_fee: billData.calculated_service_fee || billData.service_fee || 100,
        override_reason: ''
      });
    }
  }, [visible, billData, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const overrideData = {
        ...values,
        override_reason: overrideReason,
        original_ctn_fee: billData.ctn_fee,
        original_service_fee: billData.service_fee,
        bill_id: billData.id
      };
      onSave(overrideData);
    } catch (error) {
      console.error('Form validation failed:', error);
    }
  };

  const calculateTotal = () => {
    const ctnFee = form.getFieldValue('ctn_fee') || 0;
    const serviceFee = form.getFieldValue('service_fee') || 0;
    return ctnFee + serviceFee;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceText = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  if (!billData) return null;

  const confidenceScore = billData.ocr_confidence_score || 0;
  const confidenceBreakdown = billData.confidence_breakdown || {};

  return (
    <Modal
      title={
        <Space>
          <EditOutlined />
          <span>Manual Pricing Override</span>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={800}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button 
          key="save" 
          type="primary" 
          icon={<SaveOutlined />}
          loading={loading}
          onClick={handleSave}
        >
          Save Override
        </Button>
      ]}
    >
      <div style={{ marginBottom: 16 }}>
        <Alert
          message="OCR Confidence Analysis"
          description={
            <div>
              <Text strong>Overall Confidence: </Text>
              <Text type={getConfidenceColor(confidenceScore)}>
                {getConfidenceText(confidenceScore)} ({(confidenceScore * 100).toFixed(1)}%)
              </Text>
              <br />
              <Text>Container Detection: {(confidenceBreakdown.container_detection * 100).toFixed(1)}%</Text>
              <br />
              <Text>Weight Detection: {(confidenceBreakdown.weight_detection * 100).toFixed(1)}%</Text>
              <br />
              <Text>Shipment Classification: {(confidenceBreakdown.shipment_classification * 100).toFixed(1)}%</Text>
            </div>
          }
          type={getConfidenceColor(confidenceScore)}
          showIcon
          icon={<InfoCircleOutlined />}
        />
      </div>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Shipment Details" size="small">
            <Form form={form} layout="vertical">
              <Form.Item
                name="shipment_type"
                label="Shipment Type"
                rules={[{ required: true, message: 'Please select shipment type' }]}
              >
                <Select>
                  <Option value="ocean">Ocean Freight</Option>
                  <Option value="air">Air Freight</Option>
                  <Option value="loose_cargo">Loose Cargo</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="container_type"
                label="Container Type"
                rules={[{ required: true, message: 'Please select container type' }]}
              >
                <Select>
                  <Option value="20ft">20ft Container</Option>
                  <Option value="40ft">40ft Container</Option>
                  <Option value="40ft_hc">40ft High Cube</Option>
                  <Option value="loose_cargo">Loose Cargo</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="container_count"
                label="Container Count"
                rules={[{ required: true, message: 'Please enter container count' }]}
              >
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="total_weight_kg"
                label="Total Weight (kg)"
                rules={[{ required: true, message: 'Please enter total weight' }]}
              >
                <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="weight_unit"
                label="Weight Unit"
                rules={[{ required: true, message: 'Please select weight unit' }]}
              >
                <Select>
                  <Option value="kg">Kilograms (kg)</Option>
                  <Option value="lbs">Pounds (lbs)</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="pricing_method"
                label="Pricing Method"
                rules={[{ required: true, message: 'Please select pricing method' }]}
              >
                <Select>
                  <Option value="container">Per Container</Option>
                  <Option value="weight">Per Weight</Option>
                  <Option value="mixed">Mixed</Option>
                </Select>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Fee Calculation" size="small">
            <Form form={form} layout="vertical">
              <Form.Item
                name="ctn_fee"
                label="CTN Fee (USD)"
                rules={[{ required: true, message: 'Please enter CTN fee' }]}
              >
                <InputNumber 
                  min={0} 
                  step={0.01} 
                  style={{ width: '100%' }}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>

              <Form.Item
                name="service_fee"
                label="Service Fee (USD)"
                rules={[{ required: true, message: 'Please enter service fee' }]}
              >
                <InputNumber 
                  min={0} 
                  step={0.01} 
                  style={{ width: '100%' }}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>

              <Divider />

              <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                <Title level={4} style={{ margin: 0 }}>
                  Total: ${calculateTotal().toFixed(2)}
                </Title>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>

      <Divider />

      <Form.Item
        label="Override Reason"
        rules={[{ required: true, message: 'Please provide a reason for the override' }]}
      >
        <Input.TextArea
          value={overrideReason}
          onChange={(e) => setOverrideReason(e.target.value)}
          placeholder="Explain why this override is necessary (e.g., OCR error, special pricing, etc.)"
          rows={3}
        />
      </Form.Item>

      <Alert
        message="Override Information"
        description="This override will be logged for audit purposes. Please ensure the reason is clear and accurate."
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </Modal>
  );
};

export default PricingOverrideModal; 