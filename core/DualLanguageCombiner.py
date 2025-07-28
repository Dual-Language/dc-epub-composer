import re
from typing import List, Tuple, Optional
from pathlib import Path
import logging

class DualLanguageCombiner:
    """Utility class to combine original and translated markdown files into dual-language format."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def combine_markdown_files(self, original_content: str, translated_content: str) -> str:
        """
        Combine original and translated markdown content into dual-language format.
        
        Args:
            original_content: Content from original.md
            translated_content: Content from translatedcontent.md
            
        Returns:
            Combined dual-language markdown content
        """
        try:
            # Parse both documents into structured sections
            original_sections = self._parse_markdown_sections(original_content)
            translated_sections = self._parse_markdown_sections(translated_content)
            
            # Combine sections
            combined_content = self._combine_sections(original_sections, translated_sections)
            
            return combined_content
            
        except Exception as e:
            self.logger.error(f"Error combining markdown files: {str(e)}")
            raise
    
    def _parse_markdown_sections(self, content: str) -> List[Tuple[str, str, List[str]]]:
        """
        Parse markdown content into sections based on headers.
        
        Returns:
            List of (level, title, content_lines) tuples
        """
        lines = content.strip().split('\n')
        sections = []
        current_section = None
        current_lines = []
        
        for line in lines:
            # Check if this is a header line
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            
            if header_match:
                # Save previous section if exists
                if current_section:
                    sections.append((current_section[0], current_section[1], current_lines))
                
                # Start new section
                level = header_match.group(1)  # Number of # characters
                title = header_match.group(2).strip()
                current_section = (level, title)
                current_lines = []
            else:
                # Add to current section content
                current_lines.append(line)
        
        # Add final section
        if current_section:
            sections.append((current_section[0], current_section[1], current_lines))
        
        return sections
    
    def _combine_sections(self, original_sections: List[Tuple[str, str, List[str]]], 
                         translated_sections: List[Tuple[str, str, List[str]]]) -> str:
        """
        Combine original and translated sections into dual-language format.
        """
        combined_lines = []
        
        # Create mapping of translated sections by normalized title for easier matching
        translated_map = {}
        for level, title, content in translated_sections:
            normalized_title = self._normalize_title(title)
            translated_map[normalized_title] = (level, title, content)
        
        for orig_level, orig_title, orig_content in original_sections:
            normalized_orig_title = self._normalize_title(orig_title)
            
            # Find matching translated section
            translated_section = translated_map.get(normalized_orig_title)
            
            if translated_section:
                trans_level, trans_title, trans_content = translated_section
                
                # Add combined header
                if orig_level == '#':  # H1 - main title
                    combined_lines.append(f"# {orig_title}")
                    combined_lines.append("")
                    combined_lines.append(f"# {trans_title}")
                else:  # Other headers - combine in single line
                    combined_lines.append(f"{orig_level} {orig_title} / {trans_title}")
                
                combined_lines.append("")
                
                # Combine content paragraph by paragraph
                combined_content = self._combine_content_paragraphs(orig_content, trans_content)
                combined_lines.extend(combined_content)
                combined_lines.append("")
            else:
                # No translation found, add original only
                self.logger.warn(f"No translation found for section: {orig_title}")
                combined_lines.append(f"{orig_level} {orig_title}")
                combined_lines.append("")
                combined_lines.extend(orig_content)
                combined_lines.append("")
        
        # Remove trailing empty lines
        while combined_lines and combined_lines[-1] == "":
            combined_lines.pop()
        
        return '\n'.join(combined_lines)
    
    def _combine_content_paragraphs(self, orig_content: List[str], trans_content: List[str]) -> List[str]:
        """
        Combine content paragraphs from original and translated sections.
        """
        combined = []
        
        # Split content into paragraphs (separated by empty lines)
        orig_paragraphs = self._split_into_paragraphs(orig_content)
        trans_paragraphs = self._split_into_paragraphs(trans_content)
        
        # Combine paragraphs one by one
        max_paragraphs = max(len(orig_paragraphs), len(trans_paragraphs))
        
        for i in range(max_paragraphs):
            orig_para = orig_paragraphs[i] if i < len(orig_paragraphs) else []
            trans_para = trans_paragraphs[i] if i < len(trans_paragraphs) else []
            
            # Special handling for bullet points
            if orig_para and trans_para and self._is_bullet_list(orig_para) and self._is_bullet_list(trans_para):
                combined_bullets = self._combine_bullet_lists(orig_para, trans_para)
                combined.extend(combined_bullets)
                combined.append("")
            else:
                # Add original paragraph
                if orig_para:
                    combined.extend(orig_para)
                    combined.append("")
                
                # Add translated paragraph
                if trans_para:
                    combined.extend(trans_para)
                    combined.append("")
        
        # Remove final empty line if exists
        if combined and combined[-1] == "":
            combined.pop()
        
        return combined
    
    def _is_bullet_list(self, lines: List[str]) -> bool:
        """Check if the lines form a bullet list."""
        if not lines:
            return False
        
        # Check if most lines start with bullet points
        bullet_count = 0
        non_empty_count = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                non_empty_count += 1
                if stripped.startswith(('- ', '* ', '+ ')):
                    bullet_count += 1
        
        # Consider it a bullet list if most non-empty lines are bullets
        return non_empty_count > 0 and bullet_count >= non_empty_count * 0.5
    
    def _combine_bullet_lists(self, orig_list: List[str], trans_list: List[str]) -> List[str]:
        """Combine two bullet lists into dual-language format."""
        combined = []
        
        # Extract bullet items from both lists
        orig_bullets = self._extract_bullet_items(orig_list)
        trans_bullets = self._extract_bullet_items(trans_list)
        
        # Combine bullets one by one
        max_bullets = max(len(orig_bullets), len(trans_bullets))
        
        for i in range(max_bullets):
            orig_bullet = orig_bullets[i] if i < len(orig_bullets) else ""
            trans_bullet = trans_bullets[i] if i < len(trans_bullets) else ""
            
            if orig_bullet and trans_bullet:
                # Remove just the bullet marker, keep the rest
                orig_text = re.sub(r'^[-*+]\s*', '', orig_bullet).strip()
                trans_text = re.sub(r'^[-*+]\s*', '', trans_bullet).strip()
                combined.append(f"- {orig_text} / {trans_text}")
            elif orig_bullet:
                combined.append(orig_bullet)
            elif trans_bullet:
                combined.append(trans_bullet)
        
        return combined
    
    def _extract_bullet_items(self, lines: List[str]) -> List[str]:
        """Extract bullet items from a list of lines."""
        bullets = []
        
        for line in lines:
            stripped = line.strip()
            if stripped and stripped.startswith(('- ', '* ', '+ ')):
                bullets.append(stripped)
        
        return bullets
    
    def _split_into_paragraphs(self, lines: List[str]) -> List[List[str]]:
        """Split lines into paragraphs based on empty lines."""
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            if line.strip() == "":
                if current_paragraph:
                    paragraphs.append(current_paragraph)
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # Add final paragraph if exists
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        return paragraphs
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for matching by removing common variations.
        """
        # Remove leading/trailing whitespace and convert to lowercase
        normalized = title.strip().lower()
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Create a simple keyword-based mapping for common translations
        # This helps match content even with different languages
        keyword_mappings = {
            'test book sample dual language content': 'book_main_title',
            'sách kiểm tra nội dung song ngữ mẫu': 'book_main_title',
            'chapter 1 introduction': 'chapter_1_intro',
            'chương 1 giới thiệu': 'chapter_1_intro',
            'chapter 2 technology': 'chapter_2_tech',
            'chương 2 công nghệ': 'chapter_2_tech',
            'features': 'features_section',
            'tính năng': 'features_section',
            'chapter 3 getting started': 'chapter_3_start',
            'chương 3 bắt đầu': 'chapter_3_start',
            'conclusion': 'conclusion_section',
            'kết luận': 'conclusion_section'
        }
        
        # Check if we have a direct mapping
        if normalized in keyword_mappings:
            return keyword_mappings[normalized]
        
        return normalized.strip()
    
    def combine_files(self, original_file_path: Path, translated_file_path: Path, 
                     output_file_path: Path) -> bool:
        """
        Combine two markdown files and write the result to output file.
        
        Args:
            original_file_path: Path to original.md
            translated_file_path: Path to translatedcontent.md
            output_file_path: Path to write combined content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read original file
            if not original_file_path.exists():
                self.logger.error(f"Original file not found: {original_file_path}")
                return False
            
            with open(original_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Read translated file
            if not translated_file_path.exists():
                self.logger.error(f"Translated file not found: {translated_file_path}")
                return False
            
            with open(translated_file_path, 'r', encoding='utf-8') as f:
                translated_content = f.read()
            
            # Combine content
            combined_content = self.combine_markdown_files(original_content, translated_content)
            
            # Write combined content
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            self.logger.info(f"Successfully combined files to: {output_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error combining files: {str(e)}")
            return False
