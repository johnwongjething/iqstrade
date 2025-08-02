#!/usr/bin/env python3
"""
Production-Ready Email Validation System
Enhances email processing with validation layer without disrupting existing logic
"""

import logging
import json
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailValidationSystem:
    """
    Production-ready email validation system
    Enhances OpenAI responses without changing core classification logic
    """
    
    def __init__(self):
        self.request_patterns = {
            'ctn_request': [
                r'ctn\s+(?:number|num|#|no\.?)',
                r'container\s+(?:number|num|#|no\.?)',
                r'get\s+ctn',
                r'need\s+ctn',
                r'ctn\s+for\s+bl',
                r'container\s+for\s+bl'
            ],
            'invoice_request': [
                r'invoice',
                r'bill',
                r'receipt',
                r'statement',
                r'get\s+invoice',
                r'need\s+invoice',
                r'send\s+invoice'
            ],
            'payment_status': [
                r'payment\s+status',
                r'payment\s+confirmation',
                r'payment\s+received',
                r'payment\s+receipt',
                r'confirm\s+payment',
                r'payment\s+update'
            ],
            'fee_inquiry': [
                r'fee',
                r'cost',
                r'price',
                r'charge',
                r'amount\s+due',
                r'total\s+cost',
                r'how\s+much',
                r'what\s+is\s+the\s+cost'
            ],
            'business_hours': [
                r'business\s+hours',
                r'working\s+hours',
                r'office\s+hours',
                r'operating\s+hours',
                r'when\s+are\s+you\s+open',
                r'what\s+time\s+do\s+you\s+open',
                r'营业时间',
                r'工作时间'
            ],
            'payment_methods': [
                r'payment\s+method',
                r'how\s+to\s+pay',
                r'payment\s+options',
                r'bank\s+transfer',
                r'wire\s+transfer',
                r'payment\s+instructions',
                r'付款方式',
                r'如何付款'
            ],
            'ctn_process': [
                r'ctn\s+process',
                r'ctn\s+processing',
                r'how\s+long\s+for\s+ctn',
                r'ctn\s+time',
                r'ctn\s+duration',
                r'processing\s+time',
                r'处理时间',
                r'CTN处理'
            ]
        }
        
        # Valid BL numbers and their costs (from your specifications)
        self.valid_bl_costs = {
            '001-123': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
            'NYC220': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
            'NAM20': {'ctn_cost': 500, 'service_cost': 500, 'total': 1000}
        }
    
    def detect_request_types(self, email_body: str) -> List[str]:
        """Detect all request types in email body"""
        detected_types = []
        email_lower = email_body.lower()
        
        for request_type, patterns in self.request_patterns.items():
            for pattern in patterns:
                if re.search(pattern, email_lower, re.IGNORECASE):
                    detected_types.append(request_type)
                    break
        
        return list(set(detected_types))  # Remove duplicates
    
    def extract_amounts(self, email_body: str) -> List[Dict]:
        """Extract mentioned amounts and BL numbers"""
        amounts = []
        
        # Extract BL numbers
        bl_pattern = r'\b(?:BL|bl|Bl)\s*(?:number|num|#|no\.?)?\s*[:#]?\s*([A-Z0-9\-]+)'
        bl_matches = re.findall(bl_pattern, email_body, re.IGNORECASE)
        
        # Extract amounts
        amount_patterns = [
            r'\$?\s*(\d+(?:\.\d{2})?)\s*(?:USD|usd|dollars?|dollars?)',
            r'(\d+(?:\.\d{2})?)\s*(?:USD|usd|dollars?|dollars?)',
            r'USD\s*(\d+(?:\.\d{2})?)',
            r'usd\s*(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match)
                    amounts.append({
                        'amount': amount,
                        'bl_numbers': bl_matches if bl_matches else [],
                        'context': 'payment_mentioned'
                    })
                except ValueError:
                    continue
        
        return amounts
    
    def validate_amounts(self, amounts: List[Dict], ai_reply: str) -> List[Dict]:
        """Validate if amounts mentioned match expected costs"""
        issues = []
        
        for amount_info in amounts:
            amount = amount_info['amount']
            bl_numbers = amount_info['bl_numbers']
            
            if not bl_numbers:
                continue
            
            for bl in bl_numbers:
                if bl in self.valid_bl_costs:
                    expected_total = self.valid_bl_costs[bl]['total']
                    
                    if amount != expected_total:
                        issues.append({
                            'bl_number': bl,
                            'mentioned_amount': amount,
                            'expected_amount': expected_total,
                            'difference': amount - expected_total,
                            'issue_type': 'amount_mismatch'
                        })
        
        return issues
    
    def validate_ai_reply(self, email_body: str, ai_reply: str) -> Dict:
        """
        Validate AI reply against original email
        Returns validation result with issues and recommendations
        """
        # Detect request types in original email
        original_requests = self.detect_request_types(email_body)
        
        # Detect request types in AI reply
        reply_requests = self.detect_request_types(ai_reply)
        
        # Find missed request types
        missed_requests = [req for req in original_requests if req not in reply_requests]
        
        # Extract and validate amounts
        amounts = self.extract_amounts(email_body)
        amount_issues = self.validate_amounts(amounts, ai_reply)
        
        # Generate recommendations
        recommendations = []
        
        if missed_requests:
            recommendations.append(f"Add responses for: {', '.join(missed_requests)}")
        
        if amount_issues:
            for issue in amount_issues:
                if issue['difference'] > 0:
                    recommendations.append(f"Customer overpaid ${issue['difference']} for BL {issue['bl_number']}")
                else:
                    recommendations.append(f"Customer underpaid ${abs(issue['difference'])} for BL {issue['bl_number']}")
        
        # Determine if reclassification is needed
        needs_reclassification = bool(missed_requests or amount_issues)
        
        return {
            'original_request_types': original_requests,
            'missed_request_types': missed_requests,
            'amount_validation_issues': amount_issues,
            'recommendations': recommendations,
            'needs_reclassification': needs_reclassification
        }
    
    def generate_enhanced_prompt(self, email_body: str, validation_result: Dict) -> str:
        """Generate enhanced prompt for OpenAI when validation fails"""
        enhanced_prompt = f"""
IMPORTANT: The following email requires enhanced processing due to missed information.

ORIGINAL EMAIL:
{email_body}

MISSED REQUEST TYPES: {', '.join(validation_result['missed_request_types'])}

AMOUNT ISSUES: {len(validation_result['amount_validation_issues'])} issues detected

ENHANCED INSTRUCTIONS:
1. Ensure you address ALL request types mentioned in the original email
2. Pay special attention to: {', '.join(validation_result['missed_request_types'])}
3. Validate any mentioned amounts against our fee structure
4. Provide complete and accurate responses for all customer inquiries

Please process this email with enhanced attention to detail.
"""
        return enhanced_prompt

def validate_email_with_openai(subject: str, body: str, attachments: List[str], from_addr: str, 
                              original_openai_function) -> Dict:
    """
    Enhanced email processing with validation layer
    
    Args:
        subject: Email subject
        body: Email body
        attachments: List of attachment paths
        from_addr: Sender email address
        original_openai_function: The original handle_email_via_openai function
    
    Returns:
        Dictionary with same structure as original function + validation_result
    """
    logger.info(f"🔍 Validating email from {from_addr}: {subject}")
    
    # Initialize validation system
    validator = EmailValidationSystem()
    
    # First, try original processing
    try:
        original_result = original_openai_function(subject, body, attachments, from_addr)
        logger.info(f"✅ Original processing completed with confidence: {original_result.get('confidence_score', 0)}")
    except Exception as e:
        logger.error(f"❌ Original processing failed: {e}")
        return {
            'classification': 'error',
            'reply': f"Error processing email: {str(e)}",
            'confidence_score': 0.0,
            'validation_result': {}
        }
    
    # Validate the response
    validation_result = validator.validate_ai_reply(body, original_result.get('reply', ''))
    
    # If validation passes, return original result with validation info
    if not validation_result['needs_reclassification']:
        logger.info("✅ Validation passed - using original response")
        original_result['validation_result'] = validation_result
        return original_result
    
    # If validation fails, try enhanced processing
    logger.warning(f"🚨 Validation failed - attempting enhanced processing")
    logger.warning(f"   Missed requests: {validation_result['missed_request_types']}")
    logger.warning(f"   Amount issues: {len(validation_result['amount_validation_issues'])}")
    
    try:
        # Generate enhanced prompt
        enhanced_prompt = validator.generate_enhanced_prompt(body, validation_result)
        
        # Create enhanced email body
        enhanced_body = f"{enhanced_prompt}\n\nORIGINAL EMAIL:\n{body}"
        
        # Retry with enhanced processing
        enhanced_result = original_openai_function(
            f"[ENHANCED] {subject}", 
            enhanced_body, 
            attachments, 
            from_addr
        )
        
        logger.info(f"✅ Enhanced processing completed with confidence: {enhanced_result.get('confidence_score', 0)}")
        
        # Validate enhanced response
        enhanced_validation = validator.validate_ai_reply(body, enhanced_result.get('reply', ''))
        
        if not enhanced_validation['needs_reclassification']:
            logger.info("✅ Enhanced processing successful - using enhanced response")
            enhanced_result['validation_result'] = enhanced_validation
            enhanced_result['enhanced_processing_used'] = True
            return enhanced_result
        else:
            logger.warning("⚠️ Enhanced processing still has issues - using original with warnings")
            validation_result['enhanced_attempt_failed'] = True
            original_result['validation_result'] = validation_result
            return original_result
            
    except Exception as e:
        logger.error(f"❌ Enhanced processing failed: {e}")
        validation_result['enhanced_attempt_failed'] = True
        original_result['validation_result'] = validation_result
        return original_result

# Production integration functions
def integrate_validation_into_ingestion():
    """
    Instructions for integrating validation into existing email ingestion
    """
    integration_guide = """
=== PRODUCTION INTEGRATION GUIDE ===

1. BACKUP YOUR CURRENT SYSTEM:
   - Backup utils/ingest_emails.py
   - Backup email_ingestor.py
   - Backup email_scheduler.py

2. MODIFY utils/ingest_emails.py:
   Add these imports at the top:
   ```python
   from email_validation_production import validate_email_with_openai
   ```

3. REPLACE the OpenAI call in handle_email_via_openai function:
   ```python
   # OLD CODE:
   action = handle_email_via_openai(subject, body_text, attachments, from_addr)
   
   # NEW CODE:
   action = validate_email_with_openai(
       subject, body_text, attachments, from_addr, handle_email_via_openai
   )
   ```

4. ADD VALIDATION LOGGING:
   ```python
   if action.get('validation_result', {}).get('needs_reclassification'):
       logger.warning(f"Validation issues for email {email_id}: {action['validation_result']}")
   ```

5. TEST WITH SMALL BATCH:
   - Send 2-3 test emails
   - Monitor logs for validation results
   - Verify improvements

6. FULL DEPLOYMENT:
   - Monitor for 24-48 hours
   - Check validation success rates
   - Adjust if needed

=== MONITORING ===
- Check logs for "Validation failed" messages
- Monitor confidence scores
- Track customer satisfaction
- Review validation results weekly

=== ROLLBACK PLAN ===
If issues occur, simply revert the changes in utils/ingest_emails.py
"""
    
    return integration_guide

if __name__ == "__main__":
    print("🔧 Email Validation System - Production Ready")
    print("=" * 50)
    print(integrate_validation_into_ingestion()) 