#!/bin/bash
# Cleanup script for lab-only components
# This script removes lab-related iptables rules and stops Docker containers

set -e

# Default configuration
SIP_PORT="${SIP_PORT:-5060}"
SPOOFED_SUBNET="${SPOOFED_SUBNET:-10.10.123.0/25}"
ATTACKER_IP="${ATTACKER_IP:-143.53.142.93}"
ACK_PORT="${ACK_PORT:-4000}"
DOCKER_NAME="${DOCKER_NAME:-stormshadow-sip-server}"

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

log_info "Cleaning up lab components..."

# Clean up return path DNAT rule
iptables -t nat -D OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT" 2>/dev/null && \
    log_info "✓ Removed return path DNAT rule" || \
    log_warn "Return path rule not found or already removed"

# Stop and remove Docker container
if docker ps -q -f name="$DOCKER_NAME" | grep -q .; then
    docker stop "$DOCKER_NAME" && log_info "✓ Stopped Docker container '$DOCKER_NAME'"
    docker rm "$DOCKER_NAME" && log_info "✓ Removed Docker container '$DOCKER_NAME'"
else
    log_warn "Docker container '$DOCKER_NAME' not found or already stopped"
fi

log_info "✓ Lab cleanup completed"
