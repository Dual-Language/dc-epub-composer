"""
DC EPUB Composer API Server
Provides REST API endpoints for EPUB composition from markdown files
Following the same pattern as other DC services: compose/job_status/download
"""

import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file
from flask_swagger_ui import get_swaggerui_blueprint

# Import the existing composer infrastructure
from core.ComposerFactory import ComposerFactory
from common.configuration import get_storage_root
from common.logger import get_logger

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configure upload folder
UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logger = get_logger(__name__)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "DC EPUB Composer API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def get_job_progress(job_id: str) -> Dict[str, Any]:
    """Get the current progress of a composition job"""
    storage_root = get_storage_root()
    job_dir = Path(storage_root) / job_id
    progress_file = job_dir / 'composingservice-progress.json'
    
    if not job_dir.exists():
        return {
            'status': 'not_found',
            'message': 'Job not found',
            'jobType': 'epub_composition'
        }
    
    try:
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                
            # Map internal status to API status
            status_mapping = {
                'pending': 'pending',
                'processing': 'processing', 
                'completed': 'completed',
                'error': 'failed',
                'not_implemented': 'failed'
            }
            
            api_status = status_mapping.get(progress.get('status', 'pending'), 'pending')
            
            return {
                'status': api_status,
                'progress': progress,
                'message': progress.get('message', f'EPUB composition {api_status}'),
                'jobType': 'epub_composition',
                'composer': progress.get('composer', 'unknown')
            }
        else:
            # Check if output files exist (completed without progress file)
            output_files = [
                job_dir / 'final.epub',
                job_dir / 'dual-language-final.epub'
            ]
            
            for output_file in output_files:
                if output_file.exists():
                    return {
                        'status': 'completed',
                        'progress': {'status': 'completed'},
                        'message': 'EPUB composition completed (no progress file found)',
                        'jobType': 'epub_composition',
                        'outputFile': str(output_file)
                    }
            
            return {
                'status': 'pending',
                'progress': None,
                'message': 'No composition progress found',
                'jobType': 'epub_composition'
            }
            
    except Exception as e:
        logger.error(f"Error checking job progress for {job_id}: {str(e)}")
        return {
            'status': 'failed',
            'progress': None,
            'message': f'Error checking job progress: {str(e)}',
            'jobType': 'epub_composition'
        }


def save_uploaded_files(job_id: str, files: Dict) -> Dict[str, str]:
    """Save uploaded files to job directory"""
    storage_root = get_storage_root()
    job_dir = Path(storage_root) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = {}
    
    for field_name, file in files.items():
        if file and file.filename:
            filename = secure_filename(file.filename)
            
            # Map field names to expected filenames
            filename_mapping = {
                'originalBook': 'originalbook.md',
                'translatedContent': 'translatedcontent.md',
                'markdownFile': 'translatedcontent.md'  # For simple composition
            }
            
            target_filename = filename_mapping.get(field_name, filename)
            file_path = job_dir / target_filename
            
            file.save(str(file_path))
            saved_files[field_name] = target_filename
            
    return saved_files


