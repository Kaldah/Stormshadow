#!/bin/bash
# Network status checker

echo "[+] StormShadow Network Status"
echo "================================"

echo ""
echo "[*] IPTables Rules (filter table):"
sudo iptables -L OUTPUT -n --line-numbers | grep -E "(NFQUEUE|5060|4000)" || echo "    No relevant rules found"

echo ""
echo "[*] IPTables Rules (nat table):"
sudo iptables -t nat -L OUTPUT -n --line-numbers | grep -E "(DNAT|5060)" || echo "    No relevant NAT rules found"

echo ""
echo "[*] IP Forwarding:"
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
    echo "    ✓ Enabled"
else
    echo "    ✗ Disabled"
fi

echo ""
echo "[*] Network Interfaces:"
ip addr show | grep -E "^[0-9]+:|inet " | head -10

echo ""
echo "[*] Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(sip|SIP)" || echo "    No SIP containers found"

echo ""
echo "[*] SIP Services:"
systemctl is-active asterisk opensips kamailio 2>/dev/null | paste <(echo -e "asterisk\nopensips\nkamailio") - || echo "    No SIP services found"

echo ""
echo "[*] Listening Ports:"
netstat -ulnp | grep ":5060" || echo "    Port 5060 not in use"
