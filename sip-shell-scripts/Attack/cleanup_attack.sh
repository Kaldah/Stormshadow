#!/bin/bash
# Cleanup script for attack-only components
# This script removes attack-related iptables rules

set -e

# Default configuration
ATTACK_QUEUE_NUM="${ATTACK_QUEUE_NUM:-1}"
ACK_RETURN_QUEUE_NUM="${ACK_RETURN_QUEUE_NUM:-2}"
SIP_PORT="${SIP_PORT:-5060}"
ACK_PORT="${ACK_PORT:-4000}"

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Cleaning up attack components..."

# Clean up attack iptables rules
iptables -D OUTPUT -p udp --dport "$SIP_PORT" -j NFQUEUE --queue-num "$ATTACK_QUEUE_NUM" 2>/dev/null && \
    log_info "✓ Removed attack iptables rule" || \
    log_warn "Attack rule not found or already removed"

# Clean up spoofing iptables rules
iptables -D OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM" 2>/dev/null && \
    log_info "✓ Removed spoofing iptables rule" || \
    log_warn "Spoofing rule not found or already removed"

# Kill any running attack processes
pkill -f "sip.*attack" 2>/dev/null && log_info "✓ Stopped attack processes" || log_warn "No attack processes found"

log_info "✓ Attack cleanup completed"
