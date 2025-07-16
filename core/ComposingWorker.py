import os
import pathlib
import time
from typing import List, Optional
from core.ComposerFactory import ComposerFactory
from core.IComposer import IComposer
from common.configuration import get_storage_root, get_composer_config
from common.logger import get_logger
from event_logger import write_service_event

class ComposingWorker:
    """Main worker that continuously scans for composition jobs."""
    
    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = storage_root or get_storage_root()
        self.config = get_composer_config()
        self.logger = get_logger(self.storage_root)
        self.composer_factory = ComposerFactory()
        
        self.logger.info(f"ComposingWorker initialized with storage root: {self.storage_root}")
        self.logger.info(f"Available composers: {self.composer_factory.get_available_composers()}")
    
    def find_jobs(self) -> List[str]:
        """Find books that need composition."""
        jobs = []
        try:
            storage_path = pathlib.Path(self.storage_root)
            if not storage_path.exists():
                self.logger.warn(f"Storage directory does not exist: {self.storage_root}")
                return jobs
            
            self.logger.info(f"Scanning for jobs in: {self.storage_root}")
            
            for item in storage_path.iterdir():
                if item.is_dir():
                    book_id = item.name
                    
                    # Check if this book needs composition
                    if self._needs_composition(book_id):
                        self.logger.info(f"Found composition job: {book_id}", book_id)
                        jobs.append(book_id)
        
        except Exception as e:
            self.logger.error(f"Error finding jobs: {str(e)}", error=e)
        
        return jobs
    
    def _needs_composition(self, book_id: str) -> bool:
        """Check if a book needs composition."""
        book_dir = pathlib.Path(self.storage_root) / book_id
        
        # Check if final.epub already exists
        final_epub_path = book_dir / self.config['final_epub_filename']
        if final_epub_path.exists():
            return False
        
        # Check if translatedcontent.md exists
        translated_content_path = book_dir / self.config['translated_content_filename']
        if not translated_content_path.exists():
            return False
        
        # Check progress to see if it's already been processed
        progress = self._load_progress(book_id)
        if progress.get('status') in ['completed', 'error']:
            return False
        
        # Find a suitable composer
        composer = self.composer_factory.find_suitable_composer(book_id, self.storage_root)
        return composer is not None
    
    def _load_progress(self, book_id: str) -> dict:
        """Load progress for a book."""
        progress_path = pathlib.Path(self.storage_root) / book_id / self.config['progress_filename']
        
        if progress_path.exists():
            try:
                import json
                with open(progress_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading progress for {book_id}: {str(e)}", book_id, error=e)
        
        return {'status': 'pending'}
    
    def process_book(self, book_id: str) -> bool:
        """Process a single book."""
        try:
            self.logger.info(f"Processing book: {book_id}", book_id)
            
            # Find suitable composer
            composer = self.composer_factory.find_suitable_composer(book_id, self.storage_root)
            if not composer:
                self.logger.error(f"No suitable composer found for {book_id}", book_id)
                return False
            
            # Perform composition
            success = composer.compose(book_id, self.storage_root)
            
            if success:
                self.logger.info(f"Successfully processed book: {book_id}", book_id)
            else:
                self.logger.error(f"Failed to process book: {book_id}", book_id)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing book {book_id}: {str(e)}", book_id, error=e)
            return False
    
    def run(self):
        """Main run loop."""
        self.logger.info("Starting ComposingWorker main loop...")
        
        while True:
            try:
                found_job = False
                jobs = self.find_jobs()
                
                for book_id in jobs:
                    found_job = True
                    # Log service-start event for this book/job
                    write_service_event("service-start", book_id, "composingservice", storage_root=self.storage_root)
                    try:
                        success = self.process_book(book_id)
                        if success:
                            write_service_event("service-stop", book_id, "composingservice", storage_root=self.storage_root, result="success")
                        else:
                            write_service_event("service-stop", book_id, "composingservice", storage_root=self.storage_root, result="error")
                    except Exception as e:
                        write_service_event("service-stop", book_id, "composingservice", storage_root=self.storage_root, result="error", error=str(e))
                        raise
                
                if not found_job:
                    self.logger.info("No jobs found. Sleeping...")
                
                # Sleep before next scan
                time.sleep(self.config['sleep_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal. Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {str(e)}", error=e)
                time.sleep(self.config['sleep_interval']) 