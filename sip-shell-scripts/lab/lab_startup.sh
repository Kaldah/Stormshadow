#!/bin/bash
# Enhanced lab startup script

LAB_TYPE=${1:-"docker"}
SIP_PORT=${2:-5060}
DOMAIN=${3:-"example.com"}
CONFIG_FILE=${4:-""}

echo "[+] Starting SIP lab environment"
echo "    - Lab Type: $LAB_TYPE"
echo "    - SIP Port: $SIP_PORT"
echo "    - Domain: $DOMAIN"

case $LAB_TYPE in
    "docker")
        echo "[+] Starting Docker SIP server..."
        
        # Stop existing container if running
        docker stop sip-server 2>/dev/null || true
        docker rm sip-server 2>/dev/null || true
        
        # Check if custom Dockerfile exists
        if [ -f "$(dirname "$0")/../sip-lab/sip_server/Dockerfile" ]; then
            echo "[*] Building custom SIP server image..."
            cd "$(dirname "$0")/../sip-lab/sip_server"
            docker build -t storm-sip-server .
            cd - > /dev/null
            
            echo "[*] Starting custom SIP server container..."
            docker run -d --name sip-server                 -p $SIP_PORT:5060/udp                 -e SIP_DOMAIN=$DOMAIN                 storm-sip-server
        else
            echo "[*] Starting default Asterisk container..."
            docker run -d --name sip-server                 -p $SIP_PORT:5060/udp                 -e SIP_DOMAIN=$DOMAIN                 asterisk/asterisk:latest
        fi
        
        # Wait for container to start
        sleep 3
        
        if docker ps | grep -q sip-server; then
            echo "[+] Docker SIP server started successfully"
            docker logs sip-server --tail 10
        else
            echo "[!] Failed to start Docker SIP server"
            exit 1
        fi
        ;;
        
    "local")
        echo "[+] Starting local SIP server..."
        
        # Try different SIP servers
        if systemctl is-active --quiet asterisk; then
            echo "[*] Asterisk is already running"
        elif command -v asterisk >/dev/null 2>&1; then
            echo "[*] Starting Asterisk..."
            sudo systemctl start asterisk
        elif command -v opensips >/dev/null 2>&1; then
            echo "[*] Starting OpenSIPS..."
            sudo systemctl start opensips
        elif command -v kamailio >/dev/null 2>&1; then
            echo "[*] Starting Kamailio..."
            sudo systemctl start kamailio
        else
            echo "[!] No SIP server found. Please install Asterisk, OpenSIPS, or Kamailio"
            exit 1
        fi
        ;;
        
    "existing")
        echo "[+] Using existing SIP server (no startup needed)"
        ;;
        
    *)
        echo "[!] Unknown lab type: $LAB_TYPE"
        echo "    Supported types: docker, local, existing"
        exit 1
        ;;
esac

echo "[+] Lab environment ready"
