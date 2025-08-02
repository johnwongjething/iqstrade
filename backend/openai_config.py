#!/usr/bin/env python3
"""
OpenAI Configuration
Centralized configuration for OpenAI rate limits and settings
Production Strategy: GPT-4o for OCR, GPT-3.5-turbo for email replies
"""

import os
from typing import Dict, Any

class OpenAIConfig:
    """Configuration for OpenAI API usage"""
    
    # Rate limits (requests per time window)
    REQUESTS_PER_MINUTE = int(os.getenv('OPENAI_REQUESTS_PER_MINUTE', '60'))
    REQUESTS_PER_HOUR = int(os.getenv('OPENAI_REQUESTS_PER_HOUR', '3500'))
    
    # Email processing rate limits
    EMAILS_PER_MINUTE = int(os.getenv('EMAILS_PER_MINUTE', '10'))
    
    # Retry settings
    MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
    BASE_DELAY = float(os.getenv('OPENAI_BASE_DELAY', '1.0'))
    MAX_DELAY = float(os.getenv('OPENAI_MAX_DELAY', '60.0'))
    
    # Production Model Strategy
    # OCR: GPT-4o (higher accuracy for document processing)
    # Email: GPT-3.5-turbo (faster, cheaper for text processing)
    OCR_MODEL = os.getenv('OPENAI_OCR_MODEL', 'gpt-4o')
    EMAIL_MODEL = os.getenv('OPENAI_EMAIL_MODEL', 'gpt-3.5-turbo')
    
    # Fallback models
    OCR_FALLBACK_MODEL = os.getenv('OPENAI_OCR_FALLBACK_MODEL', 'gpt-3.5-turbo')
    EMAIL_FALLBACK_MODEL = os.getenv('OPENAI_EMAIL_FALLBACK_MODEL', 'gpt-4o')
    
    # API settings
    TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.0'))
    MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
    
    # Fallback settings
    ENABLE_FALLBACK = os.getenv('OPENAI_ENABLE_FALLBACK', 'true').lower() == 'true'
    
    @classmethod
    def get_rate_limits(cls) -> Dict[str, int]:
        """Get rate limit settings"""
        return {
            'requests_per_minute': cls.REQUESTS_PER_MINUTE,
            'requests_per_hour': cls.REQUESTS_PER_HOUR,
            'emails_per_minute': cls.EMAILS_PER_MINUTE
        }
    
    @classmethod
    def get_retry_settings(cls) -> Dict[str, Any]:
        """Get retry settings"""
        return {
            'max_retries': cls.MAX_RETRIES,
            'base_delay': cls.BASE_DELAY,
            'max_delay': cls.MAX_DELAY
        }
    
    @classmethod
    def get_ocr_settings(cls) -> Dict[str, Any]:
        """Get OCR-specific settings"""
        return {
            'primary_model': cls.OCR_MODEL,
            'fallback_model': cls.OCR_FALLBACK_MODEL,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'enable_fallback': cls.ENABLE_FALLBACK
        }
    
    @classmethod
    def get_email_settings(cls) -> Dict[str, Any]:
        """Get email-specific settings"""
        return {
            'primary_model': cls.EMAIL_MODEL,
            'fallback_model': cls.EMAIL_FALLBACK_MODEL,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'enable_fallback': cls.ENABLE_FALLBACK
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("🔧 OpenAI Production Configuration")
        print("=" * 50)
        print(f"📊 Rate Limits:")
        print(f"   Requests per minute: {cls.REQUESTS_PER_MINUTE}")
        print(f"   Requests per hour: {cls.REQUESTS_PER_HOUR}")
        print(f"   Emails per minute: {cls.EMAILS_PER_MINUTE}")
        print(f"\n🔄 Retry Settings:")
        print(f"   Max retries: {cls.MAX_RETRIES}")
        print(f"   Base delay: {cls.BASE_DELAY}s")
        print(f"   Max delay: {cls.MAX_DELAY}s")
        print(f"\n🤖 Model Strategy:")
        print(f"   OCR Primary: {cls.OCR_MODEL} (high accuracy)")
        print(f"   OCR Fallback: {cls.OCR_FALLBACK_MODEL}")
        print(f"   Email Primary: {cls.EMAIL_MODEL} (fast, cheap)")
        print(f"   Email Fallback: {cls.EMAIL_FALLBACK_MODEL}")
        print(f"\n⚙️ API Settings:")
        print(f"   Temperature: {cls.TEMPERATURE}")
        print(f"   Max tokens: {cls.MAX_TOKENS}")
        print(f"   Fallback enabled: {cls.ENABLE_FALLBACK}")

# Environment variable examples
ENV_EXAMPLES = """
# Add these to your .env.local file for production:

# Rate limits
OPENAI_REQUESTS_PER_MINUTE=60
OPENAI_REQUESTS_PER_HOUR=3500
EMAILS_PER_MINUTE=10

# Retry settings
OPENAI_MAX_RETRIES=3
OPENAI_BASE_DELAY=1.0
OPENAI_MAX_DELAY=60.0

# Production Model Strategy
OPENAI_OCR_MODEL=gpt-4o
OPENAI_EMAIL_MODEL=gpt-3.5-turbo
OPENAI_OCR_FALLBACK_MODEL=gpt-3.5-turbo
OPENAI_EMAIL_FALLBACK_MODEL=gpt-4o

# API settings
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=4000
OPENAI_ENABLE_FALLBACK=true
"""

if __name__ == "__main__":
    OpenAIConfig.print_config()
    print(f"\n📝 Environment Variables:")
    print(ENV_EXAMPLES) 