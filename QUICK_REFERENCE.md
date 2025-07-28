# DC EPUB Composer - Quick Reference

## 🚀 Quick Commands

### Generate Dual-Language EPUB
```bash
# Activate environment and generate EPUB
source venv/bin/activate
python generate_final_epub.py
```

### Process Specific Book
```bash
python main.py --book-id [job-id] --storage-root storage-new
```

### Check Available Composers
```python
from core.ComposerFactory import ComposerFactory
factory = ComposerFactory()
print(factory.get_available_composers())
```

## 📁 File Structure Reference

### Input Files (storage-new/[job-id]/)
- `originalbook.md` - English source content
- `translatedcontent.md` - Vietnamese translated content  
- `images/` - Associated images

### Output Files
- `dual-language-FINAL.epub` - Final dual-language e-book

### Key Source Files
- `position_based_combiner.py` - Core dual-language logic
- `generate_final_epub.py` - Complete EPUB generation
- `core/RealStorageDualLanguageComposer.py` - Production composer
- `core/ComposerFactory.py` - Composer factory and registry

## 🔧 Common Code Patterns

### Basic Usage
```python
from position_based_combiner import PositionBasedCombiner

combiner = PositionBasedCombiner()
result = combiner.combine_by_position(english_content, vietnamese_content)
```

### Factory Pattern
```python
from core.ComposerFactory import ComposerFactory

factory = ComposerFactory()
composer = factory.find_suitable_composer(book_id, storage_root)
result = composer.compose(book_id, storage_root)
```

### Custom Composer
```python
from core.IComposer import IComposer

class MyComposer(IComposer):
    def can_compose(self, book_id, storage_root):
        # Check if this composer can handle the content
        return True
    
    def compose(self, book_id, storage_root):
        # Main composition logic
        return {"success": True, "output_path": "path/to/epub"}
    
    def get_name(self):
        return "my_custom_composer"
```

## 📊 Processing Statistics

### Typical Performance
- **Input Size**: ~2MB markdown files
- **Output Size**: ~3MB EPUB file
- **Processing Time**: 2-5 seconds
- **Memory Usage**: <100MB
- **Content Volume**: 600+ headers, 14K+ Vietnamese characters

### Success Metrics
- **Section Matching**: Position-based (handles translated titles)
- **Content Integration**: Side-by-side English/Vietnamese
- **Format Quality**: Professional EPUB 3.0 standard
- **Image Handling**: Embedded with proper scaling

## 🐛 Quick Debugging

### Check Input Files
```bash
ls -la storage-new/[job-id]/
file storage-new/[job-id]/*.md  # Check encoding
```

### Verify Dependencies
```bash
pip list | grep -E "(markdown|ebooklib|beautifulsoup4|lxml)"
```

### Test Basic Functionality
```python
# Test combiner
from position_based_combiner import PositionBasedCombiner
combiner = PositionBasedCombiner()
print("✅ PositionBasedCombiner loaded")

# Test factory
from core.ComposerFactory import ComposerFactory
factory = ComposerFactory()
print(f"✅ Available composers: {len(factory.get_available_composers())}")
```

### Common Issues
1. **Missing Vietnamese content**: Check `translatedcontent.md` exists and has content
2. **Encoding errors**: Ensure UTF-8 encoding for Vietnamese files
3. **Section mismatch**: Use position-based combiner (handles title differences)
4. **Import errors**: Verify virtual environment activated and dependencies installed

## 🎯 Key Algorithms

### Position-Based Matching
- **Purpose**: Match English and Vietnamese sections by order, not title
- **Benefit**: Handles translated titles correctly ("Clean Code" → "Mã Sạch")
- **Implementation**: Index-based matching with fallback handling

### Dual-Language Formatting
- **H1 Headers**: Separate lines for main titles
- **Other Headers**: Combined with " / " separator
- **Content**: Alternating English/Vietnamese paragraphs
- **Images**: Preserved with proper embedding

## 📝 Configuration Options

### Composer Priority (ComposerFactory)
1. `real_storage_dual_language_markdown` - Production (RealStorageDualLanguageComposer)
2. `dual_language_markdown` - Testing (DualLanguageMarkdownComposer)  
3. `simple_markdown` - Basic (SimpleMarkdownComposer)
4. `paragraph_by_paragraph` - Alternative (ParagraphByParagraphComposer)

### File Naming Conventions
- Input: `originalbook.md`, `translatedcontent.md`
- Output: `dual-language-FINAL.epub`
- Images: `images/*.{png,jpg,jpeg}`

### Processing Parameters
- Encoding: UTF-8
- Format: EPUB 3.0
- Language tags: en, vi
- Image optimization: Automatic scaling

---

*For complete documentation, see [COMPREHENSIVE_DOCUMENTATION.md](COMPREHENSIVE_DOCUMENTATION.md)*