@app.route('/api/swagger.json')
def swagger():
    """Return Swagger JSON specification"""
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "DC EPUB Composer API",
            "version": "1.0.0",
            "description": "API for composing EPUB files from markdown content. Supports both single-language and dual-language EPUB generation."
        },
        "paths": {
            "/api/compose": {
                "post": {
                    "summary": "Submit files for EPUB composition",
                    "description": "Upload markdown files for EPUB composition. Supports single-language or dual-language composition based on uploaded files.",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "jobId": {
                                            "type": "string",
                                            "description": "Unique identifier for this composition job"
                                        },
                                        "markdownFile": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "Markdown file for single-language composition"
                                        },
                                        "originalBook": {
                                            "type": "string", 
                                            "format": "binary",
                                            "description": "Original markdown content for dual-language composition"
                                        },
                                        "translatedContent": {
                                            "type": "string",
                                            "format": "binary", 
                                            "description": "Translated markdown content for dual-language composition"
                                        },
                                        "composerType": {
                                            "type": "string",
                                            "enum": ["auto", "simple_markdown", "dual_language", "real_storage_dual_language"],
                                            "description": "Specific composer type to use (optional, defaults to auto-detection)"
                                        }
                                    },
                                    "oneOf": [
                                        {
                                            "required": ["jobId", "markdownFile"]
                                        },
                                        {
                                            "required": ["jobId", "originalBook", "translatedContent"]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Composition job created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "jobId": {"type": "string"},
                                            "message": {"type": "string"},
                                            "composer": {"type": "string"},
                                            "uploadedFiles": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - missing required files or invalid job ID"
                        },
                        "409": {
                            "description": "Job already exists or is being processed"
                        }
                    }
                }
            },
            "/api/job_status": {
                "get": {
                    "summary": "Get composition job status",
                    "description": "Get the current status of an EPUB composition job",
                    "parameters": [{
                        "name": "jobId",
                        "in": "query", 
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Job ID to check status for"
                    }],
                    "responses": {
                        "200": {
                            "description": "Job status retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "enum": ["pending", "processing", "completed", "failed", "not_found"]
                                            },
                                            "progress": {"type": "object"},
                                            "message": {"type": "string"},
                                            "jobType": {"type": "string"},
                                            "composer": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Missing jobId parameter"
                        }
                    }
                }
            },
            "/api/download": {
                "get": {
                    "summary": "Download composed EPUB file",
                    "description": "Download the generated EPUB file for a completed composition job",
                    "parameters": [{
                        "name": "jobId",
                        "in": "query",
                        "required": True, 
                        "schema": {"type": "string"},
                        "description": "Job ID to download EPUB for"
                    }],
                    "responses": {
                        "200": {
                            "description": "EPUB file download"
                        },
                        "400": {
                            "description": "Job not completed or failed"
                        },
                        "404": {
                            "description": "Job or EPUB file not found"
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger_spec)


@app.route('/api/compose', methods=['POST'])
def compose():
    """
    POST /api/compose
    Submit files for EPUB composition
    """
    try:
        # Get jobId from form data
        job_id = request.form.get('jobId')
        if not job_id:
            return jsonify({'error': 'Missing jobId parameter'}), 400
        
        # Check if job already exists
        current_status = get_job_progress(job_id)
        if current_status['status'] == 'completed':
            return jsonify({
                'error': 'Job already completed',
                'jobId': job_id,
                'status': current_status['status']
            }), 409
        elif current_status['status'] == 'processing':
            return jsonify({
                'error': 'Job already in progress', 
                'jobId': job_id,
                'status': current_status['status']
            }), 409

        # Get uploaded files
        files = {}
        for field_name in ['markdownFile', 'originalBook', 'translatedContent']:
            if field_name in request.files:
                file = request.files[field_name]
                if file and file.filename:
                    files[field_name] = file

        if not files:
            return jsonify({'error': 'No files uploaded'}), 400

        # Validate file combinations
        has_single = 'markdownFile' in files
        has_dual = 'originalBook' in files and 'translatedContent' in files
        
        if not (has_single or has_dual):
            return jsonify({
                'error': 'Invalid file combination. Provide either markdownFile for single-language or both originalBook and translatedContent for dual-language composition',
                'received': list(files.keys())
            }), 400

        # Validate file types
        for field_name, file in files.items():
            if not file.filename.lower().endswith('.md'):
                return jsonify({'error': f'{field_name} must be a markdown (.md) file'}), 400

        # Save uploaded files
        try:
            saved_files = save_uploaded_files(job_id, files)
        except Exception as e:
            return jsonify({
                'error': 'Failed to save uploaded files',
                'details': str(e)
            }), 500

        # Determine composer type
        composer_type = request.form.get('composerType', 'auto')
        if composer_type == 'auto':
            if has_dual:
                composer_type = 'real_storage_dual_language'
            else:
                composer_type = 'simple_markdown'

        # Create initial progress file
        storage_root = get_storage_root()
        job_dir = Path(storage_root) / job_id
        progress_file = job_dir / 'composingservice-progress.json'
        
        progress = {
            'book_id': job_id,
            'composer': composer_type,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'message': 'EPUB composition job submitted via API',
            'uploaded_files': saved_files
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

        return jsonify({
            'jobId': job_id,
            'message': 'EPUB composition job submitted successfully. The composing service will process it automatically.',
            'composer': composer_type,
            'uploadedFiles': saved_files
        })

    except Exception as e:
        logger.error(f"Error in compose endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/api/job_status')
def job_status():
    """
    GET /api/job_status?jobId=...
    Get the status of an EPUB composition job
    """
    job_id = request.args.get('jobId')
    if not job_id:
        return jsonify({'error': 'Missing jobId parameter'}), 400

    progress = get_job_progress(job_id)
    return jsonify(progress)


@app.route('/api/download')
def download():
    """
    GET /api/download?jobId=...
    Download the composed EPUB file
    """
    job_id = request.args.get('jobId')
    if not job_id:
        return jsonify({'error': 'Missing jobId parameter'}), 400

    # Check job status
    current_status = get_job_progress(job_id)
    if current_status['status'] == 'not_found':
        return jsonify({'error': 'Job not found'}), 404
    elif current_status['status'] != 'completed':
        return jsonify({
            'error': 'Job not completed',
            'status': current_status['status'],
            'message': current_status['message']
        }), 400

    # Find the output EPUB file
    storage_root = get_storage_root()
    job_dir = Path(storage_root) / job_id
    
    # Prioritize dual-language EPUB if available
    possible_files = [
        job_dir / 'dual-language-final.epub',
        job_dir / 'final.epub'
    ]
    
    output_file = None
    for file_path in possible_files:
        if file_path.exists():
            output_file = file_path
            break
    
    if not output_file:
        return jsonify({
            'error': 'EPUB file not found',
            'message': 'Expected output file not found on disk'
        }), 500

    # Determine download filename
    if 'dual-language' in output_file.name:
        download_filename = f'dual-language-{job_id}.epub'
    else:
        download_filename = f'composed-{job_id}.epub'

    try:
        return send_file(
            str(output_file),
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/epub+zip'
        )
    except Exception as e:
        logger.error(f"Error downloading file {output_file}: {str(e)}")
        return jsonify({
            'error': 'Error downloading file',
            'details': str(e)
        }), 500


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'dc-epub-composer',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3002))  # Different port from other services
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting DC EPUB Composer API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)