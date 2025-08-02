#!/usr/bin/env python3
"""
Email Classification Validator
Rechecks classification results to catch missed information
Non-disruptive addition to existing system
"""
import re
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmailClassificationValidator:
    """
    Validates and enhances email classification results
    Catches missed information without changing existing logic
    """
    
    def __init__(self):
        # Critical keywords that should trigger specific request types
        self.critical_patterns = {
            'ctn_process': [
                r'\b(how\s+long|time|duration|process)\s+(?:does\s+it\s+take\s+)?(?:to\s+)?(?:process\s+)?(?:ctn|container)\b',
                r'\b(ctn|container)\s+(?:processing\s+)?(?:time|duration|how\s+long)\b',
                r'\b(?:when|how\s+soon)\s+(?:will\s+)?(?:ctn|container)\s+(?:be\s+)?(?:ready|processed)\b'
            ],
            'payment_methods': [
                r'\b(?:how\s+to\s+pay|payment\s+method|payment\s+option|how\s+can\s+i\s+pay)\b',
                r'\b(?:what\s+)?(?:payment\s+)?(?:methods?|options?)\s+(?:do\s+you\s+)?(?:accept|offer)\b'
            ],
            'business_hours': [
                r'\b(?:what\s+are\s+)?(?:your\s+)?(?:business\s+hours|operating\s+hours|office\s+hours)\b',
                r'\b(?:when\s+are\s+you\s+)?(?:open|available)\b'
            ],
            'amount_validation': [
                r'\b(?:bl\s+)?(?:nam20|001-123|nyc220)\s*[:：]?\s*\$?\d+\b',
                r'\b(?:i\s+need\s+to\s+pay|paying|payment)\s+(?:for\s+)?(?:bl\s+)?(?:nam20|001-123|nyc220)\b'
            ]
        }
        
        # Valid BL costs for amount validation
        self.valid_bl_costs = {
            '001-123': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
            'NYC220': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
            'NAM20': {'ctn_cost': 500, 'service_cost': 500, 'total': 1000}
        }
    
    def validate_classification(self, email_body: str, subject: str, request_types: List[str], 
                              ai_reply: str, bl_numbers: List[str]) -> Dict[str, Any]:
        """
        Validates classification results and identifies missed information
        
        Returns:
            Dict with validation results and recommendations
        """
        validation_result = {
            'original_request_types': request_types,
            'missed_request_types': [],
            'amount_validation_issues': [],
            'recommendations': [],
            'needs_reclassification': False
        }
        
        # Combine email content for analysis
        full_text = f"{subject}\n\n{email_body}".lower()
        
        # Check for missed critical patterns
        for req_type, patterns in self.critical_patterns.items():
            if req_type not in request_types:
                for pattern in patterns:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        validation_result['missed_request_types'].append(req_type)
                        validation_result['recommendations'].append(
                            f"Add '{req_type}' to request types - found pattern: {pattern}"
                        )
                        break
        
        # Check for amount validation issues
        amount_issues = self._validate_amounts(full_text, ai_reply)
        if amount_issues:
            validation_result['amount_validation_issues'] = amount_issues
            validation_result['recommendations'].append(
                "Add amount validation to catch incorrect customer amounts"
            )
        
        # Check if AI reply addresses all detected request types
        reply_coverage = self._check_reply_coverage(request_types, ai_reply)
        if reply_coverage['missing_coverage']:
            validation_result['recommendations'].append(
                f"AI reply missing coverage for: {', '.join(reply_coverage['missing_coverage'])}"
            )
        
        # Determine if reclassification is needed
        if (validation_result['missed_request_types'] or 
            validation_result['amount_validation_issues'] or
            reply_coverage['missing_coverage']):
            validation_result['needs_reclassification'] = True
        
        return validation_result
    
    def _validate_amounts(self, email_text: str, ai_reply: str) -> List[Dict[str, str]]:
        """Validates if customer mentioned wrong amounts for BLs"""
        issues = []
        
        # Extract BL amounts mentioned by customer
        bl_amount_pattern = r'\b(?:bl\s+)?(nam20|001-123|nyc220)\s*[:：]?\s*\$?(\d+)\b'
        customer_amounts = re.findall(bl_amount_pattern, email_text, re.IGNORECASE)
        
        for bl, amount in customer_amounts:
            bl_upper = bl.upper()
            if bl_upper in self.valid_bl_costs:
                expected_total = self.valid_bl_costs[bl_upper]['total']
                customer_amount = int(amount)
                
                if customer_amount != expected_total:
                    issues.append({
                        'bl': bl_upper,
                        'customer_amount': customer_amount,
                        'correct_amount': expected_total,
                        'issue': f"Customer mentioned ${customer_amount} for {bl_upper}, but correct amount is ${expected_total}"
                    })
        
        return issues
    
    def _check_reply_coverage(self, request_types: List[str], ai_reply: str) -> Dict[str, Any]:
        """Checks if AI reply covers all detected request types"""
        reply_lower = ai_reply.lower()
        missing_coverage = []
        
        coverage_checks = {
            'ctn_process': ['process', 'time', 'duration', 'how long'],
            'payment_methods': ['payment method', 'bank transfer', 'how to pay'],
            'business_hours': ['hours', 'open', 'available'],
            'ctn_request': ['ctn', 'container number'],
            'invoice_request': ['invoice', 'bill'],
            'fee_inquiry': ['fee', 'cost', 'charge'],
            'payment_status': ['status', 'due', 'balance'],
            'payment_receipt': ['payment', 'receipt', 'received']
        }
        
        for req_type in request_types:
            if req_type in coverage_checks:
                keywords = coverage_checks[req_type]
                if not any(keyword in reply_lower for keyword in keywords):
                    missing_coverage.append(req_type)
        
        return {
            'missing_coverage': missing_coverage,
            'coverage_score': len(request_types) - len(missing_coverage) / max(len(request_types), 1)
        }
    
    def generate_enhanced_prompt(self, original_prompt: str, validation_result: Dict[str, Any]) -> str:
        """
        Generates an enhanced prompt that includes missed information
        """
        if not validation_result['needs_reclassification']:
            return original_prompt
        
        enhanced_sections = []
        
        # Add missed request types
        if validation_result['missed_request_types']:
            enhanced_sections.append(
                f"IMPORTANT: The customer also asked about: {', '.join(validation_result['missed_request_types'])}"
            )
        
        # Add amount validation issues
        if validation_result['amount_validation_issues']:
            amount_corrections = []
            for issue in validation_result['amount_validation_issues']:
                amount_corrections.append(
                    f"- {issue['bl']}: Customer mentioned ${issue['customer_amount']}, but correct amount is ${issue['correct_amount']}"
                )
            enhanced_sections.append(
                f"AMOUNT CORRECTIONS NEEDED:\n" + "\n".join(amount_corrections)
            )
        
        # Add recommendations
        if validation_result['recommendations']:
            enhanced_sections.append(
                f"ADDITIONAL REQUIREMENTS:\n" + "\n".join(validation_result['recommendations'])
            )
        
        enhanced_prompt = original_prompt + "\n\n" + "\n\n".join(enhanced_sections)
        
        return enhanced_prompt
    
    def log_validation_results(self, email_id: int, validation_result: Dict[str, Any]):
        """Logs validation results for monitoring"""
        if validation_result['needs_reclassification']:
            logger.warning(f"[VALIDATION] Email {email_id} needs reclassification:")
            logger.warning(f"  - Missed request types: {validation_result['missed_request_types']}")
            logger.warning(f"  - Amount issues: {len(validation_result['amount_validation_issues'])}")
            logger.warning(f"  - Recommendations: {validation_result['recommendations']}")
        else:
            logger.info(f"[VALIDATION] Email {email_id} classification validated successfully")

# Global validator instance
email_validator = EmailClassificationValidator()

def validate_email_classification(email_body: str, subject: str, request_types: List[str], 
                                ai_reply: str, bl_numbers: List[str], email_id: int = None) -> Dict[str, Any]:
    """
    Convenience function to validate email classification
    """
    result = email_validator.validate_classification(
        email_body, subject, request_types, ai_reply, bl_numbers
    )
    
    if email_id:
        email_validator.log_validation_results(email_id, result)
    
    return result 