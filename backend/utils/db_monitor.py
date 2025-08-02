#!/usr/bin/env python3
"""
Database Connection Monitoring
Tracks connection pool usage and database performance
"""

import threading
import time
from datetime import datetime
from config import db_pool, return_db_conn
from utils.timezone_utils import get_hk_now_iso
from utils.performance_monitor import performance_monitor

class DatabaseMonitor:
    """Monitor database connection pool and performance"""
    
    def __init__(self):
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'connection_errors': 0,
            'slow_queries': 0
        }
        self.lock = threading.Lock()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("[DB Monitor] Started database connection monitoring")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[DB Monitor] Stopped database connection monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self.update_stats()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                print(f"[DB Monitor] Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def update_stats(self):
        """Update connection statistics"""
        try:
            if hasattr(db_pool, '_pool'):
                pool = db_pool._pool
                with self.lock:
                    self.connection_stats['total_connections'] = len(pool)
                    self.connection_stats['active_connections'] = len([c for c in pool if c.closed == 0])
                    self.connection_stats['idle_connections'] = len([c for c in pool if c.closed == 1])
                
                # Update performance monitor
                performance_monitor.update_connection_count(self.connection_stats['active_connections'])
                
        except Exception as e:
            print(f"[DB Monitor] Error updating stats: {e}")
    
    def get_connection(self):
        """Get a database connection with monitoring"""
        start_time = time.time()
        
        try:
            conn = db_pool.getconn()
            if conn:
                with self.lock:
                    self.connection_stats['total_connections'] += 1
                
                # Log slow connection acquisition
                duration = time.time() - start_time
                if duration > 1.0:  # > 1 second
                    print(f"[DB Monitor] Slow connection acquisition: {duration:.2f}s")
                    with self.lock:
                        self.connection_stats['slow_queries'] += 1
                
                return conn
            else:
                with self.lock:
                    self.connection_stats['connection_errors'] += 1
                return None
                
        except Exception as e:
            with self.lock:
                self.connection_stats['connection_errors'] += 1
            print(f"[DB Monitor] Connection error: {e}")
            return None
    
    def return_connection(self, conn):
        """Return a database connection with monitoring"""
        try:
            if conn:
                db_pool.putconn(conn)
        except Exception as e:
            print(f"[DB Monitor] Error returning connection: {e}")
    
    def get_stats(self):
        """Get current database statistics"""
        with self.lock:
            return {
                'connection_pool': dict(self.connection_stats),
                'timestamp': get_hk_now_iso()
            }
    
    def log_stats(self):
        """Log current database statistics"""
        stats = self.get_stats()
        print(f"[DB Monitor] Connection Pool Stats:")
        print(f"  Total Connections: {stats['connection_pool']['total_connections']}")
        print(f"  Active Connections: {stats['connection_pool']['active_connections']}")
        print(f"  Idle Connections: {stats['connection_pool']['idle_connections']}")
        print(f"  Connection Errors: {stats['connection_pool']['connection_errors']}")
        print(f"  Slow Queries: {stats['connection_pool']['slow_queries']}")

# Global database monitor instance
db_monitor = DatabaseMonitor()

# Enhanced database connection function with monitoring
def get_monitored_db_conn():
    """Get database connection with monitoring"""
    return db_monitor.get_connection()

def return_monitored_db_conn(conn):
    """Return database connection with monitoring"""
    db_monitor.return_connection(conn)

# Context manager for database operations with monitoring
class MonitoredDatabaseConnection:
    """Context manager for database operations with monitoring"""
    
    def __init__(self, operation_name=None):
        self.operation_name = operation_name
        self.conn = None
        self.start_time = None
    
    def __enter__(self):
        self.start_time = performance_monitor.start_db_timer()
        self.conn = get_monitored_db_conn()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            performance_monitor.record_error('database_error', str(exc_val))
        performance_monitor.end_db_timer(self.start_time, self.operation_name)
        return_monitored_db_conn(self.conn)

# Start monitoring when module is imported
db_monitor.start_monitoring() 