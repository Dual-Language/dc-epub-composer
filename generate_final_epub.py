#!/usr/bin/env python3
"""
Final script to generate properly combined dual-language EPUB using position-based matching
"""

import sys
import os
from pathlib import Path

# Add the dc-epub-composer directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from position_based_combiner import PositionBasedCombiner

def generate_final_dual_language_epub(storage_root="storage", job_id=None):
    """Generate the final dual-language EPUB with proper Vietnamese integration."""
    print("📚 GENERATING: Final Dual-Language EPUB with Position-Based Matching")
    print("="*70)
    
    storage_path = Path(__file__).parent / storage_root
    
    # If no job_id specified, find available jobs
    if job_id is None:
        available_jobs = [d.name for d in storage_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        available_jobs = [job for job in available_jobs if job not in ['events']]  # Exclude non-job folders
        if available_jobs:
            job_id = available_jobs[0]  # Use first available job
            print(f"📂 Auto-selected job: {job_id}")
        else:
            print("❌ No job folders found in storage")
            return False
    
    job_path = storage_path / job_id
    original_file = job_path / "originalbook.md"
    translated_file = job_path / "translatedcontent.md"
    
    print(f"📂 Processing job: {job_id}")
    print(f"📁 Storage root: {storage_root}")
    
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
    
    # Use position-based combiner
    print(f"🔄 Combining content using position-based matching...")
    combiner = PositionBasedCombiner()
    combined_content = combiner.combine_by_position(original_content, translated_content)
    
    if not combined_content:
        print(f"❌ Failed to combine content!")
        return False
    
    # Analysis
    dual_markers = combined_content.count(" / ")
    vietnamese_chars = sum(1 for char in combined_content if ord(char) > 127)
    
    print(f"✅ Content combined successfully!")
    print(f"📊 Analysis:")
    print(f"   Size: {len(combined_content):,} chars")
    print(f"   Dual-language headers: {dual_markers}")
    print(f"   Vietnamese characters: {vietnamese_chars:,}")
    
    # Save combined markdown
    combined_md_file = job_path / "combined-dual-language-FINAL.md"
    with open(combined_md_file, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    print(f"💾 Saved combined markdown: {combined_md_file.name}")
    
    # Generate EPUB
    print(f"\n📚 Generating EPUB...")
    epub_file = job_path / "dual-language-FINAL.epub"
    
    success = generate_epub_from_content(combined_content, job_id, job_path, epub_file)
    
    if success:
        size_mb = epub_file.stat().st_size / (1024 * 1024)
        print(f"✅ EPUB generated successfully!")
        print(f"📚 File: {epub_file.name} ({size_mb:.2f} MB)")
        
        # Show a sample of the dual-language content
        print(f"\n📋 Sample dual-language content:")
        lines = combined_content.split('\n')
        sample_lines = []
        for line in lines[:100]:  # Check first 100 lines
            if " / " in line and any(ord(char) > 127 for char in line):
                sample_lines.append(line)
                if len(sample_lines) >= 5:
                    break
        
        for i, line in enumerate(sample_lines, 1):
            print(f"   {i}. {line}")
        
        return True
    else:
        print(f"❌ EPUB generation failed!")
        return False

def generate_epub_from_content(content, book_id, book_path, output_path):
    """Generate EPUB from combined dual-language content."""
    try:
        import markdown
        from ebooklib import epub
        
        print(f"   📄 Converting markdown to HTML...")
        # Convert markdown to HTML with HTML preservation
        html_content = markdown.markdown(
            content, 
            extensions=['markdown.extensions.extra', 'markdown.extensions.meta'],
            extension_configs={
                'markdown.extensions.extra': {
                    'markdown.extensions.codehilite': {
                        'css_class': 'highlight'
                    }
                }
            }
        )
        
        print(f"   📖 Creating EPUB structure...")
        # Create EPUB book
        book = epub.EpubBook()
        book.set_identifier(f'dual-lang-final-{book_id}')
        book.set_title('Clean Code (Dual Language)')
        book.set_language('en')
        book.add_author('Robert C. Martin')
        book.add_metadata('DC', 'description', 'Clean Code book with English and Vietnamese content side by side')
        
        # Create chapter from content
        chapter = epub.EpubHtml(title='Clean Code - Dual Language', file_name='content.xhtml', lang='en')
        chapter.content = f'''
        <html>
        <head>
            <title>Clean Code - Dual Language</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    line-height: 1.6;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #333;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                .dual-content {{
                    margin: 20px 0;
                }}
                /* Vietnamese content styling */
                span[style*="color: #2E86AB"] {{
                    color: #2E86AB !important;
                    font-style: italic !important;
                    font-weight: 500;
                    background-color: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                /* Alternative class-based styling */
                .vietnamese {{
                    color: #2E86AB !important;
                    font-style: italic !important;
                    font-weight: 500;
                    background-color: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            <div class="dual-content">
                {html_content}
            </div>
        </body>
        </html>
        '''
        
        book.add_item(chapter)
        
        # Add images
        print(f"   🖼️ Adding images...")
        images_dir = book_path / "images"
        image_count = 0
        
        if images_dir.exists():
            for img_file in images_dir.glob("*"):
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    try:
                        with open(img_file, 'rb') as f:
                            img_data = f.read()
                        
                        img_item = epub.EpubImage()
                        img_item.file_name = f"images/{img_file.name}"
                        img_item.media_type = f"image/{img_file.suffix[1:]}"
                        img_item.content = img_data
                        
                        book.add_item(img_item)
                        image_count += 1
                    except Exception as e:
                        pass  # Skip problematic images
        
        print(f"   📸 Added {image_count} images")
        
        # Table of Contents
        book.toc = (epub.Link("content.xhtml", "Clean Code - Dual Language", "content"),)
        
        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # CSS
        style = '''
        body { 
            font-family: Georgia, serif; 
            margin: 40px; 
            line-height: 1.8;
            color: #333;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }
        h1 { font-size: 2.5em; }
        h2 { font-size: 2em; }
        h3 { font-size: 1.5em; }
        img { max-width: 100%; height: auto; margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        '''
        
        nav_css = epub.EpubItem(
            uid="nav_css", 
            file_name="style/nav.css", 
            media_type="text/css", 
            content=style
        )
        book.add_item(nav_css)
        
        # Spine
        book.spine = ['nav', chapter]
        
        # Write EPUB
        print(f"   💾 Writing EPUB file...")
        epub.write_epub(str(output_path), book, {})
        
        return True
        
    except Exception as e:
        print(f"   ❌ EPUB generation error: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate dual-language EPUB')
    parser.add_argument('--storage-root', default='storage', help='Storage root directory (default: storage)')
    parser.add_argument('--job-id', help='Specific job ID to process')
    
    args = parser.parse_args()
    
    success = generate_final_dual_language_epub(storage_root=args.storage_root, job_id=args.job_id)
    
    if success:
        print(f"\n🎉 SUCCESS! Final dual-language EPUB generated!")
        print(f"✅ Your Vietnamese translations are now properly integrated!")
        print(f"📚 The EPUB contains both English and Vietnamese content side-by-side!")
    else:
        print(f"\n❌ Failed to generate final EPUB.")
