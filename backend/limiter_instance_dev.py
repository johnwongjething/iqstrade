from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Development limiter with higher limits for testing
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per hour"]  # Higher limits for development
) 