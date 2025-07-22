"""
Logging configuration for RS Personal Agent.

This module configures structured logging using structlog with support for
console, file, and database logging based on environment variables.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory


def configure_logging(
    level: Optional[str] = None,
    log_to_console: Optional[bool] = None,
    log_to_file: Optional[bool] = None,
    log_to_database: Optional[bool] = None,
    log_file_path: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        log_to_database: Whether to log to database
        log_file_path: Path to log file
    """
    # Get configuration from environment variables with defaults
    log_level = level or os.getenv("RSPA_LOGGING_LEVEL", "INFO").upper()
    console_logging = (
        log_to_console
        if log_to_console is not None
        else _env_bool("RSPA_LOGGING_LOG_TO_CONSOLE", True)
    )
    file_logging = (
        log_to_file
        if log_to_file is not None
        else _env_bool("RSPA_LOGGING_LOG_TO_FILE", True)
    )
    # Database logging configuration available but not currently used
    # database_logging = (
    #     log_to_database
    #     if log_to_database is not None
    #     else _env_bool("RSPA_LOGGING_LOG_TO_DATABASE", False)
    # )

    # Prepare processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure console output
    if console_logging:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure file output
    if file_logging:
        log_file = log_file_path or _get_default_log_file()
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Add file processor (JSON format for file logging)
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,  # type: ignore
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log level for root logger
    import logging

    logging.basicConfig(
        level=getattr(logging, log_level),
        stream=sys.stdout if console_logging else None,
        filename=log_file if file_logging else None,
        format="%(message)s",
    )


def _env_bool(key: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_default_log_file() -> str:
    """Get default log file path."""
    app_dir = Path.home() / ".rs_personal_agent"
    app_dir.mkdir(exist_ok=True)
    return str(app_dir / "rs_personal_agent.log")


# Configure logging when module is imported
configure_logging()
