"""
Centralized Timezone Utilities for IQS Trade System
Ensures consistent Hong Kong time usage across the entire application
"""

from datetime import datetime, timedelta
import pytz
from typing import Optional, Union

# Hong Kong timezone
HK_TIMEZONE = pytz.timezone('Asia/Hong_Kong')

def get_hk_now() -> datetime:
    """
    Get current time in Hong Kong timezone.
    
    Returns:
        datetime: Current time in Hong Kong timezone
    """
    return datetime.now(HK_TIMEZONE)

def get_hk_now_iso() -> str:
    """
    Get current time in Hong Kong timezone as ISO format string.
    
    Returns:
        str: Current time in Hong Kong timezone as ISO format
    """
    return get_hk_now().isoformat()

def get_hk_now_str(format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Get current time in Hong Kong timezone as formatted string.
    
    Args:
        format_str: Format string for datetime.strftime()
    
    Returns:
        str: Current time in Hong Kong timezone as formatted string
    """
    return get_hk_now().strftime(format_str)

def get_hk_timestamp() -> str:
    """
    Get current time in Hong Kong timezone as timestamp string.
    
    Returns:
        str: Current time in Hong Kong timezone as YYYYMMDD_HHMMSS format
    """
    return get_hk_now().strftime('%Y%m%d_%H%M%S')

def convert_to_hk_time(dt: datetime) -> datetime:
    """
    Convert a datetime to Hong Kong timezone.
    If datetime is naive (no timezone), assumes UTC.
    
    Args:
        dt: datetime object to convert
    
    Returns:
        datetime: datetime in Hong Kong timezone
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(HK_TIMEZONE)

def convert_to_hk_iso(dt: datetime) -> str:
    """
    Convert a datetime to Hong Kong timezone and return as ISO format.
    
    Args:
        dt: datetime object to convert
    
    Returns:
        str: datetime in Hong Kong timezone as ISO format
    """
    return convert_to_hk_time(dt).isoformat()

def get_hk_date_range(search_date_str: str) -> tuple[datetime, datetime]:
    """
    Get Hong Kong timezone date range for a given date string.
    
    Args:
        search_date_str: Date string in YYYY-MM-DD format
    
    Returns:
        tuple: (start_date, end_date) in Hong Kong timezone
    """
    search_date = datetime.strptime(search_date_str, '%Y-%m-%d')
    search_date = HK_TIMEZONE.localize(search_date)
    next_date = search_date + timedelta(days=1)
    return search_date, next_date

def get_hk_business_hours() -> dict:
    """
    Get Hong Kong business hours information.
    
    Returns:
        dict: Business hours information
    """
    return {
        'timezone': 'Asia/Hong_Kong',
        'business_hours': 'Monday to Friday, 9:00 AM to 5:00 PM (Hong Kong time)',
        'current_time': get_hk_now_str(),
        'is_business_hours': is_hk_business_hours()
    }

def is_hk_business_hours() -> bool:
    """
    Check if current time is within Hong Kong business hours.
    
    Returns:
        bool: True if within business hours (Mon-Fri, 9AM-5PM HK time)
    """
    now = get_hk_now()
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's between 9 AM and 5 PM
    business_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    business_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
    
    return business_start <= now <= business_end

def get_hk_time_ago(hours: int = 0, days: int = 0, minutes: int = 0) -> datetime:
    """
    Get Hong Kong time from specified time ago.
    
    Args:
        hours: Number of hours ago
        days: Number of days ago
        minutes: Number of minutes ago
    
    Returns:
        datetime: Hong Kong time from specified time ago
    """
    now = get_hk_now()
    return now - timedelta(hours=hours, days=days, minutes=minutes)

def format_hk_time_for_display(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format a datetime for display in Hong Kong timezone.
    
    Args:
        dt: datetime object to format
        format_str: Format string for strftime
    
    Returns:
        str: Formatted datetime string in Hong Kong timezone
    """
    hk_dt = convert_to_hk_time(dt)
    return hk_dt.strftime(format_str)

def get_hk_timezone_info() -> dict:
    """
    Get Hong Kong timezone information.
    
    Returns:
        dict: Timezone information
    """
    now = get_hk_now()
    return {
        'timezone': 'Asia/Hong_Kong',
        'current_time': now.isoformat(),
        'current_time_formatted': now.strftime('%Y-%m-%d %H:%M:%S'),
        'utc_offset': now.strftime('%z'),
        'is_dst': now.dst() != timedelta(0),
        'timezone_name': now.strftime('%Z')
    }

# Convenience functions for common use cases
def hk_now() -> datetime:
    """Alias for get_hk_now()"""
    return get_hk_now()

def hk_now_iso() -> str:
    """Alias for get_hk_now_iso()"""
    return get_hk_now_iso()

def hk_timestamp() -> str:
    """Alias for get_hk_timestamp()"""
    return get_hk_timestamp() 