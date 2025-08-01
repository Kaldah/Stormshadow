#!/bin/bash
# Setup script for packet spoofing
# This script configures iptables rules for spoofed packet handling

set -e

# Default configuration
ACK_RETURN_QUEUE_NUM="${ACK_RETURN_QUEUE_NUM:-2}"
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

cleanup() {
    log_info "Cleaning up spoofing iptables rules..."
    iptables -D OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM" 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Setting up packet spoofing environment..."
log_info "ACK return queue number: $ACK_RETURN_QUEUE_NUM"
log_info "ACK port: $ACK_PORT"

# Remove existing rule if present
iptables -D OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM" 2>/dev/null || true

# Add iptables rule for return traffic
log_info "Adding iptables rule for spoofing return traffic..."
iptables -I OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM"

if [ $? -eq 0 ]; then
    log_info "✓ Spoofing iptables rule added successfully"
else
    log_error "Failed to add spoofing iptables rule"
    exit 1
fi

log_info "Spoofing setup complete."
log_info "Rule will remain active until this script exits or is terminated."

# Keep the script running to maintain the rule
echo "Press Ctrl+C to stop and cleanup..."
while true; do 
    sleep 1
done
