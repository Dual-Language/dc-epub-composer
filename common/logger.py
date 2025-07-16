import logging
import os
import pathlib
from datetime import datetime
from typing import Optional

class ComposingServiceLogger:
    def __init__(self, storage_root: str, service_name: str = "ComposingService"):
        self.storage_root = storage_root
        self.service_name = service_name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers."""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler for service logs
        service_log_path = pathlib.Path(self.storage_root) / f"{self.service_name.lower()}.log"
        file_handler = logging.FileHandler(service_log_path)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _write_book_log(self, book_id: str, message: str, level: str = "INFO"):
        """Write to book-specific log file."""
        try:
            book_log_dir = pathlib.Path(self.storage_root) / book_id
            book_log_dir.mkdir(parents=True, exist_ok=True)
            book_log_path = book_log_dir / f"{self.service_name.lower()}-book.log"
            
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {level} [{self.service_name}] [{book_id}] {message}\n"
            
            with open(book_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.logger.error(f"Failed to write book log: {e}")
    
    def info(self, message: str, book_id: Optional[str] = None):
        """Log info message."""
        self.logger.info(message)
        if book_id:
            self._write_book_log(book_id, message, "INFO")
    
    def error(self, message: str, book_id: Optional[str] = None, error: Optional[Exception] = None):
        """Log error message."""
        if error:
            message = f"{message}: {str(error)}"
        self.logger.error(message)
        if book_id:
            self._write_book_log(book_id, message, "ERROR")
    
    def warn(self, message: str, book_id: Optional[str] = None):
        """Log warning message."""
        self.logger.warning(message)
        if book_id:
            self._write_book_log(book_id, message, "WARN")
    
    def debug(self, message: str, book_id: Optional[str] = None):
        """Log debug message."""
        self.logger.debug(message)
        if book_id:
            self._write_book_log(book_id, message, "DEBUG")

# Global logger instance
_global_logger: Optional[ComposingServiceLogger] = None

def get_logger(storage_root: Optional[str] = None) -> ComposingServiceLogger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        if storage_root is None:
            from common.configuration import get_storage_root
            storage_root = get_storage_root()
        _global_logger = ComposingServiceLogger(storage_root)
    return _global_logger 