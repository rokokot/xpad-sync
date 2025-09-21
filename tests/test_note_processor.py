#!/usr/bin/env python3
"""
Test Suite for Note Processor

Focused tests on note content processing and formatting.
"""

import unittest
from datetime import datetime
from pathlib import Path
import sys

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from file_monitor import SyncConfig, NoteProcessor

class TestNoteProcessorAdvanced(unittest.TestCase):
    """Advanced tests for note processing functionality."""
    
    def setUp(self):
        self.config = SyncConfig()
        self.processor = NoteProcessor(self.config)
    
    def test_title_extraction_edge_cases(self):
        """Test title extraction with various edge cases."""
        test_cases = [
            # Input, Expected Output
            ("", "Untitled Note"),
            ("   ", "Untitled Note"),
            ("\n\n\n", "Untitled Note"),
            ("Single word", "Single_word"),
            ("Multiple    spaces    here", "Multiple_spaces_here"),
            ("# Markdown Header", "Markdown_Header"),
            ("## Second Level Header", "Second_Level_Header"),
            ("### Third Level", "Third_Level"),
            ("*Bold* and _italic_ text", "Bold_and_italic_text"),
            ("**Double bold** text", "Double_bold_text"),
            ("Line with\nnewlines\nhere", "Line_with"),
            ("!@#$%^&*()Special chars", "Special_chars"),
            ("Numbers 123 and symbols !", "Numbers_123_and_symbols"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.extract_title(input_text)
                self.assertEqual(result, expected)
    
    def test_title_length_limits(self):
        """Test title length limiting."""
        # Test exactly at limit
        exact_limit = "a" * self.config.title_max_length
        result = self.processor.extract_title(exact_limit)
        self.assertEqual(len(result), self.config.title_max_length)
        
        # Test over limit
        over_limit = "a" * (self.config.title_max_length + 10)
        result = self.processor.extract_title(over_limit)
        self.assertTrue(len(result) <= self.config.title_max_length + 3)  # +3 for "..."
        self.assertTrue(result.endswith("..."))
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        unicode_cases = [
            ("Café notes", "Caf_notes"),
            ("日本語 notes", "_notes"),  # Non-ASCII chars filtered out
            ("Émojis 🚀 and symbols", "mojis_and_symbols"),
            ("Ñoño título", "oo_ttulo"),
        ]
        
        for input_text, expected in unicode_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.extract_title(input_text)
                # Check that result contains only allowed characters
                allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_')
                self.assertTrue(all(c in allowed_chars for c in result))
    
    def test_content_hash_consistency(self):
        """Test that content hashing is consistent."""
        content = "Test content for hashing"
        
        # Same content should produce same hash
        hash1 = self.processor.calculate_content_hash(content)
        hash2 = self.processor.calculate_content_hash(content)
        self.assertEqual(hash1, hash2)
        
        # Different content should produce different hash
        different_content = "Different test content"
        hash3 = self.processor.calculate_content_hash(different_content)
        self.assertNotEqual(hash1, hash3)
        
        # Hash should be 8 characters
        self.assertEqual(len(hash1), 8)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
    
    def test_markdown_formatting(self):
        """Test markdown content formatting."""
        self.config.note_format = "markdown"
        processor = NoteProcessor(self.config)
        
        content = """Project Meeting Notes

Attendees: John, Jane, Bob
Date: March 15, 2024

## Discussion Points
- Budget approval needed
- Timeline review
- Next steps

### Action Items
1. John: Review budget by Friday
2. Jane: Update timeline document
3. Bob: Schedule follow-up meeting

## Notes
Great progress on Phase 1.
Need to accelerate Phase 2.

TODO: Send meeting summary to team"""
        
        source_file = "/home/user/.config/xpad/content-meeting-123"
        formatted = processor.format_content(content, source_file)
        
        # Check structure
        self.assertTrue(formatted.startswith("# Project_Meeting_Notes"))
        self.assertIn("## Discussion Points", formatted)
        self.assertIn("### Action Items", formatted)
        self.assertIn("---", formatted)
        self.assertIn("*Synced from Xpad*", formatted)
        self.assertIn("content-meeting-123", formatted)
        
        # Check that original content is preserved
        self.assertIn("Attendees: John, Jane, Bob", formatted)
        self.assertIn("TODO: Send meeting summary", formatted)
    
    def test_plain_text_formatting(self):
        """Test plain text content formatting."""
        self.config.note_format = "plain"
        processor = NoteProcessor(self.config)
        
        content = "Simple note\n\nWith some content."
        source_file = "/path/to/source"
        formatted = processor.format_content(content, source_file)
        
        # Should not have markdown formatting
        self.assertNotIn("#", formatted)
        self.assertNotIn("*", formatted)
        
        # Should have metadata
        self.assertIn("Synced from Xpad", formatted)
        self.assertIn("---", formatted)
        self.assertIn("Simple note", formatted)
    
    def test_filename_generation_components(self):
        """Test filename generation with different components."""
        content = "Test Note Title\n\nContent here."
        source_file = "/path/to/content-123"
        
        filename = self.processor.generate_filename(content, source_file)
        
        # Check filename structure
        parts = filename.split('_')
        self.assertEqual(parts[0], "xpad")
        self.assertEqual(parts[1], "note")
        self.assertEqual(parts[2], "Test")
        self.assertEqual(parts[3], "Note")
        self.assertEqual(parts[4], "Title")
        
        # Should have timestamp
        timestamp_part = parts[5]  # YYYYMMDD
        self.assertEqual(len(timestamp_part), 8)
        self.assertTrue(timestamp_part.isdigit())
        
        # Should have time part
        time_part = parts[6]  # HHMMSS
        self.assertEqual(len(time_part), 6)
        self.assertTrue(time_part.isdigit())
        
        # Should have hash if enabled
        if self.config.include_hash:
            hash_part = parts[7].split('.')[0]  # Remove extension
            self.assertEqual(len(hash_part), 8)
        
        # Should have correct extension
        self.assertTrue(filename.endswith('.md'))
    
    def test_filename_generation_no_hash(self):
        """Test filename generation without hash."""
        self.config.include_hash = False
        processor = NoteProcessor(self.config)
        
        content = "Test Note"
        source_file = "/path/to/source"
        filename = processor.generate_filename(content, source_file)
        
        # Should not contain 8-character hash at the end
        parts = filename.replace('.md', '').split('_')
        # Should have: xpad, note, Test, Note, YYYYMMDD, HHMMSS
        self.assertEqual(len(parts), 6)
    
    def test_filename_length_limiting(self):
        """Test filename length limiting."""
        # Create very long title
        long_title = "Very " * 50 + "Long Title"
        content = f"{long_title}\n\nContent."
        source_file = "/path/to/source"
        
        filename = self.processor.generate_filename(content, source_file)
        
        # Filename should not be excessively long
        self.assertLess(len(filename), 250)  # Reasonable limit
    
    def test_special_characters_in_filename(self):
        """Test handling of special characters in filename generation."""
        special_content = """File/Path\\Name: Special?*<>|"Characters!
        
        Content with various symbols: @#$%^&*()"""
        
        source_file = "/path/to/source"
        filename = self.processor.generate_filename(special_content, source_file)
        
        # Should only contain safe filename characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
        self.assertTrue(all(c in safe_chars for c in filename))
    
    def test_empty_content_handling(self):
        """Test handling of empty or whitespace-only content."""
        empty_cases = ["", "   ", "\n\n\n", "\t\t"]
        
        for content in empty_cases:
            with self.subTest(content=repr(content)):
                title = self.processor.extract_title(content)
                self.assertEqual(title, "Untitled_Note")
                
                filename = self.processor.generate_filename(content, "/source")
                self.assertIn("Untitled_Note", filename)
    
    def test_timestamp_consistency(self):
        """Test that timestamps in content and filename are consistent."""
        content = "Test note"
        source_file = "/path/to/source"
        
        # Generate content and filename close together
        formatted_content = self.processor.format_content(content, source_file)
        filename = self.processor.generate_filename(content, source_file)
        
        # Extract timestamp from filename
        parts = filename.split('_')
        filename_timestamp = parts[5] + '_' + parts[6]  # YYYYMMDD_HHMMSS
        
        # Both should be from approximately the same time
        # (allowing for small differences due to execution time)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Should be within same minute
        self.assertEqual(filename_timestamp[:11], current_time[:11])  # YYYYMMDD_HH
    
    def test_metadata_inclusion(self):
        """Test that metadata is properly included in formatted content."""
        content = "Test note content"
        source_file = "/home/user/.config/xpad/content-abc123"
        
        formatted = self.processor.format_content(content, source_file)
        
        # Should include source file
        self.assertIn("content-abc123", formatted)
        
        # Should include timestamp
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(current_date, formatted)
        
        # Should include sync attribution
        self.assertIn("Synced from Xpad", formatted)
        
        # Should have metadata separator
        self.assertIn("---", formatted)

class TestNoteProcessorConfiguration(unittest.TestCase):
    """Test note processor with different configurations."""
    
    def test_custom_prefix(self):
        """Test custom filename prefix."""
        config = SyncConfig(prefix="custom_prefix_")
        processor = NoteProcessor(config)
        
        filename = processor.generate_filename("Test", "/source")
        self.assertTrue(filename.startswith("custom_prefix_"))
    
    def test_custom_timestamp_format(self):
        """Test custom timestamp format."""
        config = SyncConfig(timestamp_format="%Y-%m-%d")
        processor = NoteProcessor(config)
        
        filename = processor.generate_filename("Test", "/source")
        
        # Should contain date in YYYY-MM-DD format
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(current_date, filename)
    
    def test_custom_title_length(self):
        """Test custom title length limit."""
        config = SyncConfig(title_max_length=10)
        processor = NoteProcessor(config)
        
        long_title = "This is a very long title"
        result = processor.extract_title(long_title)
        
        # Should be truncated to 10 + 3 characters max
        self.assertLessEqual(len(result), 13)

if __name__ == '__main__':
    unittest.main(verbosity=2)