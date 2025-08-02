#!/usr/bin/env python3
"""
Performance Monitoring for Concurrent Users
Tracks response times, database performance, and system health
"""

import time
import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import psutil
import os
from utils.timezone_utils import get_hk_now_iso

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor system performance for concurrent user handling"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)  # Keep last 1000 requests
        self.db_times = deque(maxlen=1000)       # Keep last 1000 DB queries
        self.error_counts = defaultdict(int)     # Track errors by type
        self.active_connections = 0              # Track active DB connections
        self.lock = threading.Lock()
        
        # Performance thresholds
        self.slow_request_threshold = 5.0  # 5 seconds
        self.slow_db_threshold = 1.0       # 1 second
        self.max_memory_percent = 80       # 80% memory usage
        
    def start_request_timer(self):
        """Start timing a request"""
        return time.time()
    
    def end_request_timer(self, start_time, endpoint=None):
        """End timing a request and record it"""
        duration = time.time() - start_time
        
        with self.lock:
            self.request_times.append({
                'duration': duration,
                'endpoint': endpoint,
                'timestamp': get_hk_now_iso()
            })
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(f"Slow request: {endpoint} took {duration:.2f}s")
    
    def start_db_timer(self):
        """Start timing a database operation"""
        return time.time()
    
    def end_db_timer(self, start_time, operation=None):
        """End timing a database operation and record it"""
        duration = time.time() - start_time
        
        with self.lock:
            self.db_times.append({
                'duration': duration,
                'operation': operation,
                'timestamp': get_hk_now_iso()
            })
            
            # Log slow database operations
            if duration > self.slow_db_threshold:
                logger.warning(f"Slow DB operation: {operation} took {duration:.2f}s")
    
    def record_error(self, error_type, error_message=None):
        """Record an error occurrence"""
        with self.lock:
            self.error_counts[error_type] += 1
            
        logger.error(f"Error recorded: {error_type} - {error_message}")
    
    def update_connection_count(self, count):
        """Update active database connection count"""
        with self.lock:
            self.active_connections = count
    
    def get_performance_stats(self):
        """Get current performance statistics"""
        with self.lock:
            # Calculate request statistics
            if self.request_times:
                request_durations = [r['duration'] for r in self.request_times]
                avg_request_time = sum(request_durations) / len(request_durations)
                max_request_time = max(request_durations)
                slow_requests = sum(1 for d in request_durations if d > self.slow_request_threshold)
            else:
                avg_request_time = max_request_time = slow_requests = 0
            
            # Calculate database statistics
            if self.db_times:
                db_durations = [d['duration'] for d in self.db_times]
                avg_db_time = sum(db_durations) / len(db_durations)
                max_db_time = max(db_durations)
                slow_db_ops = sum(1 for d in db_durations if d > self.slow_db_threshold)
            else:
                avg_db_time = max_db_time = slow_db_ops = 0
            
            # System metrics
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'requests': {
                    'total': len(self.request_times),
                    'avg_time': round(avg_request_time, 3),
                    'max_time': round(max_request_time, 3),
                    'slow_requests': slow_requests
                },
                'database': {
                    'total_queries': len(self.db_times),
                    'avg_time': round(avg_db_time, 3),
                    'max_time': round(max_db_time, 3),
                    'slow_operations': slow_db_ops,
                    'active_connections': self.active_connections
                },
                'system': {
                    'memory_percent': memory_percent,
                    'cpu_percent': cpu_percent,
                    'memory_warning': memory_percent > self.max_memory_percent
                },
                'errors': dict(self.error_counts),
                'timestamp': get_hk_now_iso()
            }
    
    def log_performance_summary(self):
        """Log a performance summary"""
        stats = self.get_performance_stats()
        
        logger.info("=== PERFORMANCE SUMMARY ===")
        logger.info(f"Requests: {stats['requests']['total']} total, "
                   f"{stats['requests']['avg_time']}s avg, "
                   f"{stats['requests']['slow_requests']} slow")
        logger.info(f"Database: {stats['database']['total_queries']} queries, "
                   f"{stats['database']['avg_time']}s avg, "
                   f"{stats['database']['slow_operations']} slow")
        logger.info(f"System: {stats['system']['memory_percent']}% memory, "
                   f"{stats['system']['cpu_percent']}% CPU")
        logger.info(f"Active DB connections: {stats['database']['active_connections']}")
        logger.info(f"Errors: {sum(stats['errors'].values())} total")
        logger.info("==========================")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorator for monitoring request performance
def monitor_request(endpoint=None):
    """Decorator to monitor request performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = performance_monitor.start_request_timer()
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_request_timer(start_time, endpoint)
                return result
            except Exception as e:
                performance_monitor.record_error('request_error', str(e))
                performance_monitor.end_request_timer(start_time, endpoint)
                raise
        return wrapper
    return decorator

# Context manager for database operation monitoring
class DatabaseMonitor:
    """Context manager for monitoring database operations"""
    
    def __init__(self, operation=None):
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = performance_monitor.start_db_timer()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            performance_monitor.record_error('database_error', str(exc_val))
        performance_monitor.end_db_timer(self.start_time, self.operation) 