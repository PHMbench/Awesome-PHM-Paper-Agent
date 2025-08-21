"""
Logging configuration for APPA system.

This module sets up structured logging with appropriate formatters and handlers.
"""

import os
import logging
import logging.handlers
from typing import Dict, Any
import colorlog


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging configuration based on config settings.
    
    Args:
        config: Configuration dictionary containing logging settings
    """
    # Get logging configuration
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO').upper()
    log_file = log_config.get('file', 'logs/appa.log')
    max_file_size = log_config.get('max_file_size', 10) * 1024 * 1024  # Convert MB to bytes
    backup_count = log_config.get('backup_count', 5)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class to add logging capability to other classes.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(self.__class__.__name__)


if __name__ == "__main__":
    # Test logging setup
    test_config = {
        'logging': {
            'level': 'DEBUG',
            'file': 'logs/test.log',
            'max_file_size': 1,
            'backup_count': 3
        }
    }
    
    setup_logging(test_config)
    
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
