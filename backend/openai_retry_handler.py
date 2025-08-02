#!/usr/bin/env python3
"""
OpenAI Retry Handler
Handles 429 errors with exponential backoff and smart retries
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

def retry_on_429(max_retries=3, base_delay=1, max_delay=60, exponential_base=2):
    """
    Decorator to retry OpenAI calls on 429 errors with exponential backoff
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if it's a 429 error
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        if attempt < max_retries:
                            # Calculate delay with exponential backoff and jitter
                            delay = min(base_delay * (exponential_base ** attempt), max_delay)
                            jitter = random.uniform(0, 0.1 * delay)  # 10% jitter
                            total_delay = delay + jitter
                            
                            logger.warning(f"OpenAI 429 error (attempt {attempt + 1}/{max_retries + 1}). "
                                         f"Retrying in {total_delay:.1f}s...")
                            
                            time.sleep(total_delay)
                            continue
                        else:
                            logger.error(f"OpenAI 429 error after {max_retries} retries. Giving up.")
                    else:
                        # Not a 429 error, don't retry
                        logger.error(f"OpenAI error (not 429): {e}")
                        break
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator

class OpenAIRetryHandler:
    """
    Advanced retry handler for OpenAI API calls
    """
    
    def __init__(self, max_retries=3, base_delay=1, max_delay=60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_count = 0
        self.total_retries = 0
    
    def call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function with retry logic for 429 errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"OpenAI call succeeded after {attempt} retries")
                return result
                
            except Exception as e:
                last_exception = e
                self.retry_count += 1
                
                # Check if it's a 429 error
                if "429" in str(e) or "rate limit" in str(e).lower():
                    if attempt < self.max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        
                        # Add jitter to prevent thundering herd
                        jitter = random.uniform(0, 0.2 * delay)
                        total_delay = delay + jitter
                        
                        logger.warning(f"OpenAI 429 error (attempt {attempt + 1}/{self.max_retries + 1}). "
                                     f"Retrying in {total_delay:.1f}s...")
                        
                        time.sleep(total_delay)
                        continue
                    else:
                        logger.error(f"OpenAI 429 error after {self.max_retries} retries. Giving up.")
                else:
                    # Not a 429 error, don't retry
                    logger.error(f"OpenAI error (not 429): {e}")
                    break
        
        # If we get here, all retries failed
        self.total_retries += self.retry_count
        raise last_exception
    
    def get_stats(self):
        """Get retry statistics"""
        return {
            'retry_count': self.retry_count,
            'total_retries': self.total_retries,
            'max_retries': self.max_retries
        }

# Global retry handler
retry_handler = OpenAIRetryHandler()

def smart_openai_call(func: Callable, *args, **kwargs) -> Any:
    """
    Smart OpenAI call with retry logic and rate limiting
    """
    from openai_rate_limiter import rate_limiter
    
    # Wait for rate limit
    wait_time = rate_limiter.wait_if_needed()
    if wait_time > 0:
        logger.info(f"Rate limiting: Waiting {wait_time:.1f}s")
        time.sleep(wait_time)
    
    # Record the request
    rate_limiter.record_request()
    
    # Call with retry logic
    return retry_handler.call_with_retry(func, *args, **kwargs)

# Email processing with rate limiting
def process_email_with_rate_limit(email_data):
    """
    Process email with rate limiting to avoid 429 errors
    """
    from openai_rate_limiter import email_rate_limiter
    
    # Wait for processing slot
    if not email_rate_limiter.can_process_email():
        logger.info("Rate limit: Waiting for email processing slot")
        email_rate_limiter.wait_for_slot()
    
    # Process the email
    try:
        # Your email processing logic here
        result = process_single_email(email_data)
        email_rate_limiter.record_email_processed()
        return result
    except Exception as e:
        logger.error(f"Email processing error: {e}")
        raise e

def process_single_email(email_data):
    """
    Process a single email (placeholder for your actual logic)
    """
    # This would be your actual email processing logic
    # For now, just a placeholder
    time.sleep(0.1)  # Simulate processing time
    return {"status": "processed"}

if __name__ == "__main__":
    print("🧪 Testing OpenAI Retry Handler")
    print("=" * 40)
    
    # Test the retry handler
    @retry_on_429(max_retries=2, base_delay=1)
    def test_function():
        import random
        if random.random() < 0.7:  # 70% chance of 429 error
            raise Exception("429 Too Many Requests")
        return "Success!"
    
    try:
        result = test_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Final error: {e}")
    
    # Show stats
    stats = retry_handler.get_stats()
    print(f"\n📊 Retry Statistics:")
    print(f"   Retry count: {stats['retry_count']}")
    print(f"   Total retries: {stats['total_retries']}") 