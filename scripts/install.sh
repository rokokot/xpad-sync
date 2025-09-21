#!/bin/bash
# Xpad to Google Drive Sync - Installation Script
# 
# Clean, simple installation for the new Google Drive architecture.
#
# Author: Robin Kokot
# License: GPL v2

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$HOME/.local/bin"
CONFIG_FILE="$HOME/.xpad_gdrive_config.json"

# Colors (disable if not a terminal)
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
log_fatal() { echo -e "${RED}[FATAL]${NC} $1" >&2; exit 1; }

# Check if we're running as root (bad idea)
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_fatal "Don't run this as root. It installs in your home directory."
    fi
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ ! "$(uname -s)" == "Linux" ]]; then
        log_fatal "This script only works on Linux"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_fatal "Python 3 is required but not found. Install with: sudo apt install python3"
    fi
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 7 ]]; then
        log_fatal "Python 3.7+ is required, found $python_version"
    fi
    
    log_success "Python $python_version found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_fatal "pip3 is required but not found. Install with: sudo apt install python3-pip"
    fi
    
    log_success "System requirements check passed"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Install watchdog for file monitoring
    if pip3 install --user "watchdog>=5.0.0" &> /dev/null; then
        log_success "Installed watchdog"
    else
        log_warning "Failed to install watchdog - trying without version constraint"
        if pip3 install --user watchdog &> /dev/null; then
            log_success "Installed watchdog (no version constraint)"
        else
            log_warning "Failed to install watchdog - real-time sync may not work"
        fi
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating directories..."
    
    local dirs=(
        "$INSTALL_DIR"
        "$(dirname "$CONFIG_FILE")"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            if mkdir -p "$dir"; then
                log_success "Created $dir"
            else
                log_fatal "Failed to create $dir"
            fi
        fi
    done
}

# Install main script
install_script() {
    log_info "Installing main script..."
    
    # Check if source script exists
    local source_script="$SCRIPT_DIR/xpad-gdrive-sync"
    if [[ ! -f "$source_script" ]]; then
        log_fatal "Source script not found: $source_script"
    fi
    
    # Copy and make executable
    cp "$source_script" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/xpad-gdrive-sync"
    log_success "Installed xpad-gdrive-sync to $INSTALL_DIR"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        log_warning "~/.local/bin is not in your PATH"
        
        # Detect shell and provide appropriate instructions
        if [[ "$SHELL" == *"zsh"* ]]; then
            log_info "Add this to your ~/.zshrc:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            log_info "Then run: source ~/.zshrc"
        elif [[ "$SHELL" == *"bash"* ]]; then
            log_info "Add this to your ~/.bashrc:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            log_info "Then run: source ~/.bashrc"
        else
            log_info "Add this to your shell's configuration file:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            log_info "Then restart your terminal or source the config file"
        fi
    fi
}

# Create default configuration
create_config() {
    log_info "Creating configuration file..."
    
    if [[ -f "$CONFIG_FILE" ]]; then
        log_warning "Configuration file already exists, backing up..."
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%s)"
    fi
    
    # Use the example config
    local example_config="$PROJECT_ROOT/config.example.json"
    if [[ -f "$example_config" ]]; then
        cp "$example_config" "$CONFIG_FILE"
        log_success "Configuration file created: $CONFIG_FILE"
    else
        log_fatal "Example configuration not found: $example_config"
    fi
    
    # Set secure permissions
    chmod 600 "$CONFIG_FILE"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Test that script is executable
    if [[ -x "$INSTALL_DIR/xpad-gdrive-sync" ]]; then
        log_success "xpad-gdrive-sync is executable"
    else
        log_error "xpad-gdrive-sync is not executable"
        return 1
    fi
    
    # Test basic functionality
    if "$INSTALL_DIR/xpad-gdrive-sync" status &> /dev/null; then
        log_success "Basic functionality test passed"
    else
        log_warning "Basic functionality test had issues (this may be normal if directories don't exist yet)"
    fi
    
    log_success "Installation test completed"
}

# Show usage information
show_usage() {
    echo
    echo -e "${GREEN}${BOLD}Installation completed successfully!${NC}"
    echo
    echo "Configuration:"
    echo "=============="
    echo "  Config file: $CONFIG_FILE"
    echo "  Edit this file to set your Google Drive sync folder path"
    echo
    echo "Quick Start:"
    echo "============"
    echo "1. Edit configuration:       nano $CONFIG_FILE"
    echo "2. Set Google Drive folder:  ~/GoogleDrive/XpadSync"
    echo "3. Test the setup:           xpad-gdrive-sync status"
    echo "4. Run one-time sync:        xpad-gdrive-sync sync"
    echo "5. Start monitoring:         xpad-gdrive-sync monitor"
    echo
    echo "Common Commands:"
    echo "================"
    echo "  xpad-gdrive-sync status     # Check system status"
    echo "  xpad-gdrive-sync sync       # One-time sync"
    echo "  xpad-gdrive-sync sync --force  # Force sync all notes"
    echo "  xpad-gdrive-sync monitor    # Start real-time monitoring"
    echo
    echo "Next Steps:"
    echo "==========="
    echo "1. Install Google Drive Desktop client if not already installed"
    echo "2. Set up the sync folder path in the configuration"
    echo "3. Follow the Zapier setup guide in zapier/setup_guide.md"
    echo "4. Configure iOS Shortcuts using ios/setup_guide.md"
    echo
    echo "Documentation:"
    echo "=============="
    echo "  Project: $PROJECT_ROOT"
    echo "  Zapier guide: $PROJECT_ROOT/zapier/setup_guide.md"
    echo "  iOS guide: $PROJECT_ROOT/ios/setup_guide.md"
    echo
}

# Uninstall function
uninstall() {
    log_info "Uninstalling Xpad to Google Drive Sync..."
    
    # Remove script
    rm -f "$INSTALL_DIR/xpad-gdrive-sync"
    log_success "Removed executable"
    
    # Ask about configuration
    read -p "Remove configuration file? [y/N]: " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$CONFIG_FILE"
        rm -f "$CONFIG_FILE".backup.*
        log_success "Configuration removed"
    else
        log_info "Configuration preserved: $CONFIG_FILE"
    fi
    
    log_success "Uninstallation completed"
}

# Main installation function
main() {
    echo -e "${BOLD}${BLUE}"
    echo "Xpad to Google Drive Sync - Installation"
    echo "========================================"
    echo -e "${NC}"
    echo "This will install the sync system in your home directory."
    echo "No root privileges required."
    echo
    
    # Confirm installation
    read -p "Continue with installation? [Y/n]: " -r
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
    
    # Run installation steps
    check_not_root
    check_system_requirements
    install_python_deps
    create_directories
    install_script
    create_config
    
    # Test installation
    if ! test_installation; then
        log_error "Installation test failed"
        exit 1
    fi
    
    # Show usage information
    show_usage
    
    log_success "Installation completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help|--uninstall]"
        echo
        echo "Installs Xpad to Google Drive sync system."
        echo "Run without arguments for interactive installation."
        exit 0
        ;;
    --uninstall)
        uninstall
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information."
        exit 1
        ;;
esac