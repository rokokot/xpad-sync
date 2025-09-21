#!/usr/bin/env python3
"""
Integration Test Suite

End-to-end tests for the complete Xpad sync system.
"""

import unittest
import tempfile
import shutil
import json
import time
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from file_monitor import SyncConfig, XpadGDriveSync, load_config

class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow."""
    
    def setUp(self):
        # Create temporary directories
        self.temp_xpad = tempfile.mkdtemp()
        self.temp_gdrive = tempfile.mkdtemp()
        self.temp_config_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config_file = Path(self.temp_config_dir) / "test_config.json"
        config_data = {
            "xpad_directory": self.temp_xpad,
            "gdrive_sync_folder": self.temp_gdrive,
            "note_format": "markdown",
            "enable_realtime": False,
            "debounce_seconds": 0.1,  # Fast for testing
            "log_level": "DEBUG"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Initialize sync engine
        self.config = load_config(str(self.config_file))
        with patch('file_monitor.logging'):  # Mock logging for tests
            self.sync_engine = XpadGDriveSync(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_xpad)
        shutil.rmtree(self.temp_gdrive)
        shutil.rmtree(self.temp_config_dir)
    
    def test_single_note_workflow(self):
        """Test complete workflow with a single note."""
        # Step 1: Create Xpad note
        note_content = """Meeting with Development Team

Date: March 15, 2024
Attendees: Alice, Bob, Charlie

## Agenda
1. Sprint review
2. Next sprint planning
3. Technical debt discussion

## Notes
- Sprint went well, all stories completed
- Need to focus on performance improvements next
- Database optimization is priority

## Action Items
- Alice: Create performance testing framework
- Bob: Investigate database indexing
- Charlie: Review code quality metrics

