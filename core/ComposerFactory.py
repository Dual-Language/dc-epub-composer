from typing import Any, Dict, Type, Optional
from core.IComposer import IComposer
from core.SimpleMarkdownComposer import SimpleMarkdownComposer
from core.ParagraphByParagraphComposer import ParagraphByParagraphComposer
from common.logger import get_logger

class ComposerFactory:
    """Factory for creating composer instances."""
    
    def __init__(self):
        self.logger = get_logger()
        self._composers: Dict[str, Type[IComposer]] = {}
        self._register_default_composers()
    
    def _register_default_composers(self):
        """Register the default composers."""
        self.register_composer('simple_markdown', SimpleMarkdownComposer)
        self.register_composer('paragraph_by_paragraph', ParagraphByParagraphComposer)
    
    def register_composer(self, name: str, composer_class: Type[IComposer]):
        """Register a composer class with a name."""
        self._composers[name] = composer_class
        self.logger.info(f"Registered composer: {name}")
    
    def get_composer(self, name: str) -> Optional[IComposer]:
        """Get a composer instance by name."""
        composer_class = self._composers.get(name)
        if composer_class:
            return composer_class()
        else:
            self.logger.error(f"Composer not found: {name}")
            return None
    
    def get_available_composers(self) -> list[str]:
        """Get list of available composer names."""
        return list(self._composers.keys())
    
    def find_suitable_composer(self, book_id: str, storage_root: str, filenames: Optional[Dict[str, Any]] = None) -> Optional[IComposer]:
        """Find the first composer that can handle the given book."""
        for name, composer_class in self._composers.items():
            composer = composer_class()
            if filenames is not None:
                composer.set_filenames(filenames)
            if composer.can_compose(book_id, storage_root):
                self.logger.info(f"Found suitable composer '{name}' for book {book_id}", book_id)
                return composer
        
        self.logger.warn(f"No suitable composer found for book {book_id}", book_id)
        return None 