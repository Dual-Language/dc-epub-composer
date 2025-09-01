# DC EPUB Composer API

This document describes the REST API endpoints for the DC EPUB Composer service. The API provides a consistent interface following the same pattern as other DC services: **compose → job_status → download**.

## Overview

The DC EPUB Composer API enables programmatic creation of EPUB files from markdown content. It supports both:

- **Single-language composition**: Convert markdown files to EPUB
- **Dual-language composition**: Combine original and translated content into side-by-side dual-language EPUBs

## API Endpoints

### 1. Compose EPUB Files

**POST** `/api/compose`

Submit markdown files for EPUB composition.

#### Single-Language Composition

**Form Fields:**
- `jobId` (string, required): Unique identifier for the composition job
- `markdownFile` (file, required): Markdown file to convert to EPUB
- `composerType` (string, optional): Force specific composer type

**Example:**
```bash
curl -X POST "http://localhost:3002/api/compose" \
  -F "jobId=my-book-123" \
  -F "markdownFile=@content.md"
```

#### Dual-Language Composition

**Form Fields:**
- `jobId` (string, required): Unique identifier for the composition job  
- `originalBook` (file, required): Original markdown content
- `translatedContent` (file, required): Translated markdown content
- `composerType` (string, optional): Force specific composer type

**Example:**
```bash
curl -X POST "http://localhost:3002/api/compose" \
  -F "jobId=dual-book-456" \
  -F "originalBook=@original.md" \
  -F "translatedContent=@translated.md"
```

#### Response

```json
{
  "jobId": "my-book-123",
  "message": "EPUB composition job submitted successfully. The composing service will process it automatically.",
  "composer": "simple_markdown",
  "uploadedFiles": {
    "markdownFile": "translatedcontent.md"
  }
}
```

#### Status Codes
- `200` - Job submitted successfully
- `400` - Bad request (missing jobId, no files, or invalid file combination)
- `409` - Job already exists or is being processed
- `413` - File too large (max 100MB)

### 2. Check Job Status

**GET** `/api/job_status?jobId={jobId}`

Get the current status of an EPUB composition job.

**Example:**
```bash
curl "http://localhost:3002/api/job_status?jobId=my-book-123"
```

#### Response

```json
{
  "status": "completed",
  "progress": {
    "book_id": "my-book-123",
    "composer": "simple_markdown", 
    "status": "completed",
    "created_at": "2025-01-15T10:30:00",
    "completed_at": "2025-01-15T10:30:15",
    "output_file": "/path/to/final.epub"
  },
  "message": "EPUB composition completed",
  "jobType": "epub_composition",
  "composer": "simple_markdown"
}
```

#### Status Values
- `pending` - Job submitted but not yet processed
- `processing` - Job currently being composed
- `completed` - EPUB created successfully  
- `failed` - Job failed with error
- `not_found` - Job ID not found

### 3. Download EPUB File

**GET** `/api/download?jobId={jobId}`

Download the generated EPUB file for a completed job.

**Example:**
```bash
curl -O "http://localhost:3002/api/download?jobId=my-book-123"
```

#### Response
- **Success**: EPUB file download with appropriate filename
- **File Types**:
  - Single-language: `composed-{jobId}.epub`
  - Dual-language: `dual-language-{jobId}.epub`

#### Status Codes
- `200` - File downloaded successfully
- `400` - Job not completed or failed
- `404` - Job or EPUB file not found
- `500` - Error accessing file

## Composer Types

The service automatically detects the appropriate composer based on uploaded files:

### Auto-Detection (Default)
- **Single file** → `simple_markdown` composer
- **Two files** → `real_storage_dual_language` composer

### Manual Selection
Override auto-detection with `composerType` parameter:

- `simple_markdown` - Basic markdown to EPUB conversion
- `dual_language` - Test dual-language composer  
- `real_storage_dual_language` - Production dual-language composer
- `paragraph_by_paragraph` - Alternative processing approach

## File Requirements

### Supported Files
- **Format**: Markdown (.md files only)
- **Size**: Maximum 100MB per file
- **Encoding**: UTF-8 recommended

### File Validation
- File extensions must be `.md`
- Files must not be empty
- Valid markdown syntax recommended

## Running the API Server

### Prerequisites
```bash
# Install API dependencies
pip install flask flask-swagger-ui

# Ensure main service dependencies are installed
pip install -r requirements.txt
```

### Start the Server

#### Development
```bash
python api_server.py
```

#### Production
```bash
PORT=3002 python api_server.py
```

#### With Environment Variables
```bash
export PORT=3002
export DEBUG=false
export STORAGE_ROOT=/path/to/storage
python api_server.py
```

### Configuration

Environment variables:
- `PORT` - Server port (default: 3002)
- `DEBUG` - Debug mode (default: False)
- `STORAGE_ROOT` - Storage directory path
- `SLEEP_INTERVAL` - Background service scan interval

## API Documentation

Interactive API documentation is available at `/api/docs` when the server is running.

**Access**: `http://localhost:3002/api/docs`

The Swagger UI provides:
- Interactive API exploration
- Request/response examples
- Schema definitions
- Try-it-out functionality

## Integration Examples

### Basic Workflow

```bash
# 1. Submit single-language composition
curl -X POST "http://localhost:3002/api/compose" \
  -F "jobId=example-book" \
  -F "markdownFile=@book.md"

# 2. Check status
curl "http://localhost:3002/api/job_status?jobId=example-book"

# 3. Download when completed
curl -O "http://localhost:3002/api/download?jobId=example-book"
```

