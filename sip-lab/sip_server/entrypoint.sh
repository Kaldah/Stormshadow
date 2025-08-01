#!/bin/sh

echo "[*] Starting Asterisk SIP Server..."
echo "Spoofed Subnet: $SPOOFED_SUBNET"
echo "Return IP     : $RETURN_ADDR"

# Define cleanup function
cleanup() {
    echo "[*] Cleaning up iptables DNAT rule..."
    iptables -t nat -D OUTPUT -p udp --sport 5060 -d "$SPOOFED_SUBNET" \
      -j DNAT --to-destination "$RETURN_ADDR"
    exit
}

# Catch signals: script exit, Ctrl+C, SIGTERM
trap cleanup EXIT INT TERM

# Apply iptables DNAT rule
echo "[*] Applying iptables DNAT rule..."
iptables -t nat -A OUTPUT -p udp --sport 5060 -d "$SPOOFED_SUBNET" \
  -j DNAT --to-destination "$RETURN_ADDR" \
  -m comment --comment "asterisk-dnat"

# Start Asterisk in foreground
exec /usr/sbin/asterisk -f -U asterisk -G asterisk
