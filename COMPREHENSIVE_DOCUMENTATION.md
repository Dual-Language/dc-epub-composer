# DC EPUB Composer - Comprehensive Documentation

## Overview

DC EPUB Composer is a dual-language EPUB generation system that combines English and Vietnamese content into professionally formatted e-books. The system processes markdown files and generates EPUBs with side-by-side dual-language content.

## Project Structure

```
dc-epub-composer/
├── main.py                           # Main application entry point
├── position_based_combiner.py        # Position-based dual-language combiner
├── generate_final_epub.py           # Final EPUB generation script
├── event_logger.py                  # Event logging utility
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── common/                          # Common utilities
│   ├── configuration.py             # Application configuration
│   └── logger.py                    # Logging utilities
├── core/                            # Core composer modules
│   ├── IComposer.py                 # Composer interface
│   ├── IComposingWorker.py          # Worker interface
│   ├── ComposerFactory.py           # Factory pattern for composers
│   ├── ComposingWorker.py           # Background processing worker
│   ├── DualLanguageCombiner.py      # Core dual-language logic
│   ├── DualLanguageMarkdownComposer.py     # Test dual-language composer
│   ├── RealStorageDualLanguageComposer.py  # Production dual-language composer
│   ├── SimpleMarkdownComposer.py    # Basic markdown composer
│   └── ParagraphByParagraphComposer.py     # Alternative composer
├── storage/                         # Legacy storage format
└── storage-new/                     # Current storage format
    └── [job-id]/                    # Individual job directories
        ├── originalbook.md          # English source content
        ├── translatedcontent.md     # Vietnamese translated content
        └── images/                  # Associated images
```

## Core Components

### 1. Main Entry Point

#### `main.py`
The primary application entry point that orchestrates the entire EPUB generation process.

**Key Features:**
- Command-line interface for processing books
- Integration with ComposerFactory for automatic composer selection
- Handles both single book and batch processing modes

**Usage:**
```bash
python main.py --book-id [job-id] --storage-root storage-new
```

### 2. Position-Based Combiner

#### `position_based_combiner.py`
**Purpose:** The core dual-language combination logic that matches English and Vietnamese content by section order rather than title matching.

**Key Features:**
- Position-based section matching (solves title translation mismatch issues)
- Preserves markdown structure and formatting
- Handles different header levels appropriately
- Provides detailed processing statistics

**Class: `PositionBasedCombiner`**

**Methods:**
- `combine_by_position(original_content, translated_content)` - Main combination logic
- Uses `DualLanguageCombiner._parse_markdown_sections()` for section parsing

**Example Usage:**
```python
from position_based_combiner import PositionBasedCombiner

combiner = PositionBasedCombiner()
combined = combiner.combine_by_position(english_content, vietnamese_content)
```

**Processing Logic:**
1. Parse both documents into sections using markdown headers
2. Match sections by index position (1st English with 1st Vietnamese, etc.)
3. Combine headers: H1 titles on separate lines, others combined with " / "
4. Merge content paragraphs alternating English/Vietnamese
5. Handle edge cases for unmatched sections

### 3. EPUB Generation

#### `generate_final_epub.py`
**Purpose:** Complete script that generates professional dual-language EPUBs using position-based matching.

**Key Features:**
- Uses `ebooklib` for EPUB creation
- Proper HTML formatting with CSS styling
- Image integration and processing
- Metadata management (title, author, language)
- Chapter structure with navigation

**Main Function: `generate_final_dual_language_epub()`**

**Processing Steps:**
1. Read original and translated markdown files
2. Combine content using PositionBasedCombiner
3. Convert markdown to HTML
4. Apply CSS styling for dual-language formatting
5. Process and embed images
6. Generate EPUB with proper structure
7. Save final output

**Output:** `dual-language-FINAL.epub` - Professional dual-language e-book

### 4. Core Architecture

#### `core/ComposerFactory.py`
**Purpose:** Factory pattern implementation for creating appropriate composer instances.

