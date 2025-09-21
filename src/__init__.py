"""
Xpad to Google Drive Sync Package

Core components for synchronizing xpad notes to Google Drive
for integration with Zapier and iOS Shortcuts.

Author: Robin Kokot
License: 
"""

__version__ = "2.0.0"
__author__ = "Robin Kokot"
__license__ = "MIT"

# Import main classes for easy access
try:
    from .file_monitor import XpadGDriveSync, SyncConfig, load_config
    from .file_monitor import NoteProcessor, GoogleDriveSync
    
    __all__ = [
        'XpadGDriveSync',
        'SyncConfig', 
        'load_config',
        'NoteProcessor',
        'GoogleDriveSync'
    ]
except ImportError:
    __all__ = []