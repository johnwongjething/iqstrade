"""
Unified Response Handler for IQSTrade
Provides consistent responses across email, WhatsApp, and other channels.
Based on the WhatsApp bot logic but enhanced for multi-channel use.
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class UnifiedResponseHandler:
    """
    Handles customer enquiries with consistent responses across all channels.
    """
    
    def __init__(self, db_connector=None):
        """
        Initialize the response handler.
        
        Args:
            db_connector: Function to get database connection
        """
        self.db_connector = db_connector
    
    def extract_bl_number(self, text: str) -> Optional[str]:
        """Extract BL number from text using regex."""
        match = re.search(r'\bBL\d{3,}\b', text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def get_invoice_link(self, bl_number: str) -> Optional[str]:
        """Get invoice link from database."""
        if not self.db_connector:
            return None
        
        try:
            conn = self.db_connector()
            cur = conn.cursor()
            cur.execute('SELECT customer_invoice FROM bill_of_lading WHERE bl_number = %s', (bl_number,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting invoice link for {bl_number}: {e}")
            return None
    
    def get_unique_number(self, bl_number: str) -> Optional[str]:
        """Get CTN number from database."""
        if not self.db_connector:
            return None
        
        try:
            conn = self.db_connector()
            cur = conn.cursor()
            cur.execute('SELECT unique_number FROM bill_of_lading WHERE bl_number = %s', (bl_number,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting unique number for {bl_number}: {e}")
            return None
    
    def handle_pricing_enquiry(self, message: str) -> str:
        """Handle pricing enquiries."""
        message_lower = message.lower()
        
        # Extract number of containers
        container_match = re.search(r'(\d+)\s*container', message_lower)
        num_containers = int(container_match.group(1)) if container_match else 1
        
        ctn_fee = 100 * num_containers
        service_fee = 100 * num_containers
        total = ctn_fee + service_fee
        
        return f"""Thank you for your enquiry about pricing.

For {num_containers} container{'s' if num_containers > 1 else ''}:
• CTN Fee: USD ${ctn_fee}
• Service Fee: USD ${service_fee}
• Total: USD ${total}

Please provide your BL number so we can generate a detailed invoice for you."""
    
    def handle_payment_enquiry(self, message: str) -> str:
        """Handle payment method enquiries."""
        return """Thank you for your enquiry about payment methods.

We accept the following payment methods:
• Bank Transfer
• Allinpay
• Stripe

Please provide your BL number so we can send you the payment link and instructions."""
    
    def handle_shipping_time_enquiry(self, message: str) -> str:
        """Handle shipping time enquiries."""
        return """Thank you for your enquiry about shipping times.

Shipping times vary depending on:
• Origin and destination ports
• Vessel schedule
• Customs clearance

Please provide your BL number so I can check the specific details for your shipment."""
    
    def handle_document_enquiry(self, message: str) -> str:
        """Handle document enquiries."""
        return """Thank you for your enquiry about documents.

Common documents we handle:
• Bill of Lading (BL)
• Commercial Invoice
• Packing List
• Certificate of Origin
• Customs documents

Please provide your BL number so I can check what documents are available for your shipment."""
    
    def handle_status_enquiry(self, message: str) -> str:
        """Handle shipment status enquiries."""
        return """Thank you for your enquiry about shipment status.

To check your shipment status, I need:
• Your BL number, or
• Your CTN number

Please provide either of these so I can give you the current status and location of your shipment."""
    
    def handle_contact_enquiry(self, message: str) -> str:
        """Handle contact information enquiries."""
        return """Thank you for your enquiry.

You can contact us through:
• Email: [Your company email]
• Phone: [Your company phone]
• WhatsApp: [Your WhatsApp number]
• Office: [Your office address]

