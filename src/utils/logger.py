"""
Logging configuration and utilities
"""

import logging
import logging.handlers
import os
from pathlib import Path

from src.core.config import settings

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "vibe_investor.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate file for errors
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Trading-specific log
    trading_handler = logging.handlers.RotatingFileHandler(
        log_dir / "trading.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    trading_formatter = logging.Formatter(
        '%(asctime)s - TRADING - %(levelname)s - %(message)s'
    )
    trading_handler.setFormatter(trading_formatter)
    
    # Add trading handler to specific loggers
    trading_logger = logging.getLogger("trading")
    trading_logger.addHandler(trading_handler)
    trading_logger.setLevel(logging.INFO)
    
    # Claude decisions log
    claude_handler = logging.handlers.RotatingFileHandler(
        log_dir / "claude_decisions.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )
    claude_formatter = logging.Formatter(
        '%(asctime)s - CLAUDE - %(levelname)s - %(message)s'
    )
    claude_handler.setFormatter(claude_formatter)
    
    claude_logger = logging.getLogger("claude")
    claude_logger.addHandler(claude_handler)
    claude_logger.setLevel(logging.INFO)
    
    # Suppress some noisy loggers
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    root_logger.info("🎯 Logging configured successfully") 