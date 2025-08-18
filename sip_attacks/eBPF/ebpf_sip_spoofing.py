"""
eBPF-based SIP Packet Spoofing Manager

This module provides a high-performance eBPF-based SIP packet spoofer that replaces
the netfilterqueue approach. It provides the same interface as the original
SipPacketSpoofer class but uses eBPF for kernel-space packet modification.
"""

import os
import socket
from signal import SIGTERM
from subprocess import Popen
from typing import Optional
from ipaddress import ip_network, IPv4Network, IPv6Network

from utils.core.command_runner import run_python
from utils.core.logs import print_debug, print_error, print_success, print_warning, print_info


def wait_ready_signal(queue_num: int, timeout: int = 5):
    """
    Wait for eBPF spoofer to signal ready.
    
    Args:
        queue_num: Queue number for the signal
        timeout: Timeout in seconds
    """
    print_debug(f"Waiting for eBPF spoofer to signal ready on queue {queue_num} with timeout {timeout} seconds")
    sock_path = f'/tmp/spoofer_ready_{queue_num}.sock'
    if os.path.exists(sock_path):
        os.remove(sock_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(sock_path)
    server.settimeout(timeout)

    try:
        data, _ = server.recvfrom(1024)
        if data == b'ready':
            print_debug("eBPF Spoofer signaled ready!")
    except:
        print_warning("Timed out waiting for eBPF spoofer ready signal")
    finally:
        server.close()
        if os.path.exists(sock_path):
            os.remove(sock_path)


class EbpfSipPacketSpoofer:
    """
    eBPF-based SIP packet spoofer that provides the same interface as SipPacketSpoofer
    but uses high-performance eBPF kernel programs for packet modification.
    """

    def __init__(self, 
                 attack_queue_num: int,
                 spoofed_subnet: str,
                 victim_port: int = 0,
                 victim_ip: str = "",
                 attacker_port: int = 0,
                 interface: str = "eth0",
                 open_window: bool = False,
                 session_uid: str | None = None,
                 dry_run: bool = False,
                 verbosity: str = "info"):
        """
        Initialize the eBPF SIP packet spoofer.
        
        Args:
            attack_queue_num: Queue number (for compatibility)
            spoofed_subnet: Subnet to spoof IPs from (e.g., "10.0.0.0/24")
            victim_port: Target port to spoof packets to
            victim_ip: Target IP to spoof packets to
            attacker_port: Source port filter
            interface: Network interface to attach eBPF program to
            open_window: Whether to open in new window
            session_uid: Session UID for tracking
            dry_run: Whether to run in dry run mode
            verbosity: Logging verbosity level
        """
        self.spoofed_subnet: IPv4Network | IPv6Network = ip_network(spoofed_subnet)
        self.attack_queue_num: int = attack_queue_num
        self.attacker_port: int = attacker_port
        self.victim_ip: str = victim_ip
        self.victim_port: int = victim_port
        self.interface: str = interface
        self.dry_run: bool = dry_run
        self.verbosity: str = verbosity
        self.open_window: bool = open_window
        self.session_uid: str | None = session_uid

        self.next_ip_number: int = 0
        self.spoofed_ips: list[str] = [str(ip) for ip in self.spoofed_subnet.hosts()]
        self.spoofer_process: Optional[Popen[bytes]] = None
        self.spoofer_pid: Optional[int] = None

    def set_session_uid(self, session_uid: str) -> None:
        """Set the session UID for this spoofer."""
        self.session_uid = session_uid

    def clean_nfqueue_rules(self) -> None:
        """
        Clean NFQUEUE rules - not needed for eBPF approach.
        This method is kept for compatibility with the original interface.
        """
        print_debug("eBPF spoofer doesn't use NFQUEUE rules, skipping cleanup")

    def stop_spoofing(self) -> bool:
        """
        Stop eBPF spoofing by terminating the spoofer process.

        Returns:
            bool: True if successfully stopped, False otherwise.
        """
        if self.dry_run:
            print_info("Dry run mode: would stop eBPF spoofing")
            return True

        if self.spoofer_process is not None:
            try:
                # Terminate the whole process group (terminal + spoofer)
                p = self.spoofer_process
                pgid = os.getpgid(p.pid)
                os.killpg(pgid, SIGTERM)

                print_debug(f"Terminating eBPF spoofer process group with PID: {self.spoofer_process.pid}")
                
                # Wait for the process to terminate
                return_value = self.spoofer_process.wait(timeout=3)
                if return_value != 0:
                    print_error(f"eBPF spoofer process terminated with non-zero exit code: {return_value}")
                else:
                    print_success("eBPF spoofer process terminated successfully")
                return True
            except Exception as e:
                print_error(f"Error terminating eBPF spoofer process group: {e}")
                return False
        else:
            print_debug("No eBPF spoofer process to terminate")
            return True

    def start_spoofing(self) -> bool:
        """
        Start eBPF spoofing by launching the eBPF spoofer process.

        Returns:
            bool: True if successfully started, False otherwise.
        """
        # Check if spoofing is already running
        if self.spoofer_process is not None:
            self.stop_spoofing()
            print_debug("Stopping existing eBPF spoofing before starting a new one.")

        if self.dry_run:
            print_info("Dry run mode: would start eBPF spoofing process")
            return True

        try:
            print_debug("Starting eBPF spoofer")
            print_debug("Open window: " + str(self.open_window))
            
            # Get the project root directory to ensure correct module paths
            from utils.core.system_utils import get_project_root
            project_root = str(get_project_root())
            
            self.spoofer_process = run_python(
                module="sip_attacks.eBPF.ebpf_spoofer",
                args=[
                    str(self.attack_queue_num),
                    str(self.spoofed_subnet),
                    self.victim_ip,
                    str(self.victim_port),
                    str(self.attacker_port),
                    self.interface,
                    self.verbosity,
                ],
                cwd=project_root,  # Set working directory to project root
                want_sudo=True,
                # When escalating, preserve the current environment (venv) and allow interactive sudo
                sudo_preserve_env=True,
                sudo_non_interactive=False,
                new_terminal=False,
                open_window=self.open_window,
                window_title="eBPF SIP Spoofer",
                interactive=False,
                keep_window_open=True,  # Keep window open to see logs and errors
                dry_run=self.dry_run,
            )

            # Wait for the eBPF spoofer to be ready
            if not self.dry_run:
                wait_ready_signal(self.attack_queue_num)
            return True
        except Exception as e:
            print_warning(f"Failed to start eBPF spoofing on queue {self.attack_queue_num}: {e}")
            return False
