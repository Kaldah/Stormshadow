#!/bin/bash
# Usage examples for StormShadow SIP-Only

echo "StormShadow SIP-Only - Usage Examples"
echo "====================================="
echo ""

echo "1. GUI Mode (Recommended for beginners):"
echo "   python3 main.py --mode gui"
echo "   # Opens a user-friendly interface"
echo ""

echo "2. Lab Mode (Sets up SIP server for testing):"
echo "   sudo python3 main.py --mode lab"
echo "   # Starts Docker container with SIP server"
echo "   # Sets up return path routing"
echo ""

echo "3. Attack Mode (Prepares for SIP attacks):"
echo "   sudo python3 main.py --mode attack --target-ip 192.168.1.100"
echo "   # Configures iptables for SIP attack traffic"
echo "   # Enables packet spoofing if configured"
echo ""

echo "4. Combined Mode (Lab + Attack):"
echo "   sudo python3 main.py --mode both"
echo "   # Useful for local testing"
echo ""

echo "5. Custom Configuration:"
echo "   python3 main.py --config my-config.yaml --mode attack --target-ip 10.0.0.1"
echo "   # Uses custom configuration file"
echo ""

echo "6. Direct Shell Script Usage:"
echo "   # Lab setup"
echo "   sudo ./sip-shell-scripts/setup_lab.sh"
echo ""
echo "   # Attack setup"
echo "   sudo ./sip-shell-scripts/setup_attack.sh"
echo ""
echo "   # Cleanup everything"
echo "   sudo ./sip-shell-scripts/cleanup_all.sh"
echo ""

echo "7. Environment Variable Override:"
echo "   SERVER_IP=192.168.1.200 sudo python3 main.py --mode lab"
echo "   # Overrides server IP from environment"
echo ""

echo "Configuration Files:"
echo "- sip-stormshadow-config.yaml  (main config)"
echo "- lab-sip-config.yaml          (lab-specific)"
echo "- attack-sip-config.yaml       (attack-specific)"
echo ""

echo "Important Notes:"
echo "- Lab and attack modes require sudo for iptables operations"
echo "- Docker must be running for lab mode"
echo "- Always run cleanup when finished: sudo ./sip-shell-scripts/cleanup_all.sh"
echo "- GUI mode provides the easiest way to manage configurations"
echo ""

echo "For detailed documentation, see README_Simple.md"
