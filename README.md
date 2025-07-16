# Composing Service

## Overview
The composing service reads translated content and composes final EPUB files according to configuration. It uses an IoC (Inversion of Control) architecture to support multiple composition strategies.

## Architecture

### IoC Design
- **IComposer Interface**: Defines the contract for all composer implementations
- **ComposerFactory**: Manages composer registration and selection
- **ComposingWorker**: Main service that continuously scans for jobs

### Available Composers

#### 1. SimpleMarkdownComposer (Implemented)
- **Purpose**: Converts `translatedcontent.md` to `final.epub`
- **Input**: `translatedcontent.md` file
- **Output**: `final.epub` file
- **Status**: ✅ Fully implemented and tested

#### 2. ParagraphByParagraphComposer (Placeholder)
- **Purpose**: Combines original and translated content paragraph by paragraph
- **Input**: 
  - `translatedcontent.md`
  - `originalbook.md`
  - `translatedcontent.json`
  - `contentbreakdown.json`
- **Output**: `final.epub` with bilingual layout
- **Status**: 🔄 Placeholder - to be implemented

## File Structure
```
composingservice/
├── common/
│   ├── configuration.py    # Configuration management
│   └── logger.py          # Logging utilities
├── core/
│   ├── IComposer.py                    # Composer interface
│   ├── ComposerFactory.py              # IoC factory
│   ├── ComposingWorker.py              # Main worker
│   ├── SimpleMarkdownComposer.py       # Simple markdown composer
│   └── ParagraphByParagraphComposer.py # Future implementation
├── main.py                # Service entry point
├── test_composer.py       # Test script
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

### Environment Variables
- `STORAGE_ROOT`: Storage directory path (default: `../storage`)
- `SLEEP_INTERVAL`: Scan interval in seconds (default: `10`)
- `DEFAULT_COMPOSER`: Default composer type (default: `simple_markdown`)

### Progress Tracking
Each book maintains a progress file: `{book_id}/composingservice-progress.json`

Example progress:
```json
{
  "book_id": "example-book-123",
  "composer": "simple_markdown",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "started_at": "2024-01-01T12:00:01",
  "completed_at": "2024-01-01T12:00:05",
  "output_file": "/path/to/final.epub"
}
```

## Usage

### Running the Service
```bash
# Direct execution
python main.py

# Docker
docker-compose up composingservice

# Test
python test_composer.py
```

### Job Detection
The service automatically detects jobs by scanning the storage directory for:
1. Books with `translatedcontent.md` but no `final.epub`
2. Books not already processed (based on progress files)
3. Books that have a suitable composer available

### Output
- **Success**: Creates `final.epub` in the book directory
- **Failure**: Updates progress with error details
- **Logs**: Service and book-specific log files

## Development

### Adding New Composers
1. Implement the `IComposer` interface
2. Register in `ComposerFactory._register_default_composers()`
3. Add tests

### Testing
```bash
# Run the test script
python test_composer.py

# Check logs
tail -f storage/composingservice.log
```

## Dependencies
- `beautifulsoup4`: HTML parsing
- `EbookLib`: EPUB creation
- `Markdown`: Markdown to HTML conversion
- `lxml`: XML processing

## Future Enhancements
- [ ] Implement ParagraphByParagraphComposer
- [ ] Add side-by-side layout composer
- [ ] Add chapter-by-chapter composer
- [ ] Add custom CSS styling options
- [ ] Add image optimization
- [ ] Add metadata extraction from source files

## Integration with Other Services

### Service Dependencies
The composing service integrates with the following services in the pipeline:

1. **Translation Service** → **Composing Service**
   - Translation service creates `translatedcontent.md`
   - Composing service detects and processes this file

2. **Composing Service** → **Email Service**
   - Composing service creates `final.epub`
   - Email service detects and sends completion notifications

### File Flow
```
Translation Service
    ↓ (creates translatedcontent.md)
Composing Service
    ↓ (creates final.epub)
Email Service
    ↓ (sends notifications)
