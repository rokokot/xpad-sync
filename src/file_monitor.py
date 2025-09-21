#!/usr/bin/env python3
"""
Xpad to Google Drive File Monitor

Real-time monitoring of xpad notes with sync to Google Drive folder.
Zapier + iOS Shortcuts architecture.

Author: Robin Kokot
License: 
"""

import os
import sys
import json
import hashlib
import time
import logging
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set
from dataclasses import dataclass
import argparse

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

@dataclass
class SyncConfig:
    """Configuration for the file monitor."""
    xpad_directory: str = "~/.config/xpad"
    gdrive_sync_folder: str = "~/GoogleDrive/XpadSync"
    note_format: str = "markdown"
    enable_realtime: bool = True
    debounce_seconds: float = 2.0
    max_file_size_mb: int = 10
    log_level: str = "INFO"
    
    # File naming configuration
    prefix: str = "xpad_note_"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    include_hash: bool = True
    title_max_length: int = 50
    
    def __post_init__(self):
        """Expand paths and validate config."""
        self.xpad_directory = str(Path(self.xpad_directory).expanduser())
        self.gdrive_sync_folder = str(Path(self.gdrive_sync_folder).expanduser())

class NoteProcessor:
    """Processes and formats xpad note content."""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.logger = logging.getLogger('NoteProcessor')
    
    def extract_title(self, content: str) -> str:
        """Extract meaningful title from note content."""
        if not content.strip():
            return "Untitled Note"
        
        # Get first non-empty line
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if not lines:
            return "Untitled Note"
        
        title = lines[0]
        
        # Remove common markdown formatting
        title = title.lstrip('#').strip()
        title = title.replace('*', '').replace('_', '')
        
        # Clean and truncate
        title = ' '.join(title.split())  # Normalize whitespace
        if len(title) > self.config.title_max_length:
            title = title[:self.config.title_max_length - 3] + "..."
        
        # Sanitize for filename
        title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        title = title.replace(' ', '_')
        
        return title or "Untitled_Note"
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate short hash of content for uniqueness."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
    
    def format_content(self, content: str, source_file: str) -> str:
        """Format content with metadata."""
        timestamp = datetime.now().isoformat()
        
        if self.config.note_format == "markdown":
            formatted = f"""# {self.extract_title(content)}

{content.strip()}

---
*Synced from Xpad*  
*Source: {source_file}*  
*Timestamp: {timestamp}*
"""
        else:
            # Plain text format
            formatted = f"""{content.strip()}

---
Synced from Xpad
Source: {source_file}
Timestamp: {timestamp}
"""
        
        return formatted
    
    def generate_filename(self, content: str, source_file: str) -> str:
        """Generate filename for Google Drive."""
        title = self.extract_title(content)
        timestamp = datetime.now().strftime(self.config.timestamp_format)
        
        filename_parts = [self.config.prefix, title, timestamp]
        
        if self.config.include_hash:
            content_hash = self.calculate_content_hash(content)
            filename_parts.append(content_hash)
        
        extension = ".md" if self.config.note_format == "markdown" else ".txt"
        filename = "_".join(filename_parts) + extension
        
        # Ensure filename isn't too long
        if len(filename) > 200:
            # Truncate title part
            max_title_len = 200 - len(timestamp) - len(content_hash) - 20
            title = title[:max_title_len]
            filename_parts[1] = title
            filename = "_".join(filename_parts) + extension
        
        return filename

class GoogleDriveSync:
    """Manages Google Drive folder synchronization."""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.sync_folder = Path(config.gdrive_sync_folder)
        self.logger = logging.getLogger('GoogleDriveSync')
        
        # Ensure sync folder exists
        self.sync_folder.mkdir(parents=True, exist_ok=True)
        
        # Create metadata tracking
        self.metadata_file = self.sync_folder / ".xpad_sync_metadata.json"
        self.file_registry: Dict[str, dict] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, dict]:
        """Load sync metadata."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """Save sync metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.file_registry, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    def save_note_file(self, content: str, source_file: str, processor: NoteProcessor) -> Optional[str]:
        """Save formatted note to Google Drive sync folder."""
        try:
            # Format content and generate filename
            formatted_content = processor.format_content(content, source_file)
            filename = processor.generate_filename(content, source_file)
            
            # Check file size
            content_size_mb = len(formatted_content.encode('utf-8')) / (1024 * 1024)
            if content_size_mb > self.config.max_file_size_mb:
                self.logger.warning(f"File too large: {content_size_mb:.1f}MB > {self.config.max_file_size_mb}MB")
                return None
            
            # Save file
            output_path = self.sync_folder / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            # Update registry
            content_hash = processor.calculate_content_hash(content)
            self.file_registry[source_file] = {
                "output_file": filename,
                "content_hash": content_hash,
                "last_synced": datetime.now().isoformat(),
                "file_size": len(formatted_content)
            }
            self._save_metadata()
            
            self.logger.info(f"Synced: {source_file} -> {filename}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save {source_file}: {e}")
            return None
    
    def is_content_changed(self, source_file: str, content: str, processor: NoteProcessor) -> bool:
        """Check if content has changed since last sync."""
        if source_file not in self.file_registry:
            return True
        
        current_hash = processor.calculate_content_hash(content)
        stored_hash = self.file_registry[source_file].get("content_hash")
        
        return current_hash != stored_hash
    
    def cleanup_orphaned_files(self, active_sources: Set[str]):
        """Remove files for sources that no longer exist."""
        orphaned = set(self.file_registry.keys()) - active_sources
        
        for source_file in orphaned:
            metadata = self.file_registry[source_file]
            output_file = self.sync_folder / metadata["output_file"]
            
            if output_file.exists():
                try:
                    output_file.unlink()
                    self.logger.info(f"Removed orphaned file: {metadata['output_file']}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {output_file}: {e}")
            
            del self.file_registry[source_file]
        
        if orphaned:
            self._save_metadata()
            self.logger.info(f"Cleaned up {len(orphaned)} orphaned files")

class XpadFileMonitor(FileSystemEventHandler):
    """File system event handler for real-time sync."""
    
    def __init__(self, sync_engine):
        self.sync_engine = sync_engine
        self.logger = logging.getLogger('XpadFileMonitor')
    
    def _is_content_file(self, file_path: str) -> bool:
        """Check if this is an xpad content file."""
        return Path(file_path).name.startswith('content-')
    
    def _schedule_sync(self, file_path: str):
        """Schedule a debounced sync for the file."""
        schedule_time = time.time() + self.sync_engine.config.debounce_seconds
        self.sync_engine.pending_syncs[file_path] = schedule_time
        self.logger.debug(f"Scheduled sync for {file_path}")
    
    def on_modified(self, event):
        if not event.is_directory and self._is_content_file(event.src_path):
            self._schedule_sync(event.src_path)
    
    def on_created(self, event):
        if not event.is_directory and self._is_content_file(event.src_path):
            self._schedule_sync(event.src_path)

class XpadGDriveSync:
    """Main synchronization engine."""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.xpad_path = Path(config.xpad_directory)
        self.processor = NoteProcessor(config)
        self.gdrive_sync = GoogleDriveSync(config)
        
        self.pending_syncs: Dict[str, float] = {}
        self.observer = None
        self.running = False
        
        self._setup_logging()
        self.logger = logging.getLogger('XpadGDriveSync')
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Ensure xpad directory exists
        if not self.xpad_path.exists():
            self.logger.warning(f"Xpad directory not found: {self.xpad_path}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_monitoring()
    
    def _setup_logging(self):
        """Setup logging system."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # File handler
        log_file = self.gdrive_sync.sync_folder / "xpad_sync.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
    
    def discover_notes(self) -> list:
        """Discover all xpad content files."""
        if not self.xpad_path.exists():
            return []
        
        content_files = list(self.xpad_path.glob("content-*"))
        self.logger.debug(f"Discovered {len(content_files)} xpad files")
        return content_files
    
    def sync_note(self, file_path: Path, force: bool = False) -> bool:
        """Sync a single note file."""
        try:
            if not file_path.exists():
                self.logger.debug(f"File no longer exists: {file_path}")
                return False
            
            # Read content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read().strip()
            
            if not content:
                self.logger.debug(f"Skipping empty file: {file_path}")
                return False
            
            # Check if content changed
            source_file = str(file_path)
            if not force and not self.gdrive_sync.is_content_changed(source_file, content, self.processor):
                self.logger.debug(f"Content unchanged: {file_path.name}")
                return True
            
            # Sync to Google Drive
            output_path = self.gdrive_sync.save_note_file(content, source_file, self.processor)
            return output_path is not None
            
        except Exception as e:
            self.logger.error(f"Failed to sync {file_path}: {e}")
            return False
    
    def sync_all_notes(self, force: bool = False) -> dict:
        """Sync all discovered notes."""
        notes = self.discover_notes()
        if not notes:
            self.logger.info("No xpad notes found")
            return {}
        
        self.logger.info(f"Starting sync of {len(notes)} notes")
        results = {}
        
        for note_file in notes:
            results[str(note_file)] = self.sync_note(note_file, force=force)
        
        # Cleanup orphaned files
        active_sources = {str(f) for f in notes}
        self.gdrive_sync.cleanup_orphaned_files(active_sources)
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Sync completed: {successful}/{len(notes)} successful")
        
        return results
    
    def start_monitoring(self):
        """Start real-time file monitoring."""
        if not self.config.enable_realtime:
            self.logger.info("Real-time monitoring disabled")
            return
        
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("Watchdog not available, real-time monitoring disabled")
            return
        
        try:
            event_handler = XpadFileMonitor(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.xpad_path), recursive=False)
            self.observer.start()
            self.running = True
            
            self.logger.info(f"File monitoring started for {self.xpad_path}")
            
            # Main loop for processing pending syncs
            while self.running:
                self._process_pending_syncs()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop file monitoring."""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.logger.info("File monitoring stopped")
    
    def _process_pending_syncs(self):
        """Process any pending debounced syncs."""
        if not self.pending_syncs:
            return
        
        current_time = time.time()
        ready_files = [
            file_path for file_path, scheduled_time in self.pending_syncs.items()
            if current_time >= scheduled_time
        ]
        
        for file_path in ready_files:
            del self.pending_syncs[file_path]
            
            path_obj = Path(file_path)
            if self.sync_note(path_obj):
                self.logger.info(f"Real-time sync: {path_obj.name}")

def load_config(config_path: str = "~/.xpad_gdrive_config.json") -> SyncConfig:
    """Load configuration from file."""
    config_file = Path(config_path).expanduser()
    
    if not config_file.exists():
        # Create default config
        default_config = {
            "xpad_directory": "~/.config/xpad",
            "gdrive_sync_folder": "~/GoogleDrive/XpadSync",
            "note_format": "markdown",
            "enable_realtime": True,
            "debounce_seconds": 2.0,
            "log_level": "INFO"
        }
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"Created default config at {config_file}")
        print("Edit the configuration file and run again.")
        sys.exit(0)
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        return SyncConfig(**config_data)
    except Exception as e:
        print(f"Failed to load config from {config_file}: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Xpad to Google Drive Sync')
    parser.add_argument('command', choices=['sync', 'monitor', 'status'], 
                       help='Command to execute')
    parser.add_argument('--config', '-c', default='~/.xpad_gdrive_config.json',
                       help='Configuration file path')
    parser.add_argument('--force', action='store_true',
                       help='Force sync all notes')
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        sync_engine = XpadGDriveSync(config)
        
        if args.command == 'sync':
            print("Running one-time sync...")
            results = sync_engine.sync_all_notes(force=args.force)
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            print(f"Sync completed: {successful}/{total} successful")
            
        elif args.command == 'monitor':
            print("Starting real-time monitoring...")
            print("Press Ctrl+C to stop")
            # Initial sync
            sync_engine.sync_all_notes()
            # Start monitoring
            sync_engine.start_monitoring()
            
        elif args.command == 'status':
            print("Xpad to Google Drive Sync Status")
            print("=" * 40)
            
            # Check directories
            xpad_exists = Path(config.xpad_directory).exists()
            gdrive_exists = Path(config.gdrive_sync_folder).exists()
            
            print(f"Xpad directory: {config.xpad_directory}")
            print(f"  Status: {'✓ EXISTS' if xpad_exists else '✗ NOT FOUND'}")
            
            print(f"Google Drive sync folder: {config.gdrive_sync_folder}")
            print(f"  Status: {'✓ EXISTS' if gdrive_exists else '✗ NOT FOUND'}")
            
            if xpad_exists:
                notes = sync_engine.discover_notes()
                print(f"  Xpad notes found: {len(notes)}")
            
            if gdrive_exists:
                synced_files = list(Path(config.gdrive_sync_folder).glob("xpad_note_*"))
                print(f"  Synced files: {len(synced_files)}")
            
            print(f"Real-time monitoring: {'ENABLED' if config.enable_realtime else 'DISABLED'}")
            print(f"Watchdog available: {'YES' if WATCHDOG_AVAILABLE else 'NO'}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())