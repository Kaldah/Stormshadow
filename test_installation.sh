#!/bin/bash
# Test script for StormShadow SIP-Only
# Verifies that all components are working correctly

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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing $test_name... "
    
    if eval "$test_command" &>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test Python and dependencies
test_python() {
    log_info "Testing Python environment..."
    
    run_test "Python 3" "python3 --version"
    run_test "YAML module" "python3 -c 'import yaml'"
    
    # PySide6 is optional
    if python3 -c 'import PySide6' 2>/dev/null; then
        run_test "PySide6 (GUI)" "python3 -c 'import PySide6.QtWidgets'"
    else
        log_warn "PySide6 not installed - GUI mode will not work"
    fi
}

# Test configuration files
test_config() {
    log_info "Testing configuration files..."
    
    run_test "Main config exists" "test -f sip-stormshadow-config.yaml"
    run_test "Lab config exists" "test -f lab-sip-config.yaml"
    run_test "Attack config exists" "test -f attack-sip-config.yaml"
    
    # Test YAML syntax
    run_test "Main config syntax" "python3 -c 'import yaml; yaml.safe_load(open(\"sip-stormshadow-config.yaml\"))'"
    run_test "Lab config syntax" "python3 -c 'import yaml; yaml.safe_load(open(\"lab-sip-config.yaml\"))'"
    run_test "Attack config syntax" "python3 -c 'import yaml; yaml.safe_load(open(\"attack-sip-config.yaml\"))'"
}

# Test shell scripts
test_scripts() {
    log_info "Testing shell scripts..."
    
    local scripts=(
        "setup_lab.sh"
        "setup_attack.sh"
        "setup_spoofing.sh"
        "setup_return_path.sh"
        "cleanup_all.sh"
        "cleanup_lab.sh"
        "cleanup_attack.sh"
    )
    
    for script in "${scripts[@]}"; do
        run_test "$script exists" "test -f sip-shell-scripts/$script"
        run_test "$script executable" "test -x sip-shell-scripts/$script"
        run_test "$script syntax" "bash -n sip-shell-scripts/$script"
    done
}

# Test system requirements
test_system() {
    log_info "Testing system requirements..."
    
    run_test "iptables available" "command -v iptables"
    run_test "docker available" "command -v docker"
    
    # Test iptables access (may require sudo)
    if [[ $EUID -eq 0 ]]; then
        run_test "iptables access" "iptables -L -n"
    else
        log_warn "Not running as root - iptables access test skipped"
    fi
    
    # Test Docker access
    if docker info &>/dev/null; then
        run_test "docker access" "docker info"
    else
        log_warn "Docker not running or no access - test skipped"
    fi
}

# Test main.py functionality
test_main() {
    log_info "Testing main.py functionality..."
    
    run_test "main.py syntax" "python3 -m py_compile main.py"
    run_test "main.py help" "python3 main.py --help"
    
    # Test imports
    run_test "configuration import" "python3 -c 'from main import SipOnlyConfig'"
    run_test "shell manager import" "python3 -c 'from main import ShellScriptManager'"
    run_test "orchestrator import" "python3 -c 'from main import SipOnlyOrchestrator'"
}

# Test GUI components (if available)
test_gui() {
    log_info "Testing GUI components..."
    
    if python3 -c 'import PySide6' 2>/dev/null; then
        run_test "GUI config manager" "python3 -c 'from gui.config_manager_simple import ConfigManager'"
        run_test "GUI shell manager" "python3 -c 'from gui.shell_manager_simple import SipShellManager'"
        run_test "GUI main window" "python3 -c 'from gui.sip_only_gui_simple import SipOnlyGUI'"
    else
        log_warn "PySide6 not available - GUI tests skipped"
    fi
}

# Test configuration loading
test_config_loading() {
    log_info "Testing configuration loading..."
    
    # Test with Python
    run_test "Load main config" "python3 -c 'from main import SipOnlyConfig; c = SipOnlyConfig()'"
    run_test "Load lab config" "python3 -c 'from main import SipOnlyConfig; c = SipOnlyConfig(\"lab-sip-config.yaml\")'"
    run_test "Load attack config" "python3 -c 'from main import SipOnlyConfig; c = SipOnlyConfig(\"attack-sip-config.yaml\")'"
}

# Main test function
main() {
    log_info "StormShadow SIP-Only Test Suite"
    log_info "================================="
    
    test_python
    test_config
    test_scripts
    test_system
    test_main
    test_gui
    test_config_loading
    
    log_info ""
    log_info "================================="
    log_info "Test Results:"
    log_success "Tests passed: $TESTS_PASSED"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Tests failed: $TESTS_FAILED"
        log_error "Some components may not work correctly"
        exit 1
    else
        log_success "All tests passed! 🎉"
        log_info ""
        log_info "You can now use StormShadow SIP-Only:"
        log_info "  GUI mode:    python3 main.py --mode gui"
        log_info "  Lab mode:    sudo python3 main.py --mode lab"
        log_info "  Attack mode: sudo python3 main.py --mode attack --target-ip <target>"
        exit 0
    fi
}

# Run tests
main "$@"
