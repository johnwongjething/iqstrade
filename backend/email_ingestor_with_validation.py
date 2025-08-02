#!/usr/bin/env python3
"""
Email Ingestor with Validation Wrapper
Adds validation layer to existing email_ingestor without changing core logic
"""
import logging
from email_classification_validator import validate_email_classification, email_validator

logger = logging.getLogger(__name__)

def handle_email_via_openai_with_validation(subject, body, attachments, from_addr):
    """
    Wrapper around existing handle_email_via_openai with validation
    Non-disruptive addition to existing system
    """
    
    # Import the original function
    from email_ingestor import handle_email_via_openai
    
    # Call original function
    logger.info("[VALIDATION] Calling original email classification...")
    original_result = handle_email_via_openai(subject, body, attachments, from_addr)
    
    # Extract results
    request_types = original_result.get('request_types', [])
    ai_reply = original_result.get('reply', '')
    bl_numbers = original_result.get('bl_numbers', [])
    
    # Validate the results
    logger.info("[VALIDATION] Validating classification results...")
    validation_result = validate_email_classification(
        email_body=body,
        subject=subject,
        request_types=request_types,
        ai_reply=ai_reply,
        bl_numbers=bl_numbers
    )
    
    # If validation found issues, enhance the prompt and retry
    if validation_result['needs_reclassification']:
        logger.warning("[VALIDATION] Issues detected, attempting reclassification...")
        
        # Generate enhanced prompt
        enhanced_prompt = email_validator.generate_enhanced_prompt(
            f"Subject: {subject}\n\nBody: {body}",
            validation_result
        )
        
        # Create enhanced messages for OpenAI
        enhanced_messages = [
            {"role": "system", "content": "You're a shipping email agent. Pay special attention to ALL customer questions and correct any wrong amounts mentioned."},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        try:
            # Call OpenAI with enhanced prompt
            from email_ingestor import openai_call_with_fallback
            enhanced_response = openai_call_with_fallback(enhanced_messages, temperature=0)
            
            # Parse enhanced response
            import json
            try:
                enhanced_action = json.loads(enhanced_response)
                enhanced_reply = enhanced_action.get('reply', ai_reply)
                
                # Update the result with enhanced reply
                original_result['reply'] = enhanced_reply
                original_result['validation_applied'] = True
                original_result['validation_issues'] = validation_result
                
                logger.info("[VALIDATION] Enhanced reply applied successfully")
                
            except json.JSONDecodeError:
                logger.error("[VALIDATION] Failed to parse enhanced OpenAI response")
                original_result['validation_applied'] = False
                original_result['validation_issues'] = validation_result
                
        except Exception as e:
            logger.error(f"[VALIDATION] Failed to get enhanced response: {e}")
            original_result['validation_applied'] = False
            original_result['validation_issues'] = validation_result
    else:
        logger.info("[VALIDATION] No issues detected, using original result")
        original_result['validation_applied'] = False
        original_result['validation_issues'] = validation_result
    
    return original_result

def process_inbox_with_validation():
    """
    Wrapper around existing process_inbox with validation
    """
    from email_ingestor import process_inbox
    
    logger.info("[VALIDATION] Starting inbox processing with validation...")
    results = process_inbox()
    
    # Log validation summary
    validation_applied_count = sum(1 for result in results if result.get('validation_applied', False))
    logger.info(f"[VALIDATION] Processing complete. Validation applied to {validation_applied_count} emails.")
    
    return results

def ingest_emails_with_validation():
    """
    Wrapper around existing ingest_emails with validation
    """
    from utils.ingest_emails import ingest_emails
    
    logger.info("[VALIDATION] Starting email ingestion with validation...")
    results = ingest_emails()
    
    # Log validation summary
    validation_applied_count = sum(1 for result in results if result.get('validation_applied', False))
    logger.info(f"[VALIDATION] Ingestion complete. Validation applied to {validation_applied_count} emails.")
    
    return results 