For specific shipment enquiries, please provide your BL number so I can assist you better."""
    
    def handle_general_enquiry(self, message: str) -> str:
        """
        Handle general enquiries by detecting intent and providing appropriate response.
        """
        message_lower = message.lower()
        
        # Pricing enquiries
        if any(keyword in message_lower for keyword in ['how much', 'price', 'cost', 'fee', '费用', '多少钱', 'container', 'containers']):
            return self.handle_pricing_enquiry(message)
        
        # Payment method enquiries
        if any(keyword in message_lower for keyword in ['payment', 'pay', 'method', '方式', '银行', 'stripe', 'allinpay', 'transfer', 'how to pay']):
            return self.handle_payment_enquiry(message)
        
        # Shipping time enquiries
        if any(keyword in message_lower for keyword in ['time', 'duration', 'when', 'arrive', 'delivery', 'shipping', 'transit', '多久', '时间']):
            return self.handle_shipping_time_enquiry(message)
        
        # Document enquiries
        if any(keyword in message_lower for keyword in ['document', 'paperwork', 'certificate', 'form', '文件', '证书', '表格']):
            return self.handle_document_enquiry(message)
        
        # Status enquiries
        if any(keyword in message_lower for keyword in ['status', 'where', 'track', 'location', 'update', '状态', '位置', '跟踪']):
            return self.handle_status_enquiry(message)
        
        # Contact information enquiries
        if any(keyword in message_lower for keyword in ['contact', 'phone', 'email', 'address', 'office', '联系', '电话', '邮箱']):
            return self.handle_contact_enquiry(message)
        
        # Default response for unclear enquiries
        return """Thank you for your enquiry.

To provide you with the most accurate information, please include:
• Your BL number (if you have one)
• Specific details about what you need help with

This will help me give you a more detailed and helpful response.

Alternatively, you can contact our customer service team directly for immediate assistance."""
    
    def handle_invoice_request(self, message: str) -> Tuple[str, str]:
        """
        Handle invoice requests.
        Returns (response, bl_number)
        """
        bl_number = self.extract_bl_number(message)
        if not bl_number:
            return "Please provide your BL number so I can find your invoice.", None
        
        invoice_link = self.get_invoice_link(bl_number)
        if invoice_link:
            return f"Here's your invoice: {invoice_link}", bl_number
        else:
            return f"Sorry, I couldn't find an invoice for {bl_number}.", bl_number
    
    def handle_payment_receipt(self, message: str) -> Tuple[str, str]:
        """
        Handle payment receipt processing.
        Returns (response, bl_number)
        """
        bl_number = self.extract_bl_number(message)
        if not bl_number:
            return "Please provide your BL number so I can find your CTN number.", None
        
        ctn = self.get_unique_number(bl_number)
        if ctn:
            return f"CTN number is {ctn}.", bl_number
        else:
            return f"Sorry, I couldn't find a CTN number for {bl_number}.", bl_number
    
    def process_message(self, message: str, classification: str = None) -> Dict[str, str]:
        """
        Process a customer message and return appropriate response.
        
        Args:
            message: Customer message
            classification: Optional classification from OpenAI
            
        Returns:
            Dict with 'response', 'classification', and 'bl_number'
        """
        bl_number = self.extract_bl_number(message)
        
        # If classification is provided, use it
        if classification:
            if classification == "invoice_request":
                response, bl_num = self.handle_invoice_request(message)
                return {
                    'response': response,
                    'classification': classification,
                    'bl_number': bl_num
                }
            elif classification == "payment_receipt":
                response, bl_num = self.handle_payment_receipt(message)
                return {
                    'response': response,
                    'classification': classification,
                    'bl_number': bl_num
                }
            elif classification == "general_enquiry":
                response = self.handle_general_enquiry(message)
                return {
                    'response': response,
                    'classification': classification,
                    'bl_number': bl_number
                }
        
        # Auto-detect intent if no classification provided
        message_lower = message.lower()
        
        # Check for invoice intent
        if any(keyword in message_lower for keyword in ['invoice', '发票', '账单']) and bl_number:
            response, bl_num = self.handle_invoice_request(message)
            return {
                'response': response,
                'classification': 'invoice_request',
                'bl_number': bl_num
            }
        
        # Check for receipt intent
        if any(keyword in message_lower for keyword in ['receipt', '收据', '付款', 'payment']) and bl_number:
            response, bl_num = self.handle_payment_receipt(message)
            return {
                'response': response,
                'classification': 'payment_receipt',
                'bl_number': bl_num
            }
        
        # Default to general enquiry
        response = self.handle_general_enquiry(message)
        return {
            'response': response,
            'classification': 'general_enquiry',
            'bl_number': bl_number
        }

# Global instance for easy import
response_handler = UnifiedResponseHandler()

def get_response_handler(db_connector=None):
    """Get a response handler instance."""
    if db_connector:
        return UnifiedResponseHandler(db_connector)
    return response_handler 