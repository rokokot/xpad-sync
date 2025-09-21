#!/usr/bin/env python3
"""
Xpad to Google Drive Sync Diagnostics

Comprehensive health checks and troubleshooting tools.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def check_system_dependencies():
    """Check system dependencies and requirements."""
    print("System Dependencies")
    print("=" * 50)
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python: {python_version}")
    
    if sys.version_info < (3, 7):
        print("⚠ WARNING: Python 3.7+ recommended")
    
    # Watchdog
    try:
        import watchdog
        print(f"✓ Watchdog: {watchdog.__version__}")
    except ImportError:
        print("✗ Watchdog: Not installed (pip3 install --user watchdog)")
    
    # Xpad
    if subprocess.run(['which', 'xpad'], capture_output=True).returncode == 0:
        try:
            result = subprocess.run(['xpad', '--version'], capture_output=True, text=True)
            print(f"✓ Xpad: Available")
        except:
            print("✓ Xpad: Available (version check failed)")
    else:
        print("✗ Xpad: Not found (sudo apt install xpad)")
    
    # Google Drive clients
    gdrive_clients = ['google-drive-ocamlfuse', 'insync', 'rclone', 'gdrive']
    found_client = False
    for client in gdrive_clients:
        if subprocess.run(['which', client], capture_output=True).returncode == 0:
            print(f"✓ Google Drive client: {client}")
            found_client = True
            break
    
    if not found_client:
        print("⚠ Google Drive client: None found (install google-drive-ocamlfuse or similar)")
    
    print()

def check_file_system():
    """Check file system and directories."""
    print("File System")
    print("=" * 50)
    
    config_file = Path.home() / ".xpad_gdrive_config.json"
    
    # Configuration file
    if config_file.exists():
        print(f"✓ Config file: {config_file}")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Xpad directory
            xpad_dir = Path(config.get('xpad_directory', '~/.config/xpad')).expanduser()
            if xpad_dir.exists():
                content_files = list(xpad_dir.glob('content-*'))
                print(f"✓ Xpad directory: {xpad_dir} ({len(content_files)} notes)")
            else:
                print(f"✗ Xpad directory: {xpad_dir} (not found)")
            
            # Google Drive sync folder
            gdrive_folder = Path(config.get('gdrive_sync_folder', '~/GoogleDrive/XpadSync')).expanduser()
            if gdrive_folder.exists():
                sync_files = list(gdrive_folder.glob('xpad_note_*'))
                print(f"✓ Google Drive folder: {gdrive_folder} ({len(sync_files)} synced files)")
                
                # Check metadata file
                metadata_file = gdrive_folder / '.xpad_sync_metadata.json'
                if metadata_file.exists():
                    print(f"✓ Metadata file: Present")
                else:
                    print(f"⚠ Metadata file: Missing (will be created on first sync)")
                
                # Check log file
                log_file = gdrive_folder / 'xpad_sync.log'
                if log_file.exists():
                    size_mb = log_file.stat().st_size / (1024 * 1024)
                    print(f"✓ Log file: Present ({size_mb:.1f}MB)")
                else:
                    print(f"⚠ Log file: Missing (will be created on first run)")
            else:
                print(f"✗ Google Drive folder: {gdrive_folder} (not found)")
            
        except Exception as e:
            print(f"✗ Config file: Invalid JSON - {e}")
    else:
        print(f"✗ Config file: {config_file} (not found)")
    
    print()

def check_sync_status():
    """Check sync status and recent activity."""
    print("Sync Status")
    print("=" * 50)
    
    config_file = Path.home() / ".xpad_gdrive_config.json"
    if not config_file.exists():
        print("✗ Cannot check sync status - config file missing")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        gdrive_folder = Path(config.get('gdrive_sync_folder', '~/GoogleDrive/XpadSync')).expanduser()
        metadata_file = gdrive_folder / '.xpad_sync_metadata.json'
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            print(f"✓ Tracked files: {len(metadata)}")
            
            # Find most recent sync
            recent_syncs = []
            for file_path, data in metadata.items():
                if 'last_synced' in data:
                    try:
                        sync_time = datetime.fromisoformat(data['last_synced'])
                        recent_syncs.append((file_path, sync_time))
                    except:
                        pass
            
            if recent_syncs:
                recent_syncs.sort(key=lambda x: x[1], reverse=True)
                most_recent = recent_syncs[0]
                time_diff = datetime.now() - most_recent[1]
                
                if time_diff < timedelta(hours=1):
                    print(f"✓ Last sync: {time_diff.total_seconds():.0f} seconds ago")
                elif time_diff < timedelta(days=1):
                    print(f"✓ Last sync: {time_diff.total_seconds()/3600:.1f} hours ago")
                else:
                    print(f"⚠ Last sync: {time_diff.days} days ago")
                
                print(f"  File: {Path(most_recent[0]).name}")
            else:
                print("⚠ No sync history found")
        else:
            print("⚠ No metadata file - run sync first")
    
    except Exception as e:
        print(f"✗ Error checking sync status: {e}")
    
    print()

def check_google_drive_connectivity():
    """Check Google Drive connectivity and folder access."""
    print("Google Drive Connectivity")
    print("=" * 50)
    
    config_file = Path.home() / ".xpad_gdrive_config.json"
    if not config_file.exists():
        print("✗ Cannot check - config file missing")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        gdrive_folder = Path(config.get('gdrive_sync_folder', '~/GoogleDrive/XpadSync')).expanduser()
        
        # Test write access
        test_file = gdrive_folder / f'test_connectivity_{int(time.time())}.tmp'
        try:
            test_file.write_text(f"Connectivity test at {datetime.now()}")
            print("✓ Write access: OK")
            test_file.unlink()
            print("✓ Delete access: OK")
        except Exception as e:
            print(f"✗ File operations failed: {e}")
        
        # Check for Google Drive processes
        try:
            result = subprocess.run(['pgrep', '-f', 'google-drive'], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"✓ Google Drive processes: {len(pids)} running")
            else:
                print("⚠ Google Drive processes: None found")
        except:
            print("⚠ Could not check Google Drive processes")
        
        # Check mount points (for FUSE)
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if 'google-drive' in result.stdout.lower():
                print("✓ Google Drive FUSE mount: Detected")
            else:
                print("⚠ Google Drive FUSE mount: Not detected")
        except:
            pass
    
    except Exception as e:
        print(f"✗ Error checking Google Drive: {e}")
    
    print()

def show_recent_logs(lines=20):
    """Show recent log entries."""
    print(f"Recent Log Entries (last {lines} lines)")
    print("=" * 50)
    
    config_file = Path.home() / ".xpad_gdrive_config.json"
    if not config_file.exists():
        print("✗ Cannot show logs - config file missing")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        gdrive_folder = Path(config.get('gdrive_sync_folder', '~/GoogleDrive/XpadSync')).expanduser()
        log_file = gdrive_folder / 'xpad_sync.log'
        
        if log_file.exists():
            try:
                result = subprocess.run(['tail', f'-{lines}', str(log_file)], 
                                      capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                else:
                    print("Log file is empty")
            except:
                # Fallback to Python implementation
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    print(''.join(recent_lines))
        else:
            print("✗ Log file not found")
    
    except Exception as e:
        print(f"✗ Error reading logs: {e}")
    
    print()

def run_sync_test():
    """Run a test sync operation."""
    print("Sync Test")
    print("=" * 50)
    
    # Check if xpad-gdrive-sync is available
    sync_cmd = Path.home() / '.local/bin/xpad-gdrive-sync'
    if not sync_cmd.exists():
        print("✗ xpad-gdrive-sync not found - run 'make install' first")
        return
    
    try:
        print("Running test sync...")
        result = subprocess.run([str(sync_cmd), 'sync'], 
                              capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Sync test completed successfully")
        else:
            print(f"✗ Sync test failed (exit code: {result.returncode})")
    
    except subprocess.TimeoutExpired:
        print("✗ Sync test timed out (>30 seconds)")
    except Exception as e:
        print(f"✗ Sync test error: {e}")
    
    print()

def show_configuration():
    """Show current configuration."""
    print("Configuration")
    print("=" * 50)
    
    config_file = Path.home() / ".xpad_gdrive_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Mask sensitive information if any
            display_config = config.copy()
            
            print(json.dumps(display_config, indent=2))
        except Exception as e:
            print(f"✗ Error reading configuration: {e}")
    else:
        print("✗ Configuration file not found")
    
    print()

def run_full_diagnostic():
    """Run complete diagnostic check."""
    print("Xpad to Google Drive Sync - Full Diagnostic")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    check_system_dependencies()
    check_file_system()
    check_sync_status()
    check_google_drive_connectivity()
    show_configuration()
    show_recent_logs(10)

def main():
    parser = argparse.ArgumentParser(description='Xpad Sync Diagnostics')
    parser.add_argument('--full', action='store_true',
                       help='Run full diagnostic check')
    parser.add_argument('--logs', type=int, metavar='N', default=20,
                       help='Show last N log lines')
    parser.add_argument('--test-sync', action='store_true',
                       help='Run sync test')
    parser.add_argument('--config', action='store_true',
                       help='Show configuration')
    parser.add_argument('--status', action='store_true',
                       help='Show sync status only')
    
    args = parser.parse_args()
    
    if args.full:
        run_full_diagnostic()
    elif args.test_sync:
        run_sync_test()
    elif args.config:
        show_configuration()
    elif args.status:
        check_sync_status()
    elif args.logs:
        show_recent_logs(args.logs)
    else:
        # Default: show key status
        check_system_dependencies()
        check_file_system()
        check_sync_status()

if __name__ == '__main__':
    main()