#!/bin/bash
# Enhanced cleanup script

echo "[+] Cleaning up StormShadow SIP environment"

# Remove attack iptables rules
echo "[*] Removing attack iptables rules..."
sudo iptables -D OUTPUT -p udp --dport 5060 -j NFQUEUE --queue-num 1 2>/dev/null || true

# Remove return path rules
echo "[*] Removing return path iptables rules..."
sudo iptables -D OUTPUT -p udp --dport 4000 -j NFQUEUE --queue-num 2 2>/dev/null || true

# Remove NAT rules
echo "[*] Removing NAT rules..."
sudo iptables -t nat -D OUTPUT -p udp --sport 5060 -d 10.10.123.0/25 -j DNAT --to-destination 143.53.142.93:4000 2>/dev/null || true

# Stop Docker containers
echo "[*] Stopping SIP lab containers..."
docker stop sip-server 2>/dev/null || true
docker rm sip-server 2>/dev/null || true

# Stop local SIP services
echo "[*] Stopping local SIP services..."
sudo systemctl stop asterisk 2>/dev/null || true
sudo systemctl stop opensips 2>/dev/null || true
sudo systemctl stop kamailio 2>/dev/null || true

# Kill any remaining processes
echo "[*] Cleaning up processes..."
pkill -f "attack_inviteflood" 2>/dev/null || true
pkill -f "inviteflood" 2>/dev/null || true

echo "[+] Cleanup completed"
