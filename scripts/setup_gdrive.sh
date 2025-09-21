#!/bin/bash
# Google Drive Setup Helper Script
# 
# Helps users configure Google Drive Desktop for Xpad sync.
#
# Author: Robin Kokot
# License: GPL v2

set -euo pipefail

# Colors
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' BOLD='' NC=''
fi

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Default paths
DEFAULT_GDRIVE_ROOT="$HOME/GoogleDrive"
DEFAULT_SYNC_FOLDER="$DEFAULT_GDRIVE_ROOT/XpadSync"
CONFIG_FILE="$HOME/.xpad_gdrive_config.json"

# Detect Google Drive installation
detect_gdrive() {
    log_info "Detecting Google Drive installation..."
    
    # Common Google Drive paths
    local gdrive_paths=(
        "$HOME/Google Drive"
        "$HOME/GoogleDrive" 
        "$HOME/gdrive"
        "$HOME/Drive"
        "/mnt/gdrive"
        "/media/$USER/GoogleDrive"
    )
    
    for path in "${gdrive_paths[@]}"; do
        if [[ -d "$path" ]]; then
            log_success "Found Google Drive at: $path"
            echo "$path"
            return 0
        fi
    done
    
    # Check if Google Drive is mounted via FUSE
    if mount | grep -q "google-drive"; then
        local mount_point=$(mount | grep "google-drive" | awk '{print $3}' | head -1)
        log_success "Found Google Drive FUSE mount at: $mount_point"
        echo "$mount_point"
        return 0
    fi
    
    log_warning "Google Drive not found in common locations"
    return 1
}

# Check if Google Drive Desktop is installed
check_gdrive_desktop() {
    log_info "Checking for Google Drive Desktop..."
    
    # Check for common Google Drive Desktop executables
    local gdrive_commands=(
        "google-drive-ocamlfuse"
        "gdrive"
        "google-drive"
        "insync"
        "rclone"
    )
    
    for cmd in "${gdrive_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            log_success "Found Google Drive client: $cmd"
            echo "$cmd"
            return 0
        fi
    done
    
    log_warning "No Google Drive Desktop client found"
    return 1
}

# Install Google Drive Desktop suggestions
suggest_gdrive_install() {
    log_info "Google Drive Desktop installation options:"
    echo
    echo "Option 1: Google Drive OCamlFUSE (Recommended)"
    echo "  sudo apt update"
    echo "  sudo apt install google-drive-ocamlfuse"
    echo "  google-drive-ocamlfuse ~/GoogleDrive"
    echo
    echo "Option 2: Insync (Commercial, native Google Drive client)"
    echo "  Visit: https://www.insynchq.com/"
    echo "  Download .deb package and install"
    echo
    echo "Option 3: rclone (Advanced users)"
    echo "  sudo apt install rclone"
    echo "  rclone config  # Configure Google Drive"
    echo "  rclone mount gdrive: ~/GoogleDrive --daemon"
    echo
    echo "Option 4: Use existing cloud storage"
    echo "  - Dropbox: ~/Dropbox/XpadSync"
    echo "  - OneDrive: ~/OneDrive/XpadSync"
    echo "  - Any synced folder works!"
    echo
}

