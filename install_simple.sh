#!/bin/bash
# Installation script for StormShadow SIP-Only

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root - this is required for iptables operations"
    else
        log_info "Running as regular user - sudo will be required for iptables operations"
    fi
}

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.8+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_info "✓ Python version is compatible"
        else
            log_error "Python 3.8+ is required"
            exit 1
        fi
    else
        log_error "Python 3 is not installed"
        exit 1
    fi
}

# Check Docker
check_docker() {
    if command -v docker &> /dev/null; then
        log_info "✓ Docker is installed"
        if docker info &> /dev/null; then
            log_info "✓ Docker is running"
        else
            log_warn "Docker is installed but not running"
            log_info "You may need to start Docker: sudo systemctl start docker"
        fi
    else
        log_warn "Docker is not installed - lab mode will not work"
        log_info "Install Docker: https://docs.docker.com/get-docker/"
    fi
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not available"
        log_info "Install pip: sudo apt-get install python3-pip"
        exit 1
    fi
    
    # Install requirements
    if [ -f "requirements_simple.txt" ]; then
        pip3 install -r requirements_simple.txt --user
        log_info "✓ Python dependencies installed"
    else
        log_warn "requirements_simple.txt not found, installing minimal dependencies"
        pip3 install PyYAML PySide6 --user
    fi
}

# Make shell scripts executable
setup_scripts() {
    log_info "Setting up shell scripts..."
    
    if [ -d "sip-shell-scripts" ]; then
        chmod +x sip-shell-scripts/*.sh
        log_info "✓ Shell scripts made executable"
    else
        log_error "sip-shell-scripts directory not found"
        exit 1
    fi
}

# Create default configuration if it doesn't exist
setup_config() {
    log_info "Setting up configuration..."
    
    if [ ! -f "sip-stormshadow-config.yaml" ]; then
        log_warn "Main config file not found, creating default"
        # Config file should already exist, but create backup
        cp sip-stormshadow-config.yaml sip-stormshadow-config.yaml.backup 2>/dev/null || true
    fi
    
    log_info "✓ Configuration files ready"
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check for iptables
    if command -v iptables &> /dev/null; then
        log_info "✓ iptables is available"
    else
        log_error "iptables is not installed"
        log_info "Install iptables: sudo apt-get install iptables"
        exit 1
    fi
    
    # Check for required network tools
    if command -v ip &> /dev/null; then
        log_info "✓ ip command is available"
    else
        log_warn "ip command not found, some features may not work"
    fi
}

# Main installation
main() {
    log_info "Installing StormShadow SIP-Only..."
    log_info "======================================"
    
    check_root
    check_python
    check_docker
    check_system_requirements
    install_dependencies
    setup_scripts
    setup_config
    
    log_info ""
    log_info "======================================"
    log_info "✓ Installation completed successfully!"
    log_info ""
    log_info "Usage:"
    log_info "  GUI mode:    python3 main.py --mode gui"
    log_info "  Lab mode:    sudo python3 main.py --mode lab"
    log_info "  Attack mode: sudo python3 main.py --mode attack --target-ip <target>"
    log_info "  Both modes:  sudo python3 main.py --mode both"
    log_info ""
    log_info "Configuration files:"
    log_info "  - sip-stormshadow-config.yaml (main config)"
    log_info "  - lab-sip-config.yaml (lab-specific)"
    log_info "  - attack-sip-config.yaml (attack-specific)"
    log_info ""
    log_warn "Note: Lab and attack modes require sudo for iptables operations"
}

# Run main function
main "$@"
