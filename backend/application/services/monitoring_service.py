import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager

import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
class ClipsmithLogger:
    """Enhanced logging system for clipsmith with structured output."""
    
    def __init__(self, name: str = "clipsmith"):
        self.logger = structlog.get_logger(name)
        
        # Configure console and file handlers
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/clipsmith.log')
            ]
        )
        
        # Configure JSON logger for structured output
        self.json_logger = jsonlogger
        
        # Test logging
        self.logger.info(f"Logger initialized: {name}")
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception and context."""
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=error, extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        self.logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        self.logger.debug(message, extra=kwargs)
    
    def log_user_action(self, user_id: str, action: str, **kwargs):
        """Log user actions for audit trail."""
        self.info(
            f"User Action: {action}",
            user_id=user_id,
            action_type="user_action",
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_security_event(self, event_type: str, user_id: Optional[str] = None, **kwargs):
        """Log security events for monitoring."""
        self.warning(
            f"Security Event: {event_type}",
            user_id=user_id,
            event_type="security",
            timestamp=datetime.utcnow().isoformat(),
            severity=kwargs.get("severity", "medium"),
            **kwargs
        )
    
    def log_performance_metric(self, metric_name: str, value: float, **kwargs):
        """Log performance metrics."""
        self.info(
            f"Performance: {metric_name}={value}",
            metric_name=metric_name,
            value=value,
            metric_type="performance",
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_api_request(self, method: str, endpoint: str, user_id: Optional[str] = None, 
                    status_code: int, response_time: float, **kwargs):
        """Log API requests for monitoring and analytics."""
        self.info(
            f"API Request: {method} {endpoint} -> {status_code} ({response_time:.2f}s)",
            method=method,
            endpoint=endpoint,
            user_id=user_id,
            status_code=status_code,
            response_time=response_time,
            request_type="api_request",
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )

# Global logger instance
logger = ClipsmithLogger()

class MonitoringService:
    """Service for application monitoring and health checks."""
    
    def __init__(self):
        self.metrics = {
            'api_requests': [],
            'error_counts': {},
            'performance_metrics': [],
            'active_users': set(),
            'system_health': {}
        }
    
    def record_api_request(self, method: str, endpoint: str, user_id: Optional[str], 
                        status_code: int, response_time: float):
        """Record API request metrics."""
        logger.log_api_request(method, endpoint, user_id, status_code, response_time)
        
        self.metrics['api_requests'].append({
            'timestamp': datetime.utcnow(),
            'method': method,
            'endpoint': endpoint,
            'user_id': user_id,
            'status_code': status_code,
            'response_time': response_time
        })
        
        # Track error rates
        if status_code >= 400:
            error_key = f"{endpoint}_{method}"
            self.metrics['error_counts'][error_key] = self.metrics['error_counts'].get(error_key, 0) + 1
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Record application errors."""
        logger.error(f"Application Error: {error_type} - {error_message}", extra=context or {})
        
        self.metrics['error_counts'][error_type] = self.metrics['error_counts'].get(error_type, 0) + 1
    
    def record_user_activity(self, user_id: str, activity_type: str, **kwargs):
        """Record user activity for analytics."""
        logger.log_user_action(user_id, activity_type, **kwargs)
        self.metrics['active_users'].add(user_id)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        import psutil
        import os
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Check if key directories exist and are accessible
            upload_dir = os.path.exists('backend/uploads')
            db_accessible = os.path.exists('database.db')
            
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'healthy' if all([
                    cpu_percent < 90,  # CPU less than 90%
                    memory_percent < 90,  # Memory less than 90%
                    disk.percent < 90,  # Disk less than 90%
                    upload_dir,
                    db_accessible
                ]) else 'degraded',
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk.percent,
                    'uploads_accessible': upload_dir,
                    'database_accessible': db_accessible
                }
            }
            
            self.metrics['system_health'] = health_status
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        recent_requests = [
            req for req in self.metrics['api_requests'][-100:]  # Last 100 requests
        ]
        
        if recent_requests:
            avg_response_time = sum(req['response_time'] for req in recent_requests) / len(recent_requests)
            error_rate = sum(1 for req in recent_requests if req['status_code'] >= 400) / len(recent_requests)
        else:
            avg_response_time = 0
            error_rate = 0
        
        total_errors = sum(self.metrics['error_counts'].values())
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'active_users': len(self.metrics['active_users']),
            'recent_api_requests': len(recent_requests),
            'average_response_time': round(avg_response_time, 3),
            'error_rate': round(error_rate * 100, 2),
            'total_errors': total_errors,
            'top_errors': sorted(
                self.metrics['error_counts'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }

class ErrorReportingService:
    """Service for external error reporting (Sentry integration)."""
    
    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv('SENTRY_DSN')
        
        if self.dsn:
            try:
                import sentry_sdk
                self.sentry_client = sentry_sdk.init(
                    dsn=self.dsn,
                    traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
                    environment=os.getenv('ENVIRONMENT', 'development')
                )
                logger.info("Sentry error reporting initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
                self.sentry_client = None
        else:
            self.sentry_client = None
            logger.info("Sentry error reporting disabled")
    
    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture exception to external error reporting service."""
        if self.sentry_client:
            with self.sentry_client.push_scope() as scope:
                scope.set_tag("clipsmith", "production")
                scope.set_extra(context or {})
                self.sentry_client.capture_exception(exception)
        
        # Also log locally
        logger.error(f"Exception captured: {type(exception).__name__}: {str(exception)}", extra=context)
    
    def capture_message(self, message: str, level: str = "error", context: Optional[Dict[str, Any]] = None):
        """Capture message to external error reporting service."""
        if self.sentry_client:
            with self.sentry_client.push_scope() as scope:
                scope.set_tag("clipsmith", "production")
                scope.set_extra(context or {})
                
                if level == "error":
                    self.sentry_client.capture_message(message, level="error")
                elif level == "warning":
                    self.sentry_client.capture_message(message, level="warning")
                else:
                    self.sentry_client.capture_message(message, level="info")
        
        # Also log locally
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"Captured message: {message}", extra=context)

# Global services
monitoring_service = MonitoringService()
error_reporting = ErrorReportingService()