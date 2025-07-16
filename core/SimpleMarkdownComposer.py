import os
import json
import pathlib
from typing import Dict, Any, Optional
from markdown import markdown
from ebooklib import epub
from bs4 import BeautifulSoup
import mimetypes

from core.IComposer import IComposer
from common.logger import get_logger

class SimpleMarkdownComposer(IComposer):
    """Simple composer that converts translatedcontent.md to final.epub."""
    
    def __init__(self):
        self.logger = get_logger()
        self.progress_filename = "composingservice-progress.json"
        self.translated_content_filename = "translatedcontent.md"
        self.final_epub_filename = "final.epub"
    
    def get_name(self) -> str:
        return "simple_markdown"
    
    def can_compose(self, book_id: str, storage_root: str) -> bool:
        """Check if translatedcontent.md exists for this book."""
        book_dir = pathlib.Path(storage_root) / book_id
        translated_content_path = book_dir / self.translated_content_filename
        return translated_content_path.exists()
    
    def compose(self, book_id: str, storage_root: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Convert translatedcontent.md to final.epub."""
        try:
            self.logger.info(f"Starting composition for book: {book_id}", book_id)
            
            book_dir = pathlib.Path(storage_root) / book_id
            translated_content_path = book_dir / self.translated_content_filename
            output_epub_path = book_dir / self.final_epub_filename
            
            if not translated_content_path.exists():
                self.logger.error(f"Translated content file not found: {translated_content_path}", book_id)
                return False
            
            # Load progress
            progress = self.get_progress(book_id, storage_root)
            progress['status'] = 'processing'
            progress['started_at'] = self._get_timestamp()
            self.save_progress(book_id, storage_root, progress)
            
            # Read markdown content
            with open(translated_content_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown(md_content, output_format='html')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create EPUB book
            book = epub.EpubBook()
            book.set_identifier(f'book_{book_id}')
            book.set_title(f'Translated Book - {book_id}')
            book.set_language('en')
            book.add_author('Translation Service')
            
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
            all_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            if not all_tags:
                # Fallback: one chapter
                chapter = epub.EpubHtml(title='Chapter 1', file_name='chap_01.xhtml', lang='en')
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
                        
                        current_title = el.get_text()
                    current_chunk.append(el)
                
                # Final chunk
                if current_chunk:
                    chapter_html = ''.join(str(x) for x in current_chunk)
                    chapter = epub.EpubHtml(title=current_title, file_name=current_file_name, lang='en')
                    chapter.content = chapter_html
                    book.add_item(chapter)
                    chapters.append(chapter)
                    toc.append(epub.Link(current_file_name, current_title, f'chap{chapter_counter}'))
                
                # TOC & spine
                book.toc = tuple(toc)
                book.spine = ['nav'] + chapters
            
            # Navigation
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Write EPUB
            epub.write_epub(str(output_epub_path), book)
            
            # Update progress
            progress['status'] = 'completed'
            progress['completed_at'] = self._get_timestamp()
            progress['output_file'] = str(output_epub_path)
            self.save_progress(book_id, storage_root, progress)
            
            self.logger.info(f"Successfully created EPUB: {output_epub_path}", book_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Error composing EPUB for {book_id}: {str(e)}", book_id, e)
            
            # Update progress with error
            progress = self.get_progress(book_id, storage_root)
            progress['status'] = 'error'
            progress['error'] = str(e)
            progress['error_at'] = self._get_timestamp()
            self.save_progress(book_id, storage_root, progress)
            
            return False
    
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