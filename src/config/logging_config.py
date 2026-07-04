import logging
import logging.config
import structlog
from pathlib import Path
from typing import Any, Dict
import sys

from .settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure application logging with structlog"""
    
    # Create log directory if it doesn't exist
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog processors
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create formatters
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    
    # Configure handlers
    handlers: Dict[str, Any] = {
        "console": {
            "level": settings.log_level,
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "stream": sys.stdout,
        }
    }
    
    if settings.log_file:
        handlers["file"] = {
            "level": settings.log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "structured",
            "filename": settings.log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
        }
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "handlers": ["console"] + (["file"] if settings.log_file else []),
                "level": settings.log_level,
                "propagate": False,
            },
            "src": {
                "handlers": ["console"] + (["file"] if settings.log_file else []),
                "level": settings.log_level,
                "propagate": False,
            },
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str):
    """Get a configured logger instance"""
    return structlog.get_logger(name)