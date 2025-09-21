"""
Centralized logging configuration module for Century Property Tax application.

This module provides a unified logging configuration system that:
- Configures both standard logging and structlog
- Supports environment variable configuration
- Provides consistent logger factory with component binding
- Handles graceful fallbacks for all configuration options
- Integrates with existing WhatsApp client logging patterns
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


def get_log_directory() -> str:
    """
    Get the log directory from environment variable or use fallback.

    Returns:
        str: Absolute path to the log directory
    """
    log_dir = os.getenv('LOG_DIR')
    if log_dir:
        try:
            path = Path(log_dir)
            path.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = path / '.write_test'
            test_file.touch()
            test_file.unlink()
            return str(path.absolute())
        except (OSError, PermissionError):
            # Fall back to temp directory if custom LOG_DIR fails
            pass

    # Default fallback: logs subdirectory in current directory
    try:
        default_log_dir = Path.cwd() / 'logs'
        default_log_dir.mkdir(parents=True, exist_ok=True)
        # Test write permissions
        test_file = default_log_dir / '.write_test'
        test_file.touch()
        test_file.unlink()
        return str(default_log_dir.absolute())
    except (OSError, PermissionError):
        # Ultimate fallback: system temp directory
        return tempfile.gettempdir()


def get_log_level() -> int:
    """
    Get the log level from environment variable or use fallback.

    Returns:
        int: Logging level constant
    """
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()

    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,  # Alternative form
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    return level_mapping.get(log_level_str, logging.INFO)


def is_file_logging_enabled() -> bool:
    """
    Check if file logging is enabled via environment variable.

    Returns:
        bool: True if file logging should be enabled
    """
    file_enabled = os.getenv('LOG_FILE_ENABLED', 'true').lower()
    return file_enabled in ('true', '1', 'yes', 'on', 'enabled')


def configure_logging() -> None:
    """
    Configure the logging system with environment variable support.

    This function:
    - Sets up both standard logging and structlog
    - Configures file and console handlers based on environment variables
    - Provides graceful fallbacks for all configuration options
    - Maintains compatibility with existing structlog patterns

    Environment Variables:
        LOG_LEVEL: DEBUG/INFO/WARNING/ERROR (default: INFO)
        LOG_DIR: Custom log directory (default: ./logs or temp)
        LOG_FILE_ENABLED: true/false (default: true)
    """
    # Get configuration from environment variables
    log_level = get_log_level()
    log_dir = get_log_directory()
    file_enabled = is_file_logging_enabled()

    # Prepare handlers
    handlers = []

    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # Add file handler if enabled
    if file_enabled:
        try:
            log_file_path = Path(log_dir) / 'app.log'
            file_handler = logging.FileHandler(str(log_file_path))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(log_level)
            handlers.append(file_handler)
        except (OSError, PermissionError) as e:
            # If file logging fails, log warning to console and continue
            console_handler.handle(
                logging.LogRecord(
                    name='logging_config',
                    level=logging.WARNING,
                    pathname='',
                    lineno=0,
                    msg=f'Failed to configure file logging: {e}. Continuing with console only.',
                    args=(),
                    exc_info=None
                )
            )

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )

    # Configure structlog to work with standard logging
    # This maintains compatibility with existing patterns
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Log configuration completion
    root_logger = logging.getLogger('logging_config')
    root_logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log directory: {log_dir}")
    root_logger.info(f"File logging: {'enabled' if file_enabled else 'disabled'}")


def get_logger(component: str) -> structlog.stdlib.BoundLogger:
    """
    Factory function to get a logger with component binding.

    This function provides consistent logger creation with component binding
    that maintains compatibility with existing WhatsApp client patterns.

    Args:
        component: The component name for logger binding (e.g., 'whatsapp_client')

    Returns:
        structlog.stdlib.BoundLogger: Logger instance bound to the component

    Example:
        >>> logger = get_logger('whatsapp_client')
        >>> logger.info("Message sent successfully", recipient="+1234567890")
    """
    # Get structlog logger and bind component
    logger = structlog.get_logger()
    return logger.bind(component=component)


def get_standard_logger(name: str) -> logging.Logger:
    """
    Get a standard Python logger instance.

    This function provides access to standard Python loggers for cases where
    structlog is not needed or desired.

    Args:
        name: The logger name (typically __name__)

    Returns:
        logging.Logger: Standard Python logger instance

    Example:
        >>> logger = get_standard_logger(__name__)
        >>> logger.info("Application started")
    """
    return logging.getLogger(name)


# Global flag to track if logging has been configured
_logging_configured = False


def ensure_logging_configured() -> None:
    """
    Ensure logging is configured exactly once.

    This function provides a safe way to ensure logging configuration
    happens exactly once, even if called multiple times.
    """
    global _logging_configured
    if not _logging_configured:
        configure_logging()
        _logging_configured = True