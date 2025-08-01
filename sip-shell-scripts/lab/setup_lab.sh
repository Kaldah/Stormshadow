#!/bin/bash
# Setup script for SIP lab (victim) environment
# This script sets up the Docker container for SIP server

set -e

# Default configuration
LAB_CONFIG="${LAB_CONFIG:-lab-sip-config.yaml}"
DOCKER_NAME="${DOCKER_NAME:-stormshadow-sip-server}"
SERVER_IP="${SERVER_IP:-143.53.142.93}"
SPOOFED_SUBNET="${SPOOFED_SUBNET:-10.10.123.0/25}"

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
    log_info "Cleaning up lab setup..."
    docker stop "$DOCKER_NAME" 2>/dev/null || true
    docker rm "$DOCKER_NAME" 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if running as root for Docker operations
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Setting up SIP lab environment..."
log_info "Docker name: $DOCKER_NAME"
log_info "Server IP: $SERVER_IP"
log_info "Spoofed subnet: $SPOOFED_SUBNET"

# Stop existing container if running
docker stop "$DOCKER_NAME" 2>/dev/null || true
docker rm "$DOCKER_NAME" 2>/dev/null || true

# Build the SIP server image if it doesn't exist
if ! docker images | grep -q "stormshadow-sip"; then
    log_info "Building SIP server Docker image..."
    cd sip-lab/sip_server
    docker build -t stormshadow-sip .
    cd ../..
fi

# Run the SIP server container
log_info "Starting SIP server container..."
docker run -d \
    --name "$DOCKER_NAME" \
    --network host \
    --cap-add=NET_ADMIN \
    -e SPOOFED_SUBNET="$SPOOFED_SUBNET" \
    -e RETURN_ADDR="$SERVER_IP" \
    -e RUN_DETACHED="true" \
    stormshadow-sip

# Wait a moment for container to start
sleep 2

# Check if container is running
if docker ps | grep -q "$DOCKER_NAME"; then
    log_info "✓ SIP lab setup completed successfully"
    log_info "Container '$DOCKER_NAME' is running"
    docker logs "$DOCKER_NAME" | tail -5
else
    log_error "Failed to start SIP server container"
    docker logs "$DOCKER_NAME" 2>/dev/null || true
    exit 1
fi

log_info "Lab setup complete. Container will run until stopped."
log_info "To stop the lab, run: sudo docker stop $DOCKER_NAME"
