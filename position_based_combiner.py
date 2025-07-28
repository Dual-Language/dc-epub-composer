#!/usr/bin/env python3
"""
Position-based dual-language combiner for real books
Matches sections by order instead of title matching
"""

import sys
import os
from pathlib import Path

# Add the dc-epub-composer directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.DualLanguageCombiner import DualLanguageCombiner

class PositionBasedCombiner:
    """Combines dual-language content by section position instead of title matching."""
    
    def __init__(self):
        self.combiner = DualLanguageCombiner()
    
    def combine_by_position(self, original_content: str, translated_content: str) -> str:
        """Combine content by matching sections in order."""
        
        # Parse both documents into sections
        original_sections = self.combiner._parse_markdown_sections(original_content)
        translated_sections = self.combiner._parse_markdown_sections(translated_content)
        
        print(f"📊 Position-based matching:")
        print(f"   Original sections: {len(original_sections)}")
        print(f"   Translated sections: {len(translated_sections)}")
        
        combined_lines = []
        
        # Match sections by position (index)
        max_sections = min(len(original_sections), len(translated_sections))
        print(f"   Matching first {max_sections} sections")
        
        for i in range(max_sections):
            orig_level, orig_title, orig_content = original_sections[i]
            trans_level, trans_title, trans_content = translated_sections[i]
            
            # Combine headers
            if orig_level == '#':  # H1 - main title
                combined_lines.append(f"# {orig_title}")
                combined_lines.append("")
                # Use simple italic for Vietnamese titles
                combined_lines.append(f'# *{trans_title}*')
            else:  # Other headers - combine in single line with italic Vietnamese
                combined_lines.append(f'{orig_level} {orig_title} / *{trans_title}*')
            
            combined_lines.append("")
            
            # Combine content paragraph by paragraph
            combined_content = self._combine_content_by_position(orig_content, trans_content)
            combined_lines.extend(combined_content)
            combined_lines.append("")
        
        # Add any remaining sections from the longer document
        if len(original_sections) > max_sections:
            print(f"   Adding {len(original_sections) - max_sections} remaining original sections")
            for i in range(max_sections, len(original_sections)):
                orig_level, orig_title, orig_content = original_sections[i]
                combined_lines.append(f"{orig_level} {orig_title}")
                combined_lines.append("")
                combined_lines.extend(orig_content)
                combined_lines.append("")
        
        if len(translated_sections) > max_sections:
            print(f"   Adding {len(translated_sections) - max_sections} remaining translated sections")
            for i in range(max_sections, len(translated_sections)):
                trans_level, trans_title, trans_content = translated_sections[i]
                combined_lines.append(f"{trans_level} {trans_title}")
                combined_lines.append("")
                combined_lines.extend(trans_content)
                combined_lines.append("")
        
        # Remove trailing empty lines
        while combined_lines and combined_lines[-1] == "":
            combined_lines.pop()
        
        return '\n'.join(combined_lines)
    
    def _combine_content_by_position(self, orig_content: list, trans_content: list) -> list:
        """Combine content paragraphs by position, avoiding image duplication."""
        combined = []
        
        # Split into paragraphs
        orig_paragraphs = self._split_into_paragraphs(orig_content)
        trans_paragraphs = self._split_into_paragraphs(trans_content)
        
        # Combine paragraphs by position
        max_paragraphs = max(len(orig_paragraphs), len(trans_paragraphs))
        
        for i in range(max_paragraphs):
            orig_para = orig_paragraphs[i] if i < len(orig_paragraphs) else []
            trans_para = trans_paragraphs[i] if i < len(trans_paragraphs) else []
            
            # Check if this paragraph contains images
            orig_has_images = self._contains_images(orig_para)
            trans_has_images = self._contains_images(trans_para)
            
            if orig_has_images or trans_has_images:
                # For image paragraphs, only include once (prefer original)
                if orig_para:
                    combined.extend(orig_para)
                    combined.append("")
                elif trans_para:
                    combined.extend(trans_para)
                    combined.append("")
            else:
                # For text paragraphs, include both languages
                # Add original paragraph
                if orig_para:
                    combined.extend(orig_para)
                    combined.append("")
                
                # Add translated paragraph with Vietnamese styling
                if trans_para:
                    styled_para = self._add_vietnamese_styling(trans_para)
                    combined.extend(styled_para)
                    combined.append("")
        
        return combined
    
    def _contains_images(self, paragraph: list) -> bool:
        """Check if a paragraph contains markdown images."""
        for line in paragraph:
            # Check for markdown image syntax: ![alt](image.png) or ![](image.png)
            if '![' in line and '](' in line:
                return True
        return False
    
    def _add_vietnamese_styling(self, paragraph: list) -> list:
        """Add italic styling to Vietnamese content."""
        styled_paragraph = []
        for line in paragraph:
            if line.strip():  # Only style non-empty lines
                # Use simple italic formatting for Vietnamese content
                styled_line = f'*{line}*'
                styled_paragraph.append(styled_line)
            else:
                styled_paragraph.append(line)  # Keep empty lines as is
        return styled_paragraph
    
    def _split_into_paragraphs(self, content: list) -> list:
        """Split content into paragraphs separated by empty lines."""
        paragraphs = []
        current_paragraph = []
        
        for line in content:
            if line.strip() == "":
                if current_paragraph:
                    paragraphs.append(current_paragraph)
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # Add the last paragraph if it exists
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        return paragraphs