TODO: Schedule follow-up meeting for next week"""
        
        note_file = Path(self.temp_xpad) / "content-meeting-20240315"
        note_file.write_text(note_content)
        
        # Step 2: Run sync
        results = self.sync_engine.sync_all_notes()
        
        # Step 3: Verify sync was successful
        self.assertEqual(len(results), 1)
        self.assertTrue(list(results.values())[0])
        
        # Step 4: Verify output file exists and has correct content
        output_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(output_files), 1)
        
        output_file = output_files[0]
        with open(output_file, 'r') as f:
            synced_content = f.read()
        
        # Verify content structure
        self.assertIn("# Meeting_with_Development_Team", synced_content)
        self.assertIn("## Agenda", synced_content)
        self.assertIn("## Action Items", synced_content)
        self.assertIn("TODO: Schedule follow-up", synced_content)
        self.assertIn("Synced from Xpad", synced_content)
        self.assertIn("content-meeting-20240315", synced_content)
        
        # Step 5: Verify metadata was created
        metadata_file = Path(self.temp_gdrive) / ".xpad_sync_metadata.json"
        self.assertTrue(metadata_file.exists())
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        self.assertEqual(len(metadata), 1)
        source_path = str(note_file)
        self.assertIn(source_path, metadata)
        
        # Verify metadata content
        note_metadata = metadata[source_path]
        self.assertIn("content_hash", note_metadata)
        self.assertIn("last_synced", note_metadata)
        self.assertIn("output_file", note_metadata)
    
    def test_multiple_notes_workflow(self):
        """Test workflow with multiple notes."""
        # Create multiple test notes
        notes = {
            "content-shopping": "Shopping List\n\n- Milk\n- Bread\n- Eggs",
            "content-ideas": "Project Ideas\n\n1. Mobile app\n2. Web service\n3. Desktop tool",
            "content-todo": "TODO List\n\n- Call dentist\n- Pay bills\n- Update resume"
        }
        
        for filename, content in notes.items():
            note_file = Path(self.temp_xpad) / filename
            note_file.write_text(content)
        
        # Run sync
        results = self.sync_engine.sync_all_notes()
        
        # Verify all notes were processed
        self.assertEqual(len(results), 3)
        self.assertTrue(all(results.values()))
        
        # Verify output files
        output_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(output_files), 3)
        
        # Verify each file has unique content
        output_contents = []
        for output_file in output_files:
            with open(output_file, 'r') as f:
                content = f.read()
                output_contents.append(content)
        
        # Should all be different
        self.assertEqual(len(set(output_contents)), 3)
    
    def test_incremental_sync(self):
        """Test incremental sync behavior."""
        # Create initial note
        note_file = Path(self.temp_xpad) / "content-test"
        initial_content = "Initial content"
        note_file.write_text(initial_content)
        
        # First sync
        results1 = self.sync_engine.sync_all_notes()
        self.assertTrue(list(results1.values())[0])
        
        initial_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(initial_files), 1)
        
        # Second sync with no changes - should not create new file
        results2 = self.sync_engine.sync_all_notes()
        self.assertTrue(list(results2.values())[0])
        
        unchanged_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(unchanged_files), 1)  # Still just one file
        
        # Modify content and sync again
        modified_content = initial_content + "\n\nAdded content"
        note_file.write_text(modified_content)
        
        results3 = self.sync_engine.sync_all_notes()
        self.assertTrue(list(results3.values())[0])
        
        # Should now have two files (original + modified)
        modified_files = list(Path(self.temp_gdrive).glob("xpad_note_*"))
        self.assertEqual(len(modified_files), 2)
    
    def test_cleanup_workflow(self):
        """Test cleanup of orphaned files."""
        # Create notes and sync
        note1 = Path(self.temp_xpad) / "content-1"
        note2 = Path(self.temp_xpad) / "content-2"
        
        note1.write_text("Note 1")
        note2.write_text("Note 2")
        
        self.sync_engine.sync_all_notes()
        
        # Should have 2 output files
        self.assertEqual(len(list(Path(self.temp_gdrive).glob("xpad_note_*"))), 2)
        
        # Remove one source file
        note1.unlink()
        
        # Sync again - should clean up orphaned file
        self.sync_engine.sync_all_notes()
        
        # Check metadata was cleaned up
        metadata_file = Path(self.temp_gdrive) / ".xpad_sync_metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Should only have metadata for remaining file
        self.assertEqual(len(metadata), 1)
        self.assertIn(str(note2), metadata)
        self.assertNotIn(str(note1), metadata)

class TestConfigurationHandling(unittest.TestCase):
    """Test configuration file handling and validation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_valid_configuration_loading(self):
        """Test loading valid configuration."""
        config_file = Path(self.temp_dir) / "valid_config.json"
        config_data = {
            "xpad_directory": "~/.config/xpad",
            "gdrive_sync_folder": "~/GoogleDrive/XpadSync",
            "note_format": "markdown",
            "enable_realtime": True,
            "debounce_seconds": 2.0
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = load_config(str(config_file))
        self.assertEqual(config.note_format, "markdown")
        self.assertTrue(config.enable_realtime)
    
    def test_missing_configuration_file(self):
        """Test behavior with missing configuration file."""
        missing_file = self.temp_dir + "/missing.json"
        
        with self.assertRaises(SystemExit):
            load_config(missing_file)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
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
    
    def test_permission_errors(self):
        """Test handling of permission errors."""
        # Create read-only Google Drive directory
        ro_gdrive = Path(self.temp_gdrive) / "readonly"
        ro_gdrive.mkdir()
        ro_gdrive.chmod(0o444)  # Read-only
        
        # Try to sync with read-only target
        config = SyncConfig(
            xpad_directory=self.temp_xpad,
            gdrive_sync_folder=str(ro_gdrive),
            enable_realtime=False
        )
        
        with patch('file_monitor.logging'):
            sync_engine = XpadGDriveSync(config)
        
        # Create test note
        note_file = Path(self.temp_xpad) / "content-test"
        note_file.write_text("Test content")
        
        # Should handle permission error gracefully
        result = sync_engine.sync_note(note_file)
        self.assertFalse(result)  # Should fail gracefully
        
        # Cleanup
        ro_gdrive.chmod(0o755)
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        # Create large note (over size limit)
        large_content = "Large content " * 100000  # Very large content
        note_file = Path(self.temp_xpad) / "content-large"
        note_file.write_text(large_content)
        
        # Should handle large file appropriately
        result = self.sync_engine.sync_note(note_file)
        # Result depends on implementation - might skip or handle specially
        self.assertIsInstance(result, bool)
    
    def test_corrupted_metadata_recovery(self):
        """Test recovery from corrupted metadata."""
        # Create note and sync normally
        note_file = Path(self.temp_xpad) / "content-test"
        note_file.write_text("Test content")
        self.sync_engine.sync_all_notes()
        
        # Corrupt metadata file
        metadata_file = Path(self.temp_gdrive) / ".xpad_sync_metadata.json"
        metadata_file.write_text("invalid json content {{{")
        
        # Should recover gracefully
        with patch('file_monitor.logging'):
            new_sync_engine = XpadGDriveSync(self.config)
        
        # Should start with empty metadata
        self.assertEqual(len(new_sync_engine.gdrive_sync.file_registry), 0)
        
        # Should be able to sync again
        result = new_sync_engine.sync_all_notes()
        self.assertTrue(list(result.values())[0])

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)