#!/usr/bin/env python3
"""
Xpad to Google Drive Sync - Main Executable

Clean wrapper script for the file monitor functionality.
Handles path resolution and provides a consistent CLI interface.

Author: Robin Kokot  
License: GPL v2
"""

import sys
import os
from pathlib import Path

def find_src_directory():
    """Find the src directory relative to this script."""
    script_path = Path(__file__).resolve()
    
    # Check if we're in the development tree
    dev_src = script_path.parent.parent / "src"
    if dev_src.exists() and (dev_src / "file_monitor.py").exists():
        return dev_src
    
    # Check if we're in an installed location
    # Look for src in parent directories
    current = script_path.parent
    for _ in range(3):  # Search up to 3 levels
        src_candidate = current / "src"
        if src_candidate.exists() and (src_candidate / "file_monitor.py").exists():
            return src_candidate
        current = current.parent
    
    # Look in system-wide locations
    system_locations = [
        Path("/usr/local/share/xpad-gdrive-sync/src"),
        Path("/usr/share/xpad-gdrive-sync/src"),
        Path.home() / ".local/share/xpad-gdrive-sync/src"
    ]
    
    for location in system_locations:
        if location.exists() and (location / "file_monitor.py").exists():
            return location
    
    return None

def main():
    """Main entry point with proper error handling."""
    # Find and add src directory to Python path
    src_dir = find_src_directory()
    
    if src_dir is None:
        print("Error: Cannot find xpad-gdrive-sync source files", file=sys.stderr)
        print("Make sure the installation completed successfully", file=sys.stderr)
        print("", file=sys.stderr)
        print("Searched in:", file=sys.stderr)
        print("  - Development tree: ../src/", file=sys.stderr)
        print("  - System locations: /usr/local/share, /usr/share, ~/.local/share", file=sys.stderr)
        sys.exit(1)
    
    # Add src directory to Python path
    sys.path.insert(0, str(src_dir))
    
    # Import and run the main function
    try:
        from file_monitor import main as file_monitor_main
        return file_monitor_main()
    except ImportError as e:
        print(f"Error: Cannot import file_monitor module: {e}", file=sys.stderr)
        print(f"Source directory: {src_dir}", file=sys.stderr)
        print("Make sure all required Python packages are installed:", file=sys.stderr)
        print("  pip3 install --user watchdog", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())