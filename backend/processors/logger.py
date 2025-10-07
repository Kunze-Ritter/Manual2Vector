"""
Beautiful logging setup for processor V2

Uses rich for colored, formatted console output.
"""

import logging
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  'rich' not installed. Install with: pip install rich")
    print("   Falling back to basic logging")


class ProcessorLogger:
    """Enhanced logger with rich formatting"""
    
    def __init__(self, name: str = "processor_v2", log_file: Optional[Path] = None):
        self.name = name
        self.log_file = log_file
        self.logger = self._setup_logger()
        
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with rich handler"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers.clear()
        
        if RICH_AVAILABLE:
            # Rich console handler
            console_handler = RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=False,
            )
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
        else:
            # Fallback to basic handler with UTF-8 encoding
            # Force UTF-8 encoding for Windows compatibility with Unicode characters
            try:
                # Try to wrap stdout.buffer if available
                utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                console_handler = logging.StreamHandler(utf8_stdout)
            except AttributeError:
                # stdout.buffer not available (already wrapped), use stdout directly
                console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler (always basic format with UTF-8 encoding)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def success(self, message: str):
        """Log success message"""
        if RICH_AVAILABLE:
            # Remove emoji for Windows compatibility
            self.logger.info(f"[green]{message}[/green]")
        else:
            self.logger.info(f"[OK] {message}")
    
    def warning(self, message: str):
        """Log warning message"""
        if RICH_AVAILABLE:
            self.logger.warning(f"[yellow]{message}[/yellow]")
        else:
            self.logger.warning(f"[WARN] {message}")
    
    def error(self, message: str, exc: Optional[Exception] = None):
        """Log error message"""
        if RICH_AVAILABLE:
            self.logger.error(f"[red]{message}[/red]")
        else:
            self.logger.error(f"[ERROR] {message}")
        
        if exc:
            self.logger.exception(exc)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def section(self, title: str):
        """Print section header"""
        if RICH_AVAILABLE and self.console:
            self.console.rule(f"[bold blue]{title}[/bold blue]")
        else:
            print(f"\n{'='*60}")
            print(f"{title}")
            print(f"{'='*60}")
    
    def panel(self, content: str, title: str = "", style: str = "blue"):
        """Print content in a panel"""
        if RICH_AVAILABLE and self.console:
            self.console.print(Panel(content, title=title, style=style))
        else:
            print(f"\n{title}")
            print(content)
            print()
    
    def table(self, data: dict, title: str = ""):
        """Print data as table"""
        if RICH_AVAILABLE and self.console:
            table = Table(title=title, show_header=True)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.items():
                table.add_row(str(key), str(value))
            
            self.console.print(table)
        else:
            if title:
                print(f"\n{title}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    def progress_bar(self, items: list, description: str = "Processing"):
        """Return progress bar context manager"""
        if RICH_AVAILABLE:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            )
        else:
            # Fallback: simple counter
            class SimpleProgress:
                def __enter__(self):
                    return self
                
                def __exit__(self, *args):
                    pass
                
                def add_task(self, description, total):
                    self.total = total
                    self.current = 0
                    self.description = description
                    return 0
                
                def update(self, task_id, advance=1):
                    self.current += advance
                    print(f"{self.description}: {self.current}/{self.total}", end='\r')
                    if self.current >= self.total:
                        print()
            
            return SimpleProgress()


# Global logger instance
_logger_instance: Optional[ProcessorLogger] = None


def get_logger(
    name: str = "processor_v2",
    log_file: Optional[Path] = None
) -> ProcessorLogger:
    """
    Get or create logger instance
    
    Args:
        name: Logger name
        log_file: Optional file to log to
        
    Returns:
        ProcessorLogger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        if log_file is None:
            # Default log file location
            log_dir = Path(__file__).parent.parent / "logs"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"processor_v2_{timestamp}.log"
        
        _logger_instance = ProcessorLogger(name, log_file)
    
    return _logger_instance


def log_processing_summary(
    logger: ProcessorLogger,
    stats: dict,
    duration_seconds: float
):
    """
    Log pretty processing summary
    
    Args:
        logger: Logger instance
        stats: Dictionary with processing statistics
        duration_seconds: Total processing time
    """
    logger.section("Processing Summary")
    
    summary = {
        "Duration": f"{duration_seconds:.2f}s",
        "Documents Processed": stats.get('documents_processed', 0),
        "Chunks Created": stats.get('chunks_created', 0),
        "Embeddings Generated": stats.get('embeddings_created', 0),
        "Products Extracted": stats.get('products_extracted', 0),
        "Error Codes Found": stats.get('error_codes_extracted', 0),
        "Validation Failures": stats.get('validation_failures', 0),
        "Average Confidence": f"{stats.get('avg_confidence', 0):.2f}",
    }
    
    logger.table(summary, title="📊 Statistics")
    
    # Success/warning/error summary
    if stats.get('validation_failures', 0) > 0:
        logger.warning(
            f"Had {stats['validation_failures']} validation failures - check logs!"
        )
    
    if stats.get('avg_confidence', 1.0) < 0.7:
        logger.warning(
            f"Average confidence is low ({stats['avg_confidence']:.2f}) - "
            "extracted data may be unreliable"
        )
    
    logger.success(f"Processing completed in {duration_seconds:.2f}s")


# Example usage
if __name__ == "__main__":
    # Test logger
    logger = get_logger()
    
    logger.section("Testing Logger")
    logger.info("This is an info message")
    logger.success("This is a success message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message (won't show unless DEBUG level)")
    
    logger.panel("This is panel content", title="Test Panel", style="green")
    
    test_data = {
        "chunks_created": 150,
        "embeddings": 145,
        "confidence": 0.85
    }
    logger.table(test_data, title="Test Table")
    
    print("\n✅ Logger test complete!")
