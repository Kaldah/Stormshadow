#!/bin/bash
# IP spoofing configuration

INTERFACE=${1:-"eth0"}
SPOOFED_SUBNET=${2:-"10.10.123.0/25"}

echo "[+] Setting up IP spoofing"
echo "    - Interface: $INTERFACE"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"

# Enable IP forwarding
echo "[*] Enabling IP forwarding..."
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null

# Add route for spoofed subnet
echo "[*] Adding route for spoofed subnet..."
sudo ip route add $SPOOFED_SUBNET dev $INTERFACE 2>/dev/null || echo "[*] Route already exists"

# Disable reverse path filtering for the interface
echo "[*] Configuring reverse path filtering..."
echo 0 | sudo tee /proc/sys/net/ipv4/conf/$INTERFACE/rp_filter > /dev/null
echo 0 | sudo tee /proc/sys/net/ipv4/conf/all/rp_filter > /dev/null

echo "[+] IP spoofing configured successfully"