# Setup sync folder
setup_sync_folder() {
    local gdrive_root="$1"
    local sync_folder="$gdrive_root/XpadSync"
    
    log_info "Setting up sync folder..."
    
    # Create sync folder
    if mkdir -p "$sync_folder"; then
        log_success "Created sync folder: $sync_folder"
    else
        log_error "Failed to create sync folder: $sync_folder"
        return 1
    fi
    
    # Create a welcome note
    local welcome_note="$sync_folder/xpad_note_Welcome_$(date +%Y%m%d_%H%M%S)_setup.md"
    cat > "$welcome_note" << EOF
# Welcome to Xpad Sync!

This folder is now configured for Xpad to iOS synchronization.

## How it works:
1. **Linux**: Xpad notes are automatically saved here
2. **Google Drive**: Syncs files to the cloud
3. **Zapier**: Monitors for new files and triggers notifications
4. **iOS**: Shortcuts processes notifications and saves to Apple Notes

## Setup Status:
- ✅ Sync folder created
- ✅ Google Drive path configured
- ⏳ Next: Configure Zapier automation
- ⏳ Next: Set up iOS Shortcuts

## Files you'll see here:
- \`xpad_note_*\` - Your synced notes
- \`.xpad_sync_metadata.json\` - Sync tracking data
- \`xpad_sync.log\` - System logs

Created: $(date)
From: Xpad-GDrive-Sync Setup
EOF
    
    log_success "Created welcome note: $(basename "$welcome_note")"
    
    # Update configuration if it exists
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "Updating configuration file..."
        
        # Use Python to update JSON config
        python3 << EOF
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    
    config['gdrive_sync_folder'] = '$sync_folder'
    
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration updated")
except Exception as e:
    print(f"⚠ Could not update config: {e}")
EOF
    else
        log_warning "Configuration file not found: $CONFIG_FILE"
        log_info "Run 'make install' first to create the configuration"
    fi
    
    echo "$sync_folder"
}

# Test Google Drive sync
test_sync() {
    local sync_folder="$1"
    
    log_info "Testing Google Drive sync..."
    
    # Create test file
    local test_file="$sync_folder/test_sync_$(date +%s).txt"
    echo "Test file created at $(date)" > "$test_file"
    log_info "Created test file: $(basename "$test_file")"
    
    # Wait and check if file appears in Google Drive web interface
    log_info "Please check your Google Drive web interface (drive.google.com)"
    log_info "Look for the XpadSync folder and verify the test file appears"
    echo
    read -p "Can you see the test file in Google Drive web interface? [y/N]: " -r
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_success "Google Drive sync is working!"
        rm -f "$test_file"
        return 0
    else
        log_warning "Google Drive sync may not be working properly"
        log_info "Troubleshooting steps:"
        echo "1. Check if Google Drive Desktop is running"
        echo "2. Verify you're signed into the correct Google account"
        echo "3. Check available storage space"
        echo "4. Try restarting Google Drive Desktop"
        return 1
    fi
}

# Interactive setup
interactive_setup() {
    echo -e "${BOLD}${BLUE}"
    echo "Google Drive Setup for Xpad Sync"
    echo "================================"
    echo -e "${NC}"
    echo "This script will help you configure Google Drive for Xpad synchronization."
    echo
    
    # Detect existing Google Drive
    if gdrive_path=$(detect_gdrive); then
        echo "Found Google Drive at: $gdrive_path"
        read -p "Use this location? [Y/n]: " -r
        
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sync_folder=$(setup_sync_folder "$gdrive_path")
            if test_sync "$sync_folder"; then
                show_next_steps "$sync_folder"
                return 0
            fi
        fi
    fi
    
    # Check for Google Drive Desktop
    if ! check_gdrive_desktop; then
        log_warning "Google Drive Desktop not found"
        suggest_gdrive_install
        echo
        read -p "Do you want to continue with manual setup? [y/N]: " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled. Install Google Drive Desktop first."
            return 1
        fi
    fi
    
    # Manual path selection
    echo
    log_info "Manual Google Drive path setup:"
    echo "Enter the path to your Google Drive folder:"
    read -p "Path (default: $DEFAULT_GDRIVE_ROOT): " gdrive_input
    
    local gdrive_path="${gdrive_input:-$DEFAULT_GDRIVE_ROOT}"
    gdrive_path="${gdrive_path/#\~/$HOME}"  # Expand tilde
    
    if [[ ! -d "$gdrive_path" ]]; then
        log_warning "Directory doesn't exist: $gdrive_path"
        read -p "Create it? [Y/n]: " -r
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            mkdir -p "$gdrive_path"
            log_success "Created directory: $gdrive_path"
        else
            log_error "Cannot proceed without Google Drive folder"
            return 1
        fi
    fi
    
    sync_folder=$(setup_sync_folder "$gdrive_path")
    test_sync "$sync_folder"
    show_next_steps "$sync_folder"
}

# Show next steps
show_next_steps() {
    local sync_folder="$1"
    
    echo
    echo -e "${GREEN}${BOLD}Google Drive setup completed!${NC}"
    echo
    echo "Sync folder: $sync_folder"
    echo
    echo "Next steps:"
    echo "==========="
    echo "1. Test the Xpad sync:"
    echo "   xpad-gdrive-sync sync"
    echo
    echo "2. Start monitoring:"
    echo "   xpad-gdrive-sync monitor"
    echo
    echo "3. Set up Zapier automation:"
    echo "   - Open zapier/setup_guide.md"
    echo "   - Configure Google Drive trigger for folder: /XpadSync"
    echo
    echo "4. Configure iOS Shortcuts:"
    echo "   - Open ios/setup_guide.md"
    echo "   - Install Pushcut and create shortcuts"
    echo
    echo "Documentation:"
    echo "=============="
    echo "  Zapier guide: $(dirname "$(dirname "$(readlink -f "$0")")")/zapier/setup_guide.md"
    echo "  iOS guide: $(dirname "$(dirname "$(readlink -f "$0")")")/ios/setup_guide.md"
    echo
}

# Status check
check_status() {
    log_info "Google Drive setup status:"
    echo
    
    # Check if config exists and has Google Drive path
    if [[ -f "$CONFIG_FILE" ]]; then
        local gdrive_folder
        gdrive_folder=$(python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(config.get('gdrive_sync_folder', 'NOT_SET'))
except:
    print('ERROR')
")
        
        if [[ "$gdrive_folder" != "NOT_SET" && "$gdrive_folder" != "ERROR" ]]; then
            echo "✅ Configuration: $gdrive_folder"
            
            if [[ -d "$gdrive_folder" ]]; then
                echo "✅ Folder exists"
                
                local file_count=$(find "$gdrive_folder" -name "xpad_note_*" 2>/dev/null | wc -l)
                echo "📁 Synced files: $file_count"
                
                if [[ -f "$gdrive_folder/xpad_sync.log" ]]; then
                    echo "📝 Log file present"
                fi
            else
                echo "❌ Folder missing: $gdrive_folder"
            fi
        else
            echo "❌ Configuration not set"
        fi
    else
        echo "❌ Configuration file not found: $CONFIG_FILE"
    fi
    
    # Check Google Drive client
    if check_gdrive_desktop &>/dev/null; then
        echo "✅ Google Drive client available"
    else
        echo "❌ Google Drive client not found"
    fi
}

# Main function
main() {
    case "${1:-}" in
        --status|-s)
            check_status
            ;;
        --help|-h)
            echo "Usage: $0 [--status|--help]"
            echo
            echo "Google Drive setup helper for Xpad sync."
            echo
            echo "Options:"
            echo "  --status, -s    Check current setup status"
            echo "  --help, -h      Show this help"
            echo
            echo "Run without arguments for interactive setup."
            ;;
        "")
            interactive_setup
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"