# Xpad to Google Drive Sync - Makefile
# Clean build system for the new Google Drive architecture

.PHONY: help install uninstall test clean status

# Configuration
PREFIX ?= $(HOME)/.local
INSTALL_DIR = $(PREFIX)/bin
CONFIG_FILE = $(HOME)/.xpad_gdrive_config.json

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m

# Logging functions
define log_info
	@echo -e "$(BLUE)[INFO]$(NC) $(1)"
endef

define log_success
	@echo -e "$(GREEN)[OK]$(NC) $(1)"
endef

define log_warning
	@echo -e "$(YELLOW)[WARN]$(NC) $(1)"
endef

define log_error
	@echo -e "$(RED)[ERROR]$(NC) $(1)"
endef

# Default target
help:
	@echo "Xpad to Google Drive Sync - Build System"
	@echo "========================================"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install the sync system"
	@echo "  uninstall   - Remove the sync system"
	@echo "  test        - Test the installation"
	@echo "  clean       - Clean up temporary files"
	@echo "  status      - Show system status"
	@echo ""
	@echo "Quick commands:"
	@echo "  make install && make status    # Install and check"
	@echo "  make test                      # Test installation"
	@echo ""

# Install the software
install:
	$(call log_info,"Installing Xpad to Google Drive Sync...")
	@if [ -f scripts/install.sh ]; then \
		chmod +x scripts/install.sh && ./scripts/install.sh; \
	else \
		$(call log_error,"scripts/install.sh not found"); \
		exit 1; \
	fi
	$(call log_success,"Installation completed")

# Uninstall the software
uninstall:
	$(call log_info,"Uninstalling Xpad to Google Drive Sync...")
	@if [ -f scripts/install.sh ]; then \
		chmod +x scripts/install.sh && ./scripts/install.sh --uninstall; \
	else \
		$(call log_info,"Performing manual cleanup"); \
		rm -f $(INSTALL_DIR)/xpad-gdrive-sync; \
		rm -f $(CONFIG_FILE); \
	fi
	$(call log_success,"Uninstallation completed")

# Test installation
test:
	$(call log_info,"Testing installation...")
	@if [ -x $(INSTALL_DIR)/xpad-gdrive-sync ]; then \
		$(call log_success,"xpad-gdrive-sync installed and executable"); \
		$(INSTALL_DIR)/xpad-gdrive-sync status; \
	else \
		$(call log_error,"xpad-gdrive-sync not found or not executable"); \
		$(call log_info,"Run 'make install' first"); \
		exit 1; \
	fi

# Show system status
status:
	$(call log_info,"Checking system status...")
	@echo "Files:"
	@echo "======"
	@if [ -x $(INSTALL_DIR)/xpad-gdrive-sync ]; then \
		echo "✓ xpad-gdrive-sync: $(INSTALL_DIR)/xpad-gdrive-sync"; \
	else \
		echo "✗ xpad-gdrive-sync: not installed"; \
	fi
	@if [ -f $(CONFIG_FILE) ]; then \
		echo "✓ config: $(CONFIG_FILE)"; \
		if grep -q "~/GoogleDrive/XpadSync" $(CONFIG_FILE) 2>/dev/null; then \
			echo "  ⚠ using default path - edit to set your actual Google Drive folder"; \
		else \
			echo "  ✓ Google Drive path configured"; \
		fi; \
	else \
		echo "✗ config: not found"; \
	fi
	@echo ""
	@echo "Dependencies:"
	@echo "============="
	@if command -v python3 >/dev/null 2>&1; then \
		PYTHON_VERSION=$$(python3 --version 2>&1); \
		echo "✓ Python: $$PYTHON_VERSION"; \
	else \
		echo "✗ Python 3: not found"; \
	fi
	@if python3 -c "import watchdog" 2>/dev/null; then \
		echo "✓ Watchdog: installed"; \
	else \
		echo "✗ Watchdog: not installed (run: pip3 install --user watchdog)"; \
	fi
	@if command -v xpad >/dev/null 2>&1; then \
		echo "✓ Xpad: available"; \
	else \
		echo "✗ Xpad: not found (install with: sudo apt install xpad)"; \
	fi
	@echo ""
	@if [ -x $(INSTALL_DIR)/xpad-gdrive-sync ]; then \
		$(INSTALL_DIR)/xpad-gdrive-sync status 2>/dev/null || echo "Run xpad-gdrive-sync status for detailed info"; \
	fi

# Run a quick sync test
sync-test:
	$(call log_info,"Running sync test...")
	@if [ -x $(INSTALL_DIR)/xpad-gdrive-sync ]; then \
		$(INSTALL_DIR)/xpad-gdrive-sync sync; \
	else \
		$(call log_error,"xpad-gdrive-sync not installed. Run 'make install' first."); \
		exit 1; \
	fi

# Start monitoring
monitor:
	$(call log_info,"Starting file monitoring...")
	@if [ -x $(INSTALL_DIR)/xpad-gdrive-sync ]; then \
		$(INSTALL_DIR)/xpad-gdrive-sync monitor; \
	else \
		$(call log_error,"xpad-gdrive-sync not installed. Run 'make install' first."); \
		exit 1; \
	fi

# Clean up temporary files
clean:
	$(call log_info,"Cleaning up...")
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf *.pyc
	@rm -rf .mypy_cache/
	@rm -rf .pytest_cache/
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	$(call log_success,"Cleanup completed")

# Development targets
dev-install: install
	$(call log_info,"Installing development dependencies...")
	@pip3 install --user flake8 black mypy pytest 2>/dev/null || true
	$(call log_success,"Development environment ready")

# Quick start for new users
quickstart: install status
	$(call log_info,"Quick start completed!")
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit $(CONFIG_FILE) to set your Google Drive sync folder"
	@echo "2. Run 'make sync-test' to test the setup"
	@echo "3. Follow setup guides in zapier/ and ios/ directories"

# Show system information
sysinfo:
	$(call log_info,"System information:")
	@echo "OS: $$(uname -s) $$(uname -r)"
	@echo "Python: $$(python3 --version 2>&1)"
	@echo "Shell: $$SHELL"
	@echo "User: $$USER"
	@echo "Home: $$HOME"
	@echo "Install prefix: $(PREFIX)"
	@if command -v xpad >/dev/null 2>&1; then \
		echo "Xpad: Available"; \
	else \
		echo "Xpad: Not found (install with: sudo apt install xpad)"; \
	fi