### Dual-Language Workflow

```bash  
# 1. Submit dual-language composition
curl -X POST "http://localhost:3002/api/compose" \
  -F "jobId=dual-example" \
  -F "originalBook=@english.md" \
  -F "translatedContent=@vietnamese.md"

# 2. Monitor progress
curl "http://localhost:3002/api/job_status?jobId=dual-example"

# 3. Download dual-language EPUB
curl -O "http://localhost:3002/api/download?jobId=dual-example"
```

### Python Integration

```python
import requests
import time

# Submit job
files = {'markdownFile': open('content.md', 'rb')}
data = {'jobId': 'python-example'}

response = requests.post('http://localhost:3002/api/compose', 
                        files=files, data=data)
job_info = response.json()
job_id = job_info['jobId']

# Wait for completion
while True:
    status = requests.get(f'http://localhost:3002/api/job_status?jobId={job_id}')
    status_info = status.json()
    
    if status_info['status'] == 'completed':
        break
    elif status_info['status'] == 'failed':
        print(f"Job failed: {status_info['message']}")
        break
        
    time.sleep(5)

# Download result
epub_response = requests.get(f'http://localhost:3002/api/download?jobId={job_id}')
with open(f'{job_id}.epub', 'wb') as f:
    f.write(epub_response.content)
```

## Architecture Integration

### Service Integration
The API works alongside the existing composing worker:

1. **API Server** - Accepts job submissions via HTTP
2. **Composing Worker** - Background service processes jobs automatically  
3. **Progress Tracking** - Shared progress files between API and worker
4. **File Management** - Unified storage structure

### Storage Structure
```
storage/
├── {jobId}/
│   ├── originalbook.md              # Original content (dual-language)
│   ├── translatedcontent.md         # Translated or single content
│   ├── composingservice-progress.json # Progress tracking
│   ├── final.epub                   # Single-language output
│   └── dual-language-final.epub     # Dual-language output
```

### Background Processing
- API creates job files and progress markers
- Background worker automatically detects new jobs
- Worker processes jobs using existing composer infrastructure
- API provides status updates based on worker progress

## Error Handling

### Common Error Responses

#### Bad Request (400)
```json
{
  "error": "Invalid file combination. Provide either markdownFile for single-language or both originalBook and translatedContent for dual-language composition",
  "received": ["originalBook"]
}
```

#### Job Conflict (409)
```json
{
  "error": "Job already completed",
  "jobId": "my-book-123", 
  "status": "completed"
}
```

#### Not Found (404)
```json
{
  "error": "Job not found"
}
```

### Error Recovery
- Check job status for detailed error information
- Review progress files for processing details
- Validate input files and retry if needed
- Contact support for persistent issues

## Performance Considerations

### File Size Limits
- **Maximum file size**: 100MB per file
- **Recommended size**: Under 10MB for optimal performance
- **Large files**: May require longer processing time

### Processing Time
- **Simple composition**: 2-5 seconds
- **Dual-language composition**: 5-15 seconds  
- **Complex content**: Processing time varies with content complexity

### Concurrent Jobs
- Multiple jobs can be submitted simultaneously
- Background worker processes jobs sequentially
- API responses are immediate (non-blocking)

## Security Considerations

### File Validation
- Only `.md` files accepted
- File size limits enforced
- Filename sanitization applied
- Content validation recommended

### Access Control
- No built-in authentication (implement as needed)
- Consider rate limiting for production use
- Validate job IDs to prevent directory traversal
- Implement proper error handling to avoid information leakage

## Health Check

**GET** `/api/health`

Returns server health status:

```json
{
  "status": "healthy",
  "service": "dc-epub-composer", 
  "timestamp": "2025-01-15T10:30:00"
}
```

## Troubleshooting

### Common Issues

#### API Server Won't Start
- Check Python dependencies: `pip install flask flask-swagger-ui`
- Verify port availability: `lsof -i :3002`
- Check storage directory permissions
- Review environment variables

#### Jobs Stuck in Pending
- Verify background worker is running
- Check worker logs for errors
- Ensure storage directory is writable
- Validate composer configuration

#### Download Fails
- Confirm job status is 'completed'
- Check if EPUB file exists in job directory
- Verify file permissions
- Review server logs for errors

### Debug Mode

Enable debug logging:
```bash
DEBUG=true python api_server.py
```

Debug mode provides:
- Detailed error messages
- Request/response logging  
- Stack traces for troubleshooting
- Auto-reload on code changes

## API Consistency

This API follows the same pattern as other DC services:

| Service | Process Endpoint | Status Endpoint | Download Endpoint |
|---------|-----------------|-----------------|-------------------|
| **dc-breakdown-construct** | `/api/breakdown` | `/api/job_status` | `/api/download` |
| **dc-reconstruction** | `/api/convert` + `/api/reconstruct` | `/api/job_status` | `/api/download` |
| **dc-epub-composer** | `/api/compose` | `/api/job_status` | `/api/download` |

### Consistent Features
- Same status values (`pending`, `processing`, `completed`, `failed`)
- Same job tracking with progress files
- Same error response formats
- Same file upload/download patterns
- Same Swagger documentation structure

This consistency enables easier MCP integration and unified tooling across all DC services.