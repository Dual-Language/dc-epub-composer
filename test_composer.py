#!/usr/bin/env python3
"""
Simple test script for the composing service.
"""

import sys
import os
import tempfile
import pathlib
from pathlib import Path

# Add the composingservice directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.SimpleMarkdownComposer import SimpleMarkdownComposer
from common.logger import get_logger

def test_simple_markdown_composer():
    """Test the simple markdown composer."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_root = temp_dir
        book_id = "test-book-123"
        book_dir = pathlib.Path(storage_root) / book_id
        book_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test markdown file
        test_md_content = """# Test Book

This is a test book with some content.

## Chapter 1

This is the first chapter.

### Section 1.1

This is a subsection.

## Chapter 2

This is the second chapter.

- List item 1
- List item 2
- List item 3

**Bold text** and *italic text*.
"""
        
        translated_content_path = book_dir / "translatedcontent.md"
        with open(translated_content_path, 'w', encoding='utf-8') as f:
            f.write(test_md_content)
        
        # Test the composer
        composer = SimpleMarkdownComposer()
        
        print(f"Testing composer: {composer.get_name()}")
        print(f"Can compose: {composer.can_compose(book_id, storage_root)}")
        
        # Run composition
        success = composer.compose(book_id, storage_root)
        print(f"Composition success: {success}")
        
        # Check if output file was created
        output_path = book_dir / "final.epub"
        print(f"Output file exists: {output_path.exists()}")
        
        # Check progress
        progress = composer.get_progress(book_id, storage_root)
        print(f"Progress: {progress}")
        
        return success and output_path.exists()

if __name__ == "__main__":
    print("Testing SimpleMarkdownComposer...")
    success = test_simple_markdown_composer()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1) 