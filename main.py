#!/usr/bin/env python3
"""
Composing Service (Console Version)
Main entry point for the composing service.
"""

import sys
import os
from pathlib import Path

# Add the composingservice directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.ComposingWorker import ComposingWorker
from common.configuration import get_storage_root
from common.logger import get_logger

def main():
    """Main entry point."""
    storage_root = get_storage_root()
    logger = get_logger(storage_root)
    
    logger.info(f"Starting Composing Service with storage root: {storage_root}")
    
    try:
        worker = ComposingWorker(storage_root)
        worker.run()
    except KeyboardInterrupt:
        logger.info("Composing Service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in Composing Service: {str(e)}", error=e)
        sys.exit(1)

if __name__ == "__main__":
    main() 