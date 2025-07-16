from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IComposer(ABC):
    """Interface for all composer implementations."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name/identifier of this composer."""
        pass
    
    @abstractmethod
    def can_compose(self, book_id: str, storage_root: str) -> bool:
        """Check if this composer can handle the given book."""
        pass
    
    @abstractmethod
    def compose(self, book_id: str, storage_root: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Compose the EPUB file for the given book.
        
        Args:
            book_id: The book identifier
            storage_root: The storage root directory
            config: Optional configuration for the composer
            
        Returns:
            True if composition was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_progress(self, book_id: str, storage_root: str) -> Dict[str, Any]:
        """Get the current progress for the given book."""
        pass
    
    @abstractmethod
    def save_progress(self, book_id: str, storage_root: str, progress: Dict[str, Any]) -> None:
        """Save progress for the given book."""
        pass 