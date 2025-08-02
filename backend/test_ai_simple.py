#!/usr/bin/env python3
"""
Simple test for AI function
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.local')

def test_ai_function():
    """Test the AI function directly"""
    try:
        logger.info("🧪 Testing AI function...")
        
        # Import the function
        from email_ingestor_enhanced import handle_email_via_openai
        
        # Test data
        subject = "Payment Receipt for BL-1234"
        body = "Hello, I have made the payment of $500 for BL-1234. Please confirm receipt."
        attachments = []
        from_addr = "test@example.com"
        
        logger.info(f"📧 Subject: {subject}")
        logger.info(f"📧 Body: {body}")
        logger.info(f"📧 From: {from_addr}")
        
        # Call AI function
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        logger.info(f"🤖 AI Result: {result}")
        
        if result:
            logger.info("✅ AI function working!")
            logger.info(f"   Classification: {result.get('classification')}")
            logger.info(f"   Confidence: {result.get('confidence_score')}")
            logger.info(f"   Auto Send: {result.get('auto_send')}")
            logger.info(f"   Custom Reply: {result.get('custom_reply', '')[:100]}...")
            return True
        else:
            logger.error("❌ AI function returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing AI function: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OpenAI API key not found in environment")
            return False
        
        logger.info(f"🔑 OpenAI API key found: {api_key[:10]}...")
        
        # Test simple OpenAI call
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        logger.info(f"✅ OpenAI connection working: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        logger.error(f"❌ OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing AI functionality...")
    
    # Test OpenAI connection first
    if test_openai_connection():
        # Test AI function
        test_ai_function()
    else:
        logger.error("❌ Cannot test AI function without OpenAI connection") 