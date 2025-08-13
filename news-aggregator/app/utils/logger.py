"""
Structured logging configuration for the application.
"""
import sys
import structlog
from typing import Any, Dict

def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.make_filtering_bound_logger(30),  # INFO level
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)

def log_api_request(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
    """Log API request details."""
    return {
        "event": "api_request",
        "method": method,
        "path": path,
        **kwargs
    }

def log_api_response(status_code: int, processing_time_ms: float, **kwargs: Any) -> Dict[str, Any]:
    """Log API response details."""
    return {
        "event": "api_response",
        "status_code": status_code,
        "processing_time_ms": processing_time_ms,
        **kwargs
    }

def log_external_api_call(service: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
    """Log external API call details."""
    return {
        "event": "external_api_call",
        "service": service,
        "endpoint": endpoint,
        **kwargs
    }