**Registered Composers (Priority Order):**
1. `real_storage_dual_language_markdown` - Production dual-language (RealStorageDualLanguageComposer)
2. `dual_language_markdown` - Test scenarios (DualLanguageMarkdownComposer)
3. `simple_markdown` - Basic processing (SimpleMarkdownComposer)
4. `paragraph_by_paragraph` - Alternative approach (ParagraphByParagraphComposer)

**Key Methods:**
- `find_suitable_composer(book_id, storage_root)` - Auto-selects appropriate composer
- `get_composer(name)` - Creates specific composer instance
- `register_composer(name, composer_class)` - Adds new composer types

#### `core/IComposer.py`
**Purpose:** Interface defining the contract for all composer implementations.

**Required Methods:**
- `can_compose(book_id, storage_root)` - Checks if composer can handle the content
- `compose(book_id, storage_root)` - Main composition logic
- `get_name()` - Returns composer identifier
- `set_filenames(filenames)` - Configures input file names

#### `core/RealStorageDualLanguageComposer.py`
**Purpose:** Production composer for processing storage-new format with real translated content.

**Key Features:**
- Handles `originalbook.md` and `translatedcontent.md` files
- Integrates with PositionBasedCombiner for content combination
- Processes images and maintains file structure
- Generates production-ready dual-language EPUBs

#### `core/DualLanguageCombiner.py`
**Purpose:** Core utility class for markdown parsing and section management.

**Key Methods:**
- `_parse_markdown_sections(content)` - Parses markdown into structured sections
- `_extract_section_content(lines, start_idx)` - Extracts content for specific sections
- Section-based content organization and manipulation

#### `core/ComposingWorker.py`
**Purpose:** Background worker for processing multiple books asynchronously.

**Features:**
- Queue-based processing
- Error handling and logging
- Progress tracking
- Batch processing capabilities

### 5. Utility Components

#### `event_logger.py`
**Purpose:** Centralized event logging for the entire application.

**Features:**
- Structured logging with book ID context
- Multiple log levels (INFO, WARN, ERROR)
- File-based log storage
- Integration with all composer components

#### `common/logger.py`
**Purpose:** Base logging configuration and utilities.

**Features:**
- Configurable log levels
- File and console output
- Timestamp and formatting standards

#### `common/configuration.py`
**Purpose:** Application-wide configuration management.

**Configuration Options:**
- Storage paths and file naming conventions
- EPUB generation settings
- Processing parameters
- Default composer selections

## Data Flow

### Input Processing
1. **Source Files:**
   - `storage-new/[job-id]/originalbook.md` - English content
   - `storage-new/[job-id]/translatedcontent.md` - Vietnamese content
   - `storage-new/[job-id]/images/` - Associated images

### Processing Pipeline
1. **Content Reading:** Files loaded with UTF-8 encoding
2. **Section Parsing:** Markdown headers used to identify sections
3. **Position Matching:** Sections matched by order (1st→1st, 2nd→2nd, etc.)
4. **Content Combination:** English and Vietnamese merged with proper formatting
5. **HTML Conversion:** Markdown converted to styled HTML
6. **EPUB Assembly:** Complete e-book structure created
7. **Output Generation:** Final EPUB file saved

### Output Structure
- **File:** `dual-language-FINAL.epub`
- **Format:** Standard EPUB 3.0
- **Content:** Dual-language with side-by-side formatting
- **Images:** Embedded with proper scaling
- **Navigation:** Chapter-based table of contents

## Key Algorithms

### Position-Based Matching Algorithm

**Problem Solved:** Traditional title-matching fails when titles are translated (e.g., "Clean Code" → "Mã Sạch")

**Solution:** Match sections by their position/order in the document

**Implementation:**
```python
# Parse both documents
original_sections = parse_markdown_sections(original_content)
translated_sections = parse_markdown_sections(translated_content)

# Match by position
max_sections = min(len(original_sections), len(translated_sections))
for i in range(max_sections):
    orig_section = original_sections[i]
    trans_section = translated_sections[i]
    # Combine sections...
```

