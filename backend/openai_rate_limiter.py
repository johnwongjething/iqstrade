#!/usr/bin/env python3
"""
OpenAI Rate Limiter
Prevents 429 errors by controlling request frequency
"""

import time
import threading
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class OpenAIRateLimiter:
    """
    Rate limiter for OpenAI API calls
    Prevents 429 errors by controlling request frequency
    """
    
    def __init__(self, requests_per_minute=60, requests_per_hour=3500):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_window = deque()
        self.hour_window = deque()
        self.lock = threading.Lock()
        
        # Cleanup old entries every minute
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up old timestamps"""
        def cleanup():
            while True:
                time.sleep(60)  # Run every minute
                self._cleanup_old_entries()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_entries(self):
        """Remove timestamps older than the windows"""
        now = datetime.now()
        
        with self.lock:
            # Clean minute window (keep last 60 seconds)
            while self.minute_window and (now - self.minute_window[0]) > timedelta(minutes=1):
                self.minute_window.popleft()
            
            # Clean hour window (keep last 60 minutes)
            while self.hour_window and (now - self.hour_window[0]) > timedelta(hours=1):
                self.hour_window.popleft()
    
    def wait_if_needed(self):
        """
        Wait if rate limits would be exceeded
        Returns the wait time in seconds
        """
        with self.lock:
            now = datetime.now()
            
            # Check minute limit
            minute_count = len(self.minute_window)
            if minute_count >= self.requests_per_minute:
                # Wait until oldest request is more than 1 minute old
                oldest = self.minute_window[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit: Waiting {wait_time:.1f}s for minute window")
                    return wait_time
            
            # Check hour limit
            hour_count = len(self.hour_window)
            if hour_count >= self.requests_per_hour:
                # Wait until oldest request is more than 1 hour old
                oldest = self.hour_window[0]
                wait_time = 3600 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit: Waiting {wait_time:.1f}s for hour window")
                    return wait_time
            
            return 0
    
    def record_request(self):
        """Record that a request was made"""
        now = datetime.now()
        
        with self.lock:
            self.minute_window.append(now)
            self.hour_window.append(now)
    
    def get_status(self):
        """Get current rate limit status"""
        with self.lock:
            return {
                'minute_requests': len(self.minute_window),
                'hour_requests': len(self.hour_window),
                'minute_limit': self.requests_per_minute,
                'hour_limit': self.requests_per_hour
            }

# Global rate limiter instance
rate_limiter = OpenAIRateLimiter()

def rate_limited_openai_call(openai_function, *args, **kwargs):
    """
    Wrapper for OpenAI calls with rate limiting
    
    Usage:
        result = rate_limited_openai_call(openai.ChatCompletion.create, ...)
    """
    # Wait if needed
    wait_time = rate_limiter.wait_if_needed()
    if wait_time > 0:
        time.sleep(wait_time)
    
    # Record the request
    rate_limiter.record_request()
    
    # Make the actual call
    try:
        return openai_function(*args, **kwargs)
    except Exception as e:
        if "429" in str(e):
            logger.error(f"Rate limit exceeded despite rate limiting: {e}")
            # Wait longer and retry once
            time.sleep(30)
            rate_limiter.record_request()
            return openai_function(*args, **kwargs)
        else:
            raise e

def get_rate_limit_status():
    """Get current rate limit status"""
    return rate_limiter.get_status()

def set_rate_limits(requests_per_minute=None, requests_per_hour=None):
    """Update rate limits"""
    if requests_per_minute:
        rate_limiter.requests_per_minute = requests_per_minute
    if requests_per_hour:
        rate_limiter.requests_per_hour = requests_per_hour
    
    logger.info(f"Rate limits updated: {requests_per_minute}/min, {requests_per_hour}/hour")

# Email processing rate limiter
class EmailProcessingRateLimiter:
    """
    Rate limiter specifically for email processing
    Controls how many emails are processed per minute
    """
    
    def __init__(self, emails_per_minute=10):
        self.emails_per_minute = emails_per_minute
        self.last_processed = deque()
        self.lock = threading.Lock()
    
    def can_process_email(self):
        """Check if we can process another email"""
        now = datetime.now()
        
        with self.lock:
            # Remove emails older than 1 minute
            while self.last_processed and (now - self.last_processed[0]) > timedelta(minutes=1):
                self.last_processed.popleft()
            
            return len(self.last_processed) < self.emails_per_minute
    
    def record_email_processed(self):
        """Record that an email was processed"""
        with self.lock:
            self.last_processed.append(datetime.now())
    
    def wait_for_slot(self):
        """Wait until a processing slot is available"""
        while not self.can_process_email():
            time.sleep(6)  # Wait 6 seconds before checking again

# Global email rate limiter
email_rate_limiter = EmailProcessingRateLimiter()

if __name__ == "__main__":
    # Test the rate limiter
    print("🧪 Testing OpenAI Rate Limiter")
    print("=" * 40)
    
    # Simulate some requests
    for i in range(5):
        wait_time = rate_limiter.wait_if_needed()
        if wait_time > 0:
            print(f"Request {i+1}: Waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        else:
            print(f"Request {i+1}: No wait needed")
        
        rate_limiter.record_request()
        time.sleep(0.1)  # Small delay
    
    # Show status
    status = get_rate_limit_status()
    print(f"\n📊 Rate Limit Status:")
    print(f"   Minute requests: {status['minute_requests']}/{status['minute_limit']}")
    print(f"   Hour requests: {status['hour_requests']}/{status['hour_limit']}") 