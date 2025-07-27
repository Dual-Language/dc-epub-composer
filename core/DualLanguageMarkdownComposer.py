import os
import json
import pathlib
from typing import Dict, Any, Optional
from markdown import markdown
from ebooklib import epub
from bs4 import BeautifulSoup
import mimetypes

from core.IComposer import IComposer
from core.DualLanguageCombiner import DualLanguageCombiner
from common.logger import get_logger

class DualLanguageMarkdownComposer(IComposer):
    """
    Composer that combines original.md and translatedcontent.md into dual-language format
    before converting to EPUB.
    """
    
    def __init__(self, progress_filename: str = "composingservice-progress.json", 
                 translated_content_filename: str = "translatedcontent.md", 
                 final_epub_filename: str = "final.epub"):
        self.logger = get_logger()
        self.progress_filename = progress_filename
        self.translated_content_filename = translated_content_filename
        self.final_epub_filename = final_epub_filename
        self.combiner = DualLanguageCombiner(self.logger)
    
    def get_name(self) -> str:
        return "dual_language_markdown"
    
    def can_compose(self, book_id: str, storage_root: str) -> bool:
        """Check if both original.md and translatedcontent.md exist for this book."""
        book_dir = pathlib.Path(storage_root) / book_id
        original_path = book_dir / "original.md"
        translated_path = book_dir / self.translated_content_filename
        
        # Must have both files to create dual-language content
        return original_path.exists() and translated_path.exists()
    
    def compose(self, book_id: str, storage_root: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Combine original.md and translatedcontent.md into dual-language format,
        then convert to EPUB.
        """
        try:
            self.logger.info(f"Starting dual-language composition for book: {book_id}", book_id)
            
            book_dir = pathlib.Path(storage_root) / book_id
            original_path = book_dir / "original.md"
            translated_path = book_dir / self.translated_content_filename
            combined_path = book_dir / "combined-dual-language.md"
            output_epub_path = book_dir / self.final_epub_filename
            
            # Check if files exist
            if not original_path.exists():
                self.logger.error(f"Original content file not found: {original_path}", book_id)
                return False
            
            if not translated_path.exists():
                self.logger.error(f"Translated content file not found: {translated_path}", book_id)
                return False
            
            # Load progress
            progress = self.get_progress(book_id, storage_root)
            progress['status'] = 'processing'
            progress['started_at'] = self._get_timestamp()
            progress['step'] = 'combining_content'
            self.save_progress(book_id, storage_root, progress)
            
            # Combine original and translated content
            self.logger.info(f"Combining original and translated content for book: {book_id}", book_id)
            success = self.combiner.combine_files(original_path, translated_path, combined_path)
            
            if not success:
                self.logger.error(f"Failed to combine content for book: {book_id}", book_id)
                progress['status'] = 'error'
                progress['error'] = 'Failed to combine original and translated content'
                progress['error_at'] = self._get_timestamp()
                self.save_progress(book_id, storage_root, progress)
                return False
            
            # Update progress
            progress['step'] = 'converting_to_epub'
            self.save_progress(book_id, storage_root, progress)
            
            # Read combined markdown content
            with open(combined_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown(md_content, output_format='html')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create EPUB book
            book = epub.EpubBook()
            book.set_identifier(f'book_{book_id}')
            
            # Try to extract title from the content, fallback to book_id
            title = self._extract_title_from_content(soup) or f'Dual Language Book - {book_id}'
            book.set_title(title)
            book.set_language('en')  # Could be enhanced to support multiple languages
            book.add_author('Dual Language Translation Service')
            
            # Handle images
            image_tags = soup.find_all('img')
            for i, img_tag in enumerate(image_tags):
                img_src = img_tag.get('src')
                if not img_src:
                    continue
                
                img_path = book_dir / str(img_src)
                if not img_path.exists():
                    self.logger.warn(f"Image not found: {img_src}", book_id)
                    continue
                
                mime_type, _ = mimetypes.guess_type(str(img_path))
                mime_type = mime_type or 'image/jpeg'
                
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                
                img_name = pathlib.Path(str(img_src)).name
                epub_img = epub.EpubItem(
                    uid=f'img{i}',
                    file_name=f'images/{img_name}',
                    media_type=mime_type,
                    content=img_data
                )
                
                # Fix src in HTML
                if hasattr(img_tag, '__setitem__'):
                    img_tag['src'] = f'images/{img_name}'
                book.add_item(epub_img)
            
            # Create chapters from headings
            all_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            if not all_headers:
                # Fallback: one chapter with all content
                chapter = epub.EpubHtml(title='Dual Language Content', file_name='chap_01.xhtml', lang='en')
                chapter.content = str(soup)
                book.add_item(chapter)
                book.toc = (chapter,)
                book.spine = ['nav', chapter]
            else:
                chapters = []
                toc = []
                chapter_counter = 1
                
                current_chunk = []
                current_title = "Introduction"
                current_file_name = f"chap_{chapter_counter:02}.xhtml"
                
                body_children = list(soup.body.children) if soup.body else list(soup.children)
                
                for el in body_children:
                    if el.name and el.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                        # Save previous chapter if we have content
                        if current_chunk:
                            chapter_html = ''.join(str(x) for x in current_chunk)
                            chapter = epub.EpubHtml(title=current_title, file_name=current_file_name, lang='en')
                            chapter.content = chapter_html
                            book.add_item(chapter)
                            chapters.append(chapter)
                            toc.append(epub.Link(current_file_name, current_title, f'chap{chapter_counter}'))
                            chapter_counter += 1
                            current_file_name = f"chap_{chapter_counter:02}.xhtml"
                            current_chunk = []
                        
                        # Extract title (remove dual-language formatting if present)
                        full_title = el.get_text()
                        current_title = self._clean_chapter_title(full_title)
                    
                    current_chunk.append(el)
                
                # Add final chapter
                if current_chunk:
                    chapter_html = ''.join(str(x) for x in current_chunk)
                    chapter = epub.EpubHtml(title=current_title, file_name=current_file_name, lang='en')
                    chapter.content = chapter_html
                    book.add_item(chapter)
                    chapters.append(chapter)
                    toc.append(epub.Link(current_file_name, current_title, f'chap{chapter_counter}'))
                
                # Set table of contents and spine
                book.toc = tuple(toc)
                book.spine = ['nav'] + chapters
            
            # Add navigation
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Write EPUB
            self.logger.info(f"Writing EPUB file: {output_epub_path}", book_id)
            epub.write_epub(str(output_epub_path), book)
            
            # Update progress
            progress['status'] = 'free-completed' if self.final_epub_filename == 'free-final.epub' else 'completed'
            progress['completed_at'] = self._get_timestamp()
            progress['output_file'] = str(output_epub_path)
            progress['combined_file'] = str(combined_path)
            progress['step'] = 'completed'
            self.save_progress(book_id, storage_root, progress)
            
            self.logger.info(f"Successfully created dual-language EPUB: {output_epub_path}", book_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Error composing dual-language EPUB for {book_id}: {str(e)}", book_id, e)
            
            # Update progress with error
            progress = self.get_progress(book_id, storage_root)
            progress['status'] = 'error'
            progress['error'] = str(e)
            progress['error_at'] = self._get_timestamp()
            self.save_progress(book_id, storage_root, progress)
            
            return False
    
    def _extract_title_from_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from the first H1 tag in the content."""
        h1_tag = soup.find('h1')
        if h1_tag:
            title_text = h1_tag.get_text().strip()
            # If it's a dual-language title, take the first part
            if ' / ' in title_text:
                return title_text.split(' / ')[0].strip()
            return title_text
        return None
    
    def _clean_chapter_title(self, title: str) -> str:
        """Clean chapter title by taking the first part if it's dual-language format."""
        if ' / ' in title:
            return title.split(' / ')[0].strip()
        return title.strip()
    
    def get_progress(self, book_id: str, storage_root: str) -> Dict[str, Any]:
        """Get progress for the given book."""
        progress_path = pathlib.Path(storage_root) / book_id / self.progress_filename
        
        if progress_path.exists():
            try:
                with open(progress_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading progress for {book_id}: {str(e)}", book_id, e)
        
        # Return default progress
        return {
            'book_id': book_id,
            'composer': self.get_name(),
            'status': 'pending',
            'created_at': self._get_timestamp()
        }
    
    def save_progress(self, book_id: str, storage_root: str, progress: Dict[str, Any]) -> None:
        """Save progress for the given book."""
        try:
            book_dir = pathlib.Path(storage_root) / book_id
            book_dir.mkdir(parents=True, exist_ok=True)
            
            progress_path = book_dir / self.progress_filename
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved progress for {book_id}", book_id)
        except Exception as e:
            self.logger.error(f"Error saving progress for {book_id}: {str(e)}", book_id, e)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def set_filenames(self, filenames: Dict[str, Any]) -> None:
        """Set filenames or configuration for the composer."""
        if 'progress_filename' in filenames:
            self.progress_filename = filenames['progress_filename']
        if 'translated_content_filename' in filenames:
            self.translated_content_filename = filenames['translated_content_filename']
        if 'final_epub_filename' in filenames:
            self.final_epub_filename = filenames['final_epub_filename']