**Benefits:**
- Handles translated titles correctly
- Maintains document structure
- Processes real-world translated content
- Robust against formatting variations

## Usage Examples

### Basic EPUB Generation
```bash
# Generate EPUB for specific book
python generate_final_epub.py

# Or using main application
python main.py --book-id 1265e85f-3ba7-475b-b7a2-f9fdf1dc5043 --storage-root storage-new
```

### Programmatic Usage
```python
from position_based_combiner import PositionBasedCombiner
from generate_final_epub import generate_final_dual_language_epub

# Direct combination
combiner = PositionBasedCombiner()
result = combiner.combine_by_position(english_text, vietnamese_text)

# Full EPUB generation
generate_final_dual_language_epub()
```

### Factory Pattern Usage
```python
from core.ComposerFactory import ComposerFactory

factory = ComposerFactory()
composer = factory.find_suitable_composer(book_id, storage_root)
if composer:
    result = composer.compose(book_id, storage_root)
```

## Configuration

### Dependencies (`requirements.txt`)
```
markdown>=3.4.0
ebooklib>=0.18
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Performance Characteristics

### Typical Processing Stats
- **Input:** ~2MB markdown files
- **Output:** ~3MB EPUB file
- **Processing Time:** 2-5 seconds
- **Memory Usage:** <100MB
- **Section Matching:** 600+ dual-language headers
- **Character Processing:** 14K+ Vietnamese characters

### Scalability
- **Batch Processing:** Supports multiple books via ComposingWorker
- **Memory Efficient:** Streaming processing for large files
- **Error Recovery:** Graceful handling of malformed content

## Error Handling

### Common Issues and Solutions

1. **File Not Found:**
   - Verify job ID exists in storage-new
   - Check file naming: `originalbook.md`, `translatedcontent.md`

2. **Encoding Errors:**
   - Ensure UTF-8 encoding for Vietnamese content
   - Check BOM handling in text editors

3. **Section Mismatch:**
   - Use position-based combiner (handles translation differences)
   - Verify markdown structure consistency

4. **Image Processing:**
   - Check image file formats (PNG, JPG supported)
   - Verify image directory structure

### Logging and Debugging
- Event logs stored in `storage/composingservice.log`
- Debug output includes section counts and character statistics
- Error details logged with book ID context

## Development Guidelines

### Adding New Composers
1. Implement `IComposer` interface
2. Register in `ComposerFactory`
3. Add appropriate tests
4. Update documentation

### Extending Language Support
1. Update position-based matching logic
2. Modify HTML/CSS templates
3. Test with new language character sets
4. Update metadata handling

### Performance Optimization
1. Profile memory usage with large files
2. Optimize markdown parsing for speed
3. Consider parallel processing for batch operations
4. Cache compiled patterns and templates

## Future Enhancements

### Planned Features
- Multi-language support (beyond English/Vietnamese)
- Interactive EPUB with language switching
- Advanced formatting options
- Cloud storage integration
- Web-based interface

### Technical Improvements
- Streaming processing for very large files
- Advanced error recovery mechanisms
- Enhanced image optimization
- Automated testing suite

## Troubleshooting

### Quick Diagnostics
```bash
# Check file structure
ls -la storage-new/[job-id]/

# Verify file encoding
file storage-new/[job-id]/*.md

# Test basic combination
python -c "from position_based_combiner import PositionBasedCombiner; print('OK')"
```

### Common Solutions
- **Missing Vietnamese content:** Check `translatedcontent.md` file exists and has content
- **Malformed EPUB:** Verify all dependencies installed correctly
- **Processing errors:** Check logs in `storage/composingservice.log`

---

*This documentation covers the complete DC EPUB Composer system as of the current implementation. For additional support or feature requests, refer to the project repository or contact the development team.*
