from datetime import datetime, timedelta
import pytz

def get_hk_date_range(search_date_str):
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    search_date = datetime.strptime(search_date_str, '%Y-%m-%d')
    search_date = hk_tz.localize(search_date)
    next_date = search_date + timedelta(days=1)
    return search_date, next_date

def verify_captcha(token):
    """Bypass reCAPTCHA verification (disabled for China compatibility)."""
    return True