```

### Storage Structure
```
storage/
├── {book-id-1}/
│   ├── translatedcontent.md          ← Input from translation service
│   ├── composingservice-progress.json ← Progress tracking
│   └── final.epub                   ← Output for email service
├── {book-id-2}/
│   └── ...
└── composingservice.log              ← Service logs
```

## Monitoring and Debugging

### Log Files
- **Service Log**: `storage/composingservice.log` - General service activity
- **Book Log**: `storage/{book-id}/composingservice-book.log` - Per-book processing

### Progress Tracking
Each book maintains a progress file with status:
- `pending`: Waiting to be processed
- `processing`: Currently being composed
- `completed`: Successfully created EPUB
- `error`: Failed with error details
- `not_implemented`: Placeholder composer used

### Common Issues and Solutions

#### Issue: Service not finding jobs
**Check**: 
- Verify `translatedcontent.md` exists in book directory
- Check if `final.epub` already exists (prevents reprocessing)
- Review progress file status

#### Issue: EPUB creation fails
**Check**:
- Markdown file syntax and encoding
- Available disk space
- File permissions in storage directory

#### Issue: Service not starting
**Check**:
- Python dependencies installed (`pip install -r requirements.txt`)
- Storage directory exists and is writable
- Environment variables set correctly

## Performance Considerations

### Resource Usage
- **Memory**: Low - processes one book at a time
- **CPU**: Moderate during EPUB creation
- **Disk**: Temporary files during composition

### Optimization Tips
- Adjust `SLEEP_INTERVAL` for different scan frequencies
- Monitor log file sizes and rotate if needed
- Consider SSD storage for faster I/O

## Security Notes

### File Permissions
- Service creates files with default permissions
- Ensure storage directory has appropriate access controls
- Consider running service with limited user privileges

### Input Validation
- Validates markdown file existence before processing
- Handles malformed markdown gracefully
- Logs all errors for debugging

## Development Workflow

### Adding New Composers
1. Create new class implementing `IComposer`
2. Add to `ComposerFactory._register_default_composers()`
3. Update tests and documentation
4. Test with sample data

### Testing Strategy
- **Unit Tests**: Test individual composer logic
- **Integration Tests**: Test full service workflow
- **End-to-End**: Test with real markdown files

### Deployment Checklist
- [ ] Dependencies installed
- [ ] Storage directory configured
- [ ] Environment variables set
- [ ] Service starts without errors
- [ ] Can process sample book
- [ ] Logs are being written
- [ ] Progress files created correctly

## API Reference

### IComposer Interface
```python
class IComposer(ABC):
    def get_name(self) -> str: ...
    def can_compose(self, book_id: str, storage_root: str) -> bool: ...
    def compose(self, book_id: str, storage_root: str, config: Optional[Dict[str, Any]] = None) -> bool: ...
    def get_progress(self, book_id: str, storage_root: str) -> Dict[str, Any]: ...
    def save_progress(self, book_id: str, storage_root: str, progress: Dict[str, Any]) -> None: ...
```

### ComposerFactory Methods
```python
class ComposerFactory:
    def register_composer(self, name: str, composer_class: Type[IComposer]): ...
    def get_composer(self, name: str) -> Optional[IComposer]: ...
    def get_available_composers(self) -> list[str]: ...
    def find_suitable_composer(self, book_id: str, storage_root: str) -> Optional[IComposer]: ...
```

## Troubleshooting Guide

### Service Won't Start
1. Check Python version (requires 3.8+)
2. Verify dependencies: `pip install -r requirements.txt`
3. Check storage directory permissions
4. Review environment variables

### No Jobs Found
1. Verify `translatedcontent.md` exists in book directories
2. Check if `final.epub` already exists (prevents reprocessing)
3. Review progress file status
4. Check log files for errors

### EPUB Creation Fails
1. Validate markdown syntax
2. Check available disk space
3. Verify file encoding (UTF-8)
4. Review error logs for specific issues

### Performance Issues
1. Adjust `SLEEP_INTERVAL` for different scan frequencies
2. Monitor disk I/O and CPU usage
3. Consider SSD storage for faster processing
4. Review log file sizes and implement rotation

## Contributing

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and return values
- Add docstrings for all public methods
- Include error handling for all external operations

### Testing Requirements
- Unit tests for all composer implementations
- Integration tests for the full workflow
- Test with various markdown formats and edge cases
- Verify error handling and recovery

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Submit pull request with description
5. Ensure all tests pass
6. Code review and approval

## License
This service is part of the practice-unit-tests project and follows the same licensing terms. 