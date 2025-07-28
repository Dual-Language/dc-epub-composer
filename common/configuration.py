import os
import pathlib

def get_storage_root() -> str:
    """Get the storage root directory path."""
    return os.environ.get('STORAGE_ROOT', str(pathlib.Path(__file__).parent.parent.parent / 'storage'))

def get_composer_config() -> dict:
    """Get composer configuration."""
    return {
        'default_composer': os.environ.get('DEFAULT_COMPOSER', 'real_storage_dual_language_markdown'),
        'sleep_interval': int(os.environ.get('SLEEP_INTERVAL', '10')),
        'progress_filename': 'composingservice-progress.json',
        'translated_content_filename': 'translatedcontent.md',
        'final_epub_filename': 'final.epub'
    } 