import logging
import sys
from typing import Optional

def setup_logger(name: str = "app", level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up a logger with console and optional file handlers.
    
    Args:
        name: The name of the logger.
        level: Logging level (default: logging.INFO).
        log_file: Path to a log file (optional).
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if the logger is already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Create a default logger instance for general use
logger = setup_logger()
