"""
Colored Logging - Farbige Terminal-Ausgaben
Rot = ERROR, Gelb = WARNING, Grün = INFO/SUCCESS
"""

import logging
import sys

# ANSI Color Codes
class Colors:
    """ANSI Color codes for terminal output"""
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Backgrounds
    BG_RED = '\033[101m'
    BG_YELLOW = '\033[103m'
    BG_GREEN = '\033[102m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    
    # Format strings
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Level colors
    COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BG_RED + Colors.WHITE + Colors.BOLD
    }
    
    def format(self, record):
        # Get color for log level
        log_color = self.COLORS.get(record.levelno, Colors.WHITE)
        
        # Format the levelname with color
        levelname = record.levelname
        colored_levelname = f"{log_color}{levelname}{Colors.RESET}"
        
        # Replace levelname temporarily
        original_levelname = record.levelname
        record.levelname = colored_levelname
        
        # Format message
        result = super().format(record)
        
        # Restore original
        record.levelname = original_levelname
        
        return result

def setup_colored_logging(logger_name=None, level=logging.INFO):
    """
    Setup colored logging for a logger
    
    Args:
        logger_name: Name of logger (None = root logger)
        level: Logging level (default: INFO)
    
    Returns:
        Logger instance with colored output
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Set colored formatter
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

def apply_colored_logging_globally(level=logging.INFO):
    """
    Apply colored logging to ALL loggers
    
    Args:
        level: Logging level (default: INFO)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove all existing handlers
    root_logger.handlers = []
    
    # Add colored console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    
    root_logger.addHandler(console_handler)
    
    return root_logger

# Convenience functions
def success(message, logger_name=None):
    """Log success message in GREEN"""
    logger = logging.getLogger(logger_name)
    logger.info(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def error(message, logger_name=None):
    """Log error message in RED"""
    logger = logging.getLogger(logger_name)
    logger.error(f"{Colors.RED}❌ {message}{Colors.RESET}")

def warning(message, logger_name=None):
    """Log warning message in YELLOW"""
    logger = logging.getLogger(logger_name)
    logger.warning(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def info(message, logger_name=None):
    """Log info message in CYAN"""
    logger = logging.getLogger(logger_name)
    logger.info(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")