def test_position_based_combination(storage_root="storage-new", job_id="1265e85f-3ba7-475b-b7a2-f9fdf1dc5043"):
    """Test the position-based combination approach."""
    print("🔄 TESTING: Position-Based Dual-Language Combination")
    print("="*60)
    
    storage_path = Path(__file__).parent / storage_root
    
    job_path = storage_path / job_id
    original_file = job_path / "originalbook.md"
    translated_file = job_path / "translatedcontent.md"
    
    # Check if files exist
    if not original_file.exists():
        print(f"❌ Original file not found: {original_file}")
        return False
    if not translated_file.exists():
        print(f"❌ Translated file not found: {translated_file}")
        return False
    
    # Read files
    with open(original_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(translated_file, 'r', encoding='utf-8') as f:
        translated_content = f.read()
    
    print(f"📂 Processing: {job_id}")
    print(f"📊 Input sizes:")
    print(f"   Original: {len(original_content):,} chars")
    print(f"   Translated: {len(translated_content):,} chars")
    
    # Use position-based combiner
    combiner = PositionBasedCombiner()
    
    try:
        combined_content = combiner.combine_by_position(original_content, translated_content)
        
        if combined_content:
            print(f"\n✅ Position-based combination successful!")
            
            # Analysis
            dual_markers = combined_content.count(" / ")
            vietnamese_chars = sum(1 for char in combined_content if ord(char) > 127)
            
            print(f"📊 Results:")
            print(f"   Combined size: {len(combined_content):,} chars")
            print(f"   Dual-language markers (/): {dual_markers}")
            print(f"   Vietnamese characters: {vietnamese_chars:,}")
            
            # Save result
            output_file = job_path / "combined-dual-language-POSITION.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            print(f"💾 Saved to: {output_file.name}")
            
            # Show preview
            print(f"\n📋 Preview (first 20 lines):")
            lines = combined_content.split('\n')
            for i, line in enumerate(lines[:20]):
                prefix = "🔸" if " / " in line else "  "
                print(f"   {i+1:2d}. {prefix} {line}")
            
            return True
            
        else:
            print(f"❌ Position-based combination failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_position_based_combination()
    
    if success:
        print(f"\n✅ Position-based combination complete!")
        print(f"🔍 Check combined-dual-language-POSITION.md for proper Vietnamese integration!")
    else:
        print(f"\n❌ Position-based combination failed.")
