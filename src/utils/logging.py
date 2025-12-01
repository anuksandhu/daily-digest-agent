"""
Logging and Observability Setup for Daily Digest
Implements the three pillars: Logging, Tracing, Metrics
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log messages
    with consistent formatting for production observability
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data"""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra context if provided
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Format as readable string
        parts = [f"{log_data['timestamp']} - {log_data['level']} - {log_data['logger']}"]
        parts.append(f"- {log_data['message']}")
        
        if "context" in log_data:
            context_str = ", ".join(f"{k}={v}" for k, v in log_data["context"].items())
            parts.append(f"[{context_str}]")
        
        if "exception" in log_data:
            parts.append(f"\n{log_data['exception']}")
        
        return " ".join(parts)


def setup_logging(log_level: str = "INFO", log_dir: Path = None) -> logging.Logger:
    """
    Setup logging configuration with file and console handlers
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (creates if doesn't exist)
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if provided
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("daily-digest")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler (for stdout/stderr)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler (for persistent logs)
    log_file = log_dir / f"digest-{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def setup_tracing(enable: bool = True) -> trace.Tracer:
    """
    Setup OpenTelemetry tracing for agent execution
    
    Args:
        enable: Whether to enable tracing
    
    Returns:
        Configured tracer instance
    """
    
    if not enable:
        # Return a no-op tracer
        return trace.get_tracer(__name__)
    
    # Setup tracer provider
    provider = TracerProvider()
    
    # Add console exporter for local debugging
    # In production, this would be replaced with Cloud Trace exporter
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Create and return tracer
    tracer = trace.get_tracer("daily-digest")
    
    return tracer


class Logger:
    """
    Enhanced logger with context management and structured logging
    """
    
    def __init__(self, name: str = "daily-digest"):
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set persistent context for all log messages"""
        self._context.update(kwargs)
    
    def clear_context(self):
        """Clear persistent context"""
        self._context = {}
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with context"""
        extra = {"context": {**self._context, **kwargs}}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error message with optional exception"""
        if exception:
            kwargs["error_type"] = type(exception).__name__
            kwargs["error_message"] = str(exception)
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Exception = None, **kwargs):
        """Log critical message with optional exception"""
        if exception:
            kwargs["error_type"] = type(exception).__name__
            kwargs["error_message"] = str(exception)
        self._log(logging.CRITICAL, message, **kwargs)


# Global logger instance
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger
