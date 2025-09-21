#!/usr/bin/env python3
"""
Test Suite for File Monitor

Tests the core file monitoring and sync functionality.
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from file_monitor import (
    SyncConfig, NoteProcessor, GoogleDriveSync, 
    XpadGDriveSync, load_config
)

class TestSyncConfig(unittest.TestCase):
    """Test configuration handling."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SyncConfig()
        self.assertEqual(config.note_format, "markdown")
        self.assertTrue(config.enable_realtime)
        self.assertEqual(config.debounce_seconds, 2.0)
    
    def test_config_path_expansion(self):
        """Test path expansion in configuration."""
        config = SyncConfig(
            xpad_directory="~/test_xpad",
            gdrive_sync_folder="~/test_gdrive"
        )
        
        # Paths should be expanded
        self.assertNotIn("~", config.xpad_directory)
        self.assertNotIn("~", config.gdrive_sync_folder)
    
    def test_invalid_config(self):
        """Test configuration validation."""
        # These should not raise exceptions for now
        # Future versions may add validation
        config = SyncConfig(debounce_seconds=-1)
        self.assertEqual(config.debounce_seconds, -1)

class TestNoteProcessor(unittest.TestCase):
    """Test note content processing."""
    
    def setUp(self):
        self.config = SyncConfig()
        self.processor = NoteProcessor(self.config)
    
    def test_extract_title_simple(self):
        """Test title extraction from simple content."""
        content = "Simple Note Title\n\nThis is the content."
        title = self.processor.extract_title(content)
        self.assertEqual(title, "Simple_Note_Title")
    
    def test_extract_title_markdown(self):
        """Test title extraction from markdown content."""
        content = "# Markdown Title\n\nContent here."
        title = self.processor.extract_title(content)
        self.assertEqual(title, "Markdown_Title")
    
    def test_extract_title_empty(self):
        """Test title extraction from empty content."""
        content = ""
        title = self.processor.extract_title(content)
        self.assertEqual(title, "Untitled Note")
    
    def test_extract_title_long(self):
        """Test title truncation for long titles."""
        long_content = "This is a very long title that exceeds the maximum length limit" * 2
        title = self.processor.extract_title(long_content)
        self.assertTrue(len(title) <= self.config.title_max_length + 3)  # +3 for "..."
        self.assertTrue(title.endswith("..."))
    
    def test_calculate_content_hash(self):
        """Test content hash calculation."""
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"
        
        hash1 = self.processor.calculate_content_hash(content1)
        hash2 = self.processor.calculate_content_hash(content2)
        hash3 = self.processor.calculate_content_hash(content3)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 8)  # Short hash
    
    def test_format_content_markdown(self):
        """Test markdown content formatting."""
        content = "Test Note\n\nThis is a test."
        source_file = "/path/to/test"
        
        formatted = self.processor.format_content(content, source_file)
        
        self.assertIn("# Test_Note", formatted)
        self.assertIn("This is a test.", formatted)
        self.assertIn("Synced from Xpad", formatted)
        self.assertIn(source_file, formatted)
    
    def test_format_content_plain(self):
        """Test plain text content formatting."""
        self.config.note_format = "plain"
        processor = NoteProcessor(self.config)
        
        content = "Test Note\n\nThis is a test."
        source_file = "/path/to/test"
        
        formatted = processor.format_content(content, source_file)
        
        self.assertNotIn("#", formatted)  # No markdown headers
        self.assertIn("This is a test.", formatted)
        self.assertIn("Synced from Xpad", formatted)
    
    def test_generate_filename(self):
        """Test filename generation."""
        content = "Test Note\n\nContent here."
        source_file = "/path/to/source"
        
        filename = self.processor.generate_filename(content, source_file)
        
        self.assertTrue(filename.startswith("xpad_note_"))
        self.assertTrue(filename.endswith(".md"))
        self.assertIn("Test_Note", filename)

class TestGoogleDriveSync(unittest.TestCase):
    """Test Google Drive synchronization."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = SyncConfig(gdrive_sync_folder=self.temp_dir)
        self.gdrive_sync = GoogleDriveSync(self.config)
        self.processor = NoteProcessor(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_metadata_loading(self):
        """Test metadata file loading."""
        # Should start with empty metadata
        self.assertEqual(len(self.gdrive_sync.file_registry), 0)
        
        # Create metadata file
        metadata = {
            "test_file": {
                "content_hash": "abc123",
                "last_synced": "2024-01-01T12:00:00"
            }
        }
        
        metadata_file = Path(self.temp_dir) / ".xpad_sync_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Reload
        gdrive_sync = GoogleDriveSync(self.config)
        self.assertEqual(len(gdrive_sync.file_registry), 1)
        self.assertIn("test_file", gdrive_sync.file_registry)
    
    def test_save_note_file(self):
        """Test saving note file to Google Drive."""
        content = "Test note content"
        source_file = "/test/source"
        
        output_path = self.gdrive_sync.save_note_file(content, source_file, self.processor)
        
        self.assertIsNotNone(output_path)
        self.assertTrue(Path(output_path).exists())
        
        # Check metadata was updated
        self.assertIn(source_file, self.gdrive_sync.file_registry)
    
    def test_is_content_changed(self):
        """Test content change detection."""
        content = "Test content"
        source_file = "/test/source"
        
        # First time should be considered changed
        self.assertTrue(self.gdrive_sync.is_content_changed(source_file, content, self.processor))
        
        # Save the file
        self.gdrive_sync.save_note_file(content, source_file, self.processor)
        
        # Same content should not be changed
        self.assertFalse(self.gdrive_sync.is_content_changed(source_file, content, self.processor))
        
        # Different content should be changed
        new_content = "Different content"
        self.assertTrue(self.gdrive_sync.is_content_changed(source_file, new_content, self.processor))
    
    def test_cleanup_orphaned_files(self):
        """Test cleanup of orphaned files."""
        # Create some test files and metadata
        content = "Test content"
        source_file1 = "/test/source1"
        source_file2 = "/test/source2"
        
        self.gdrive_sync.save_note_file(content, source_file1, self.processor)
        self.gdrive_sync.save_note_file(content, source_file2, self.processor)
        
        # Both should be in registry
        self.assertEqual(len(self.gdrive_sync.file_registry), 2)
        
        # Cleanup with only one active source
        active_sources = {source_file1}
        self.gdrive_sync.cleanup_orphaned_files(active_sources)
        
        # Should only have one left
        self.assertEqual(len(self.gdrive_sync.file_registry), 1)
        self.assertIn(source_file1, self.gdrive_sync.file_registry)
        self.assertNotIn(source_file2, self.gdrive_sync.file_registry)

class TestXpadGDriveSync(unittest.TestCase):
    """Test main sync engine."""
    
    def setUp(self):
        self.temp_xpad = tempfile.mkdtemp()
        self.temp_gdrive = tempfile.mkdtemp()
        
        self.config = SyncConfig(
            xpad_directory=self.temp_xpad,
            gdrive_sync_folder=self.temp_gdrive,
            enable_realtime=False  # Disable for testing
        )
        
        # Mock logging to avoid file creation issues in tests
        with patch('file_monitor.logging'):
            self.sync_engine = XpadGDriveSync(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_xpad)
        shutil.rmtree(self.temp_gdrive)
    
    def test_discover_notes_empty(self):
        """Test note discovery with no notes."""
        notes = self.sync_engine.discover_notes()
        self.assertEqual(len(notes), 0)
    
    def test_discover_notes_with_files(self):
        """Test note discovery with xpad files."""
        # Create some test xpad files
        (Path(self.temp_xpad) / "content-1").write_text("Note 1")
        (Path(self.temp_xpad) / "content-2").write_text("Note 2")
        (Path(self.temp_xpad) / "info-1").write_text("Info file")  # Should be ignored
        
        notes = self.sync_engine.discover_notes()
        self.assertEqual(len(notes), 2)
        
        # Should only find content files
        note_names = [note.name for note in notes]
        self.assertIn("content-1", note_names)
        self.assertIn("content-2", note_names)
        self.assertNotIn("info-1", note_names)
    
    def test_sync_note_success(self):
        """Test successful note synchronization."""
        # Create test note
        note_file = Path(self.temp_xpad) / "content-test"
        note_file.write_text("Test note content\n\nThis is a test.")
        
        result = self.sync_engine.sync_note(note_file)
        self.assertTrue(result)
        
        # Check that file was created in Google Drive folder
        gdrive_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(gdrive_files), 1)
    
    def test_sync_note_empty_file(self):
        """Test sync with empty file."""
        note_file = Path(self.temp_xpad) / "content-empty"
        note_file.write_text("")
        
        result = self.sync_engine.sync_note(note_file)
        self.assertFalse(result)  # Should skip empty files
    
    def test_sync_note_nonexistent_file(self):
        """Test sync with nonexistent file."""
        note_file = Path(self.temp_xpad) / "content-missing"
        
        result = self.sync_engine.sync_note(note_file)
        self.assertFalse(result)
    
    def test_sync_all_notes(self):
        """Test syncing all notes."""
        # Create test notes
        (Path(self.temp_xpad) / "content-1").write_text("Note 1 content")
        (Path(self.temp_xpad) / "content-2").write_text("Note 2 content")
        (Path(self.temp_xpad) / "content-empty").write_text("")  # Empty, should be skipped
        
        results = self.sync_engine.sync_all_notes()
        
        # Should have attempted to sync 3 files
        self.assertEqual(len(results), 3)
        
        # 2 should have succeeded, 1 failed (empty)
        successful = sum(1 for success in results.values() if success)
        self.assertEqual(successful, 2)

class TestConfigLoading(unittest.TestCase):
    """Test configuration file loading."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_load_existing_config(self):
        """Test loading existing configuration."""
        config_data = {
            "xpad_directory": "/test/xpad",
            "gdrive_sync_folder": "/test/gdrive",
            "note_format": "plain",
            "enable_realtime": False
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = load_config(str(self.config_file))
        
        self.assertEqual(config.note_format, "plain")
        self.assertFalse(config.enable_realtime)
    
    def test_load_nonexistent_config(self):
        """Test loading nonexistent configuration."""
        nonexistent_file = self.temp_dir + "/missing_config.json"
        
        # Should exit with SystemExit
        with self.assertRaises(SystemExit):
            load_config(nonexistent_file)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        self.temp_xpad = tempfile.mkdtemp()
        self.temp_gdrive = tempfile.mkdtemp()
        
        self.config = SyncConfig(
            xpad_directory=self.temp_xpad,
            gdrive_sync_folder=self.temp_gdrive,
            enable_realtime=False
        )
        
        with patch('file_monitor.logging'):
            self.sync_engine = XpadGDriveSync(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_xpad)
        shutil.rmtree(self.temp_gdrive)
    
    def test_complete_workflow(self):
        """Test complete sync workflow."""
        # 1. Create xpad note
        note_content = """Meeting Notes
        
        Discussed project timeline
        - Phase 1: Complete by March
        - Phase 2: Start in April
        
        TODO: Follow up with team
        """
        
        note_file = Path(self.temp_xpad) / "content-meeting"
        note_file.write_text(note_content)
        
        # 2. Run sync
        results = self.sync_engine.sync_all_notes()
        self.assertTrue(results[str(note_file)])
        
        # 3. Verify output file exists
        output_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(output_files), 1)
        
        output_file = output_files[0]
        
        # 4. Verify content formatting
        with open(output_file, 'r') as f:
            synced_content = f.read()
        
        self.assertIn("# Meeting_Notes", synced_content)
        self.assertIn("Discussed project timeline", synced_content)
        self.assertIn("Synced from Xpad", synced_content)
        self.assertIn("content-meeting", synced_content)
        
        # 5. Test that subsequent sync with no changes is skipped
        results2 = self.sync_engine.sync_all_notes()
        self.assertTrue(results2[str(note_file)])  # Still successful, but no actual sync
        
        # 6. Modify note and verify it syncs again
        modified_content = note_content + "\n\nUpdated content"
        note_file.write_text(modified_content)
        
        results3 = self.sync_engine.sync_all_notes()
        self.assertTrue(results3[str(note_file)])
        
        # Should now have 2 files (original + updated)
        output_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(output_files), 2)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)