"""
Shell script manager for SIP-Only GUI.
Manages iptables, NAT rules, spoofing, and lab scripts.
"""

import subprocess
import logging
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading


class ShellScriptManager:
    """Manages shell scripts for network configuration and lab setup."""
    
    def __init__(self, config_manager):
        """Initialize shell script manager."""
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.running_scripts: Dict[str, subprocess.Popen] = {}
        
        # Define script paths - these will be created
        self.script_dir = Path(__file__).parent / "scripts"
        self.script_dir.mkdir(exist_ok=True)
        
        # Initialize scripts
        self._create_shell_scripts()
        
    def _create_shell_scripts(self):
        """Create the shell scripts needed for the GUI."""
        
        # Attack iptables rules
        attack_iptables = """#!/bin/bash
# Attack-specific iptables rules

ATTACK_QUEUE_NUM=${1:-1}
SIP_PORT=${2:-5060}
SPOOFED_SUBNET=${3:-"10.10.123.0/25"}

echo "[+] Setting up attack iptables rules"
echo "    - Queue: $ATTACK_QUEUE_NUM"
echo "    - SIP Port: $SIP_PORT"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"

# Match outgoing spoofed attack traffic → destined to SIP port
sudo iptables -I OUTPUT -p udp --dport "$SIP_PORT" -j NFQUEUE --queue-num "$ATTACK_QUEUE_NUM"
echo "[+] Attack iptables rules applied"
"""
        
        # Return path NAT rules
        return_path_nat = """#!/bin/bash
# Return path NAT rules for victim responses

ACK_PORT=${1:-4000}
SIP_PORT=${2:-5060}
SPOOFED_SUBNET=${3:-"10.10.123.0/25"}
ATTACKER_IP=${4:-"192.168.1.100"}

echo "[+] Setting up return path NAT rules"
echo "    - ACK Port: $ACK_PORT"
echo "    - SIP Port: $SIP_PORT"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"
echo "    - Attacker IP: $ATTACKER_IP"

# Redirect Asterisk replies to attacker (DNAT)
sudo iptables -t nat -I OUTPUT -p udp --sport "$SIP_PORT" -d "$SPOOFED_SUBNET" -j DNAT --to-destination "$ATTACKER_IP:$ACK_PORT"
echo "[+] Return path NAT rules applied"
"""
        
        # Spoofing setup
        spoofing_setup = """#!/bin/bash
# IP spoofing configuration

INTERFACE=${1:-"eth0"}
SPOOFED_SUBNET=${2:-"10.10.123.0/25"}

echo "[+] Setting up IP spoofing"
echo "    - Interface: $INTERFACE"
echo "    - Spoofed Subnet: $SPOOFED_SUBNET"

# Enable IP forwarding
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null

# Add route for spoofed subnet
sudo ip route add $SPOOFED_SUBNET dev $INTERFACE 2>/dev/null || true

echo "[+] IP spoofing configured"
"""
        
        # Lab startup script
        lab_startup = """#!/bin/bash
# Lab environment startup

LAB_TYPE=${1:-"docker"}
SIP_PORT=${2:-5060}
DOMAIN=${3:-"example.com"}

echo "[+] Starting lab environment"
echo "    - Lab Type: $LAB_TYPE"
echo "    - SIP Port: $SIP_PORT"
echo "    - Domain: $DOMAIN"

case $LAB_TYPE in
    "docker")
        echo "[+] Starting Docker SIP server..."
        # Check if container exists
        if docker ps -a --format "table {{.Names}}" | grep -q "sip-server"; then
            docker start sip-server
        else
            docker run -d --name sip-server -p $SIP_PORT:5060/udp asterisk/asterisk
        fi
        ;;
    "local")
        echo "[+] Starting local SIP server..."
        # Start local Asterisk or other SIP server
        sudo systemctl start asterisk 2>/dev/null || echo "No Asterisk service found"
        ;;
    *)
        echo "[!] Unknown lab type: $LAB_TYPE"
        exit 1
        ;;
esac

echo "[+] Lab environment started"
"""
        
        # Cleanup script
        cleanup_script = """#!/bin/bash
# Cleanup all rules and processes

echo "[+] Cleaning up network rules and processes"

# Remove iptables rules
echo "[*] Removing attack iptables rules..."
sudo iptables -D OUTPUT -p udp --dport 5060 -j NFQUEUE --queue-num 1 2>/dev/null || true

echo "[*] Removing return path NAT rules..."
sudo iptables -t nat -D OUTPUT -p udp --sport 5060 -d 10.10.123.0/25 -j DNAT --to-destination 192.168.1.100:4000 2>/dev/null || true

# Stop lab containers
echo "[*] Stopping lab containers..."
docker stop sip-server 2>/dev/null || true

echo "[+] Cleanup completed"
"""
        
        # Write scripts
        scripts = {
            "attack_iptables.sh": attack_iptables,
            "return_path_nat.sh": return_path_nat,
            "spoofing_setup.sh": spoofing_setup,
            "lab_startup.sh": lab_startup,
            "cleanup.sh": cleanup_script
        }
        
        for script_name, content in scripts.items():
            script_path = self.script_dir / script_name
            with open(script_path, 'w') as f:
                f.write(content)
            script_path.chmod(0o755)  # Make executable
            
        self.logger.info(f"Created {len(scripts)} shell scripts in {self.script_dir}")
        
    def setup_attack_rules(self, queue_num: int = 1, sip_port: int = 5060, 
                          spoofed_subnet: str = "10.10.123.0/25") -> bool:
        """Set up iptables rules for attack."""
        try:
            script = self.script_dir / "attack_iptables.sh"
            cmd = [str(script), str(queue_num), str(sip_port), spoofed_subnet]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Attack iptables rules applied successfully")
                return True
            else:
                self.logger.error(f"Failed to apply attack rules: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up attack rules: {e}")
            return False
            
    def setup_return_path(self, ack_port: int = 4000, sip_port: int = 5060,
                         spoofed_subnet: str = "10.10.123.0/25", 
                         attacker_ip: str = "192.168.1.100") -> bool:
        """Set up NAT rules for return path."""
        try:
            script = self.script_dir / "return_path_nat.sh"
            cmd = [str(script), str(ack_port), str(sip_port), spoofed_subnet, attacker_ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Return path NAT rules applied successfully")
                return True
            else:
                self.logger.error(f"Failed to apply return path rules: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up return path: {e}")
            return False
            
    def setup_spoofing(self, interface: str = "eth0", 
                      spoofed_subnet: str = "10.10.123.0/25") -> bool:
        """Set up IP spoofing configuration."""
        try:
            script = self.script_dir / "spoofing_setup.sh"
            cmd = [str(script), interface, spoofed_subnet]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("IP spoofing configured successfully")
                return True
            else:
                self.logger.error(f"Failed to setup spoofing: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up spoofing: {e}")
            return False
            
    def start_lab(self, lab_type: str = "docker", sip_port: int = 5060, 
                  domain: str = "example.com") -> bool:
        """Start lab environment."""
        try:
            script = self.script_dir / "lab_startup.sh"
            cmd = [str(script), lab_type, str(sip_port), domain]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Lab environment ({lab_type}) started successfully")
                return True
            else:
                self.logger.error(f"Failed to start lab: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting lab: {e}")
            return False
            
    def cleanup_all(self) -> bool:
        """Clean up all rules and processes."""
        try:
            script = self.script_dir / "cleanup.sh"
            result = subprocess.run([str(script)], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Cleanup completed successfully")
                return True
            else:
                self.logger.error(f"Cleanup failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
            
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network configuration status."""
        status = {
            "iptables_rules": [],
            "nat_rules": [],
            "interfaces": [],
            "docker_containers": []
        }
        
        try:
            # Check iptables rules
            result = subprocess.run(["sudo", "iptables", "-L", "-n"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status["iptables_rules"] = result.stdout.split('\n')
                
            # Check NAT rules
            result = subprocess.run(["sudo", "iptables", "-t", "nat", "-L", "-n"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status["nat_rules"] = result.stdout.split('\n')
                
            # Check network interfaces
            result = subprocess.run(["ip", "addr", "show"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status["interfaces"] = result.stdout.split('\n')
                
            # Check Docker containers
            result = subprocess.run(["docker", "ps", "-a"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status["docker_containers"] = result.stdout.split('\n')
                
        except Exception as e:
            self.logger.error(f"Error getting network status: {e}")
            
        return status
