#!/usr/bin/env python3
"""
eBPF-based SIP Packet Spoofer

This module provides a high-performance eBPF-based packet spoofer that replaces
the netfilterqueue approach. It uses TC (Traffic Control) to attach an eBPF program
to the network interface for kernel-space packet modification.
"""

import sys
import time
import signal
import socket
import struct
import subprocess
from pathlib import Path
from typing import List, Optional
from ipaddress import ip_network, IPv4Network, IPv6Network
from types import FrameType

from utils.core.logs import print_debug, print_error, print_info, print_success, print_warning, set_verbosity


class EbpfSpoofer:
    """
    eBPF-based packet spoofer using TC (Traffic Control) for high-performance
    packet modification in kernel space.
    """

    def __init__(self, 
                 attack_queue_num: int, 
                 spoofed_subnet: str, 
                 victim_port: int = 0, 
                 victim_ip: str = "", 
                 attacker_port: int = 0, 
                 interface: str = "eth0"):
        """
        Initialize the eBPF spoofer.
        
        Args:
            attack_queue_num: Queue number (for compatibility, not used in eBPF)
            spoofed_subnet: Subnet to spoof IPs from (e.g., "10.0.0.0/24")
            victim_port: Target port to spoof packets to
            victim_ip: Target IP to spoof packets to  
            attacker_port: Source port filter
            interface: Network interface to attach eBPF program to
        """
        self.spoofed_subnet: IPv4Network | IPv6Network = ip_network(spoofed_subnet)
        self.attack_queue_num: int = attack_queue_num
        self.attacker_port: int = attacker_port
        self.victim_ip: str = victim_ip
        self.victim_port: int = victim_port
        self.interface: str = interface
        
        self.spoofed_ips: List[str] = [str(ip) for ip in self.spoofed_subnet.hosts()]
        self.should_stop: bool = False
        self.tc_configured: bool = False
        
        # Get the directory where this script is located
        self.script_dir = Path(__file__).parent
        self.ebpf_obj_path: Path = self.script_dir / "ebpf_spoofer.o"

    def _compile_ebpf_program(self) -> bool:
        """
        Compile the eBPF program if the object file doesn't exist or is outdated.
        
        Returns:
            bool: True if compilation successful, False otherwise
        """
        ebpf_src = self.script_dir / "ebpf_spoofer.c"
        
        if not ebpf_src.exists():
            print_error(f"eBPF source file not found: {ebpf_src}")
            return False
            
        # Check if we need to compile
        if (self.ebpf_obj_path.exists() and 
            self.ebpf_obj_path.stat().st_mtime > ebpf_src.stat().st_mtime):
            print_debug("eBPF object file is up to date")
            return True
            
        print_info("Compiling eBPF program...")
        
        # Use make to compile the eBPF program
        try:
            result = subprocess.run(
                ["make", "-C", str(self.script_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            print_debug(f"eBPF compilation output: {result.stdout}")
            print_success("eBPF program compiled successfully")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to compile eBPF program: {e}")
            print_error(f"Compilation error: {e.stderr}")
            return False
        except FileNotFoundError:
            print_error("Make command not found. Please install build tools.")
            return False

    def _setup_tc_qdisc(self) -> bool:
        """
        Set up TC qdisc for the interface.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove existing clsact qdisc if it exists (ignore errors)
            subprocess.run(
                ["tc", "qdisc", "del", "dev", self.interface, "clsact"],
                capture_output=True,
                check=False
            )
            
            # Add clsact qdisc
            result = subprocess.run(
                ["tc", "qdisc", "add", "dev", self.interface, "clsact"],
                capture_output=True,
                text=True,
                check=True
            )
            print_debug(f"TC qdisc setup successful: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to setup TC qdisc: {e}")
            print_error(f"TC error: {e.stderr}")
            return False

    def _attach_ebpf_program(self) -> bool:
        """
        Attach the eBPF program to the TC egress hook.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove existing filter if it exists (ignore errors)
            subprocess.run(
                ["tc", "filter", "del", "dev", self.interface, "egress"],
                capture_output=True,
                check=False
            )
            
            # Attach eBPF program
            cmd = [
                "tc", "filter", "add", "dev", self.interface, "egress",
                "bpf", "obj", str(self.ebpf_obj_path), "sec", "tc",
                "direct-action"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print_debug(f"eBPF program attached successfully: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to attach eBPF program: {e}")
            print_error(f"TC error: {e.stderr}")
            return False

    def _configure_ebpf_maps(self) -> bool:
        """
        Configure the eBPF maps with spoofing parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        print_debug("Starting eBPF map configuration...")
        
        # First, verify the eBPF program is loaded
        try:
            result = subprocess.run(["bpftool", "prog", "list"], capture_output=True, text=True, check=True)
            if "sip_spoof" not in result.stdout:
                print_warning("eBPF program 'sip_spoof' not found in loaded programs")
                print_debug("Loaded programs:")
                print_debug(result.stdout)
        except Exception as e:
            print_warning(f"Could not check loaded eBPF programs: {e}")
        
        try:
            # Find the config map
            result = subprocess.run(
                ["bpftool", "map", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            
            config_map_id = None
            spoofed_ips_map_id = None
            
            for line in result.stdout.splitlines():
                if "config_map" in line:
                    config_map_id = line.split(":")[0]
                elif "spoofed_ips_map" in line:
                    spoofed_ips_map_id = line.split(":")[0]
            
            if not config_map_id or not spoofed_ips_map_id:
                print_error("Could not find eBPF maps")
                return False
            
            print_debug(f"Found config map ID: {config_map_id}")
            print_debug(f"Found spoofed IPs map ID: {spoofed_ips_map_id}")
            
            # Configure config map
            # Pack struct according to C structure alignment
            # Try different struct sizes to match eBPF program expectations
            # Start with a simple 20-byte struct (no padding)
            config_value = struct.pack("IHHIII", 
                int.from_bytes(socket.inet_aton(self.victim_ip), "big") if self.victim_ip else 0,
                self.victim_port,
                self.attacker_port,
                len(self.spoofed_ips),
                0,  # next_index
                int(time.time()) & 0x7fffffff  # random_seed (remove enabled flag for now)
            )
            
            print_debug(f"Config struct size: {len(config_value)} bytes")
            print_debug(f"Config value: {config_value.hex()}")
            print_debug(f"Expected struct: victim_ip={self.victim_ip}, victim_port={self.victim_port}, "
                       f"attacker_port={self.attacker_port}, num_ips={len(self.spoofed_ips)}")
            
            # Update config map using file-based approach for better compatibility
            config_hex = config_value.hex()
            key_hex = "00000000"  # Key 0 in hex format
            
            print_debug(f"Config key hex: {key_hex}")
            print_debug(f"Config value hex: {config_hex}")
            print_debug(f"Config value length: {len(config_value)} bytes")
            
            # Create temporary files for bpftool
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                key_file.write(key_hex)
                key_file_path = key_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as value_file:
                value_file.write(config_hex)
                value_file_path = value_file.name
            
            try:
                # Try file-based approach first
                result = subprocess.run([
                    "bpftool", "map", "update", "id", config_map_id,
                    "key", "file", key_file_path,
                    "value", "file", value_file_path
                ], capture_output=True, text=True, check=True)
                print_debug(f"Config map update successful (file-based): {result.stdout}")
            except subprocess.CalledProcessError as e:
                print_warning(f"File-based update failed: {e}")
                print_debug(f"Trying hex-based approach as fallback...")
                
                # Fallback to hex-based approach
                try:
                    result = subprocess.run([
                        "bpftool", "map", "update", "id", config_map_id,
                        "key", "hex", key_hex,
                        "value", "hex", config_hex
                    ], capture_output=True, text=True, check=True)
                    print_debug(f"Config map update successful (hex-based): {result.stdout}")
                except subprocess.CalledProcessError as e2:
                    print_error(f"Config map update failed: {e2}")
                    print_error(f"Error output: {e2.stderr}")
                    print_debug(f"Command that failed: bpftool map update id {config_map_id} key hex {key_hex} value hex {config_hex}")
                    return False
            finally:
                # Clean up temporary files
                import os
                try:
                    os.unlink(key_file_path)
                    os.unlink(value_file_path)
                except:
                    pass
            
            # Configure spoofed IPs map using hex format
            for i, ip_str in enumerate(self.spoofed_ips[:256]):  # Limit to map size
                # Use native endianness to match kernel expectations
                ip_bytes = struct.pack("I", int.from_bytes(socket.inet_aton(ip_str), "big"))
                key_bytes = struct.pack("I", i)  # Use native endianness for key
                
                ip_hex = ip_bytes.hex()
                key_hex = key_bytes.hex()
                
                print_debug(f"IP {i}: {ip_str} -> key:{key_hex}, value:{ip_hex}")
                
                try:
                    subprocess.run([
                        "bpftool", "map", "update", "id", spoofed_ips_map_id,
                        "key", "hex", key_hex,
                        "value", "hex", ip_hex
                    ], capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    print_error(f"Failed to update spoofed IP {i}: {e}")
                    print_error(f"Error output: {e.stderr}")
                    return False
            
            # Cleanup temp files (no longer needed)
            # for temp_file in ["/tmp/ebpf_config", "/tmp/ebpf_config_key", "/tmp/ebpf_ip", "/tmp/ebpf_key"]:
            #     try:
            #         os.unlink(temp_file)
            #     except FileNotFoundError:
            #         pass
            
            print_success(f"Configured eBPF maps with {len(self.spoofed_ips)} spoofed IPs")
            return True
            
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to configure eBPF maps: {e}")
            return False
        except Exception as e:
            print_error(f"Unexpected error configuring eBPF maps: {e}")
            return False

    def start_spoofing(self) -> bool:
        """
        Start the eBPF-based packet spoofing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        print_info("Starting eBPF packet spoofing...")
        
        # Compile eBPF program if needed
        if not self._compile_ebpf_program():
            return False
        
        # Setup TC qdisc
        if not self._setup_tc_qdisc():
            return False
        
        # Attach eBPF program
        if not self._attach_ebpf_program():
            return False
        
        # Configure eBPF maps
        if not self._configure_ebpf_maps():
            return False
        
        self.tc_configured = True
        print_success("eBPF packet spoofing started successfully")
        return True

    def stop_spoofing(self) -> bool:
        """
        Stop the eBPF-based packet spoofing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        print_info("Stopping eBPF packet spoofing...")
        
        try:
            # Remove TC filter
            subprocess.run(
                ["tc", "filter", "del", "dev", self.interface, "egress"],
                capture_output=True,
                check=False
            )
            
            # Remove TC qdisc
            subprocess.run(
                ["tc", "qdisc", "del", "dev", self.interface, "clsact"],
                capture_output=True,
                check=False
            )
            
            self.tc_configured = False
            print_success("eBPF packet spoofing stopped successfully")
            return True
        except Exception as e:
            print_error(f"Error stopping eBPF spoofing: {e}")
            return False

    def send_ready_signal(self, queue_num: int):
        """
        Send ready signal for compatibility with netfilterqueue spoofer.
        
        Args:
            queue_num: Queue number for the signal
        """
        print_debug(f"Sending ready signal for queue {queue_num}")
        sock_path = f'/tmp/spoofer_ready_{queue_num}.sock'
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            client.sendto(b'ready', sock_path)
            client.close()
            print_debug("Ready signal sent successfully")
        except Exception as e:
            print_warning(f"Failed to send ready signal: {e}")

    def cleanup(self, signum: int, frame: Optional[FrameType]):
        """
        Cleanup function for signal handlers.
        
        Args:
            signum: Signal number
            frame: Frame object
        """
        print_info("Cleanup before exit!")
        self.stop_spoofing()
        sys.exit(0)


def main():
    """Main function to run the eBPF spoofer."""
    print_info("Starting the eBPF SIP Spoofer...")
    
    if len(sys.argv) < 7:
        print_info("Usage: python ebpf_spoofer.py [attack_queue_num] [spoofing_subnet] [target_ip] [target_port] [source_port] [interface] [verbosity]")
        sys.exit(1)
    
    attack_queue_num = int(sys.argv[1])
    spoofing_subnet = sys.argv[2]
    target_ip = sys.argv[3]
    target_port = int(sys.argv[4])
    source_port = int(sys.argv[5])
    interface = sys.argv[6]
    
    # Set verbosity if provided (default to "info" if not provided)
    verbosity = sys.argv[7] if len(sys.argv) > 7 else "info"
    set_verbosity(verbosity)
    print_debug(f"eBPF Spoofer verbosity set to: {verbosity}")

    spoofer = EbpfSpoofer(
        attack_queue_num=attack_queue_num,
        spoofed_subnet=spoofing_subnet,
        victim_port=target_port,
        victim_ip=target_ip,
        attacker_port=source_port,
        interface=interface
    )
    
    print_debug(f"Initialized eBPF Spoofer with queue {attack_queue_num}, subnet {spoofing_subnet}, "
                f"target IP {target_ip}, target port {target_port}, source port {source_port}, "
                f"interface {interface}")
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, spoofer.cleanup)
    signal.signal(signal.SIGINT, spoofer.cleanup)

    try:
        # Start eBPF spoofing
        spoofing_started = spoofer.start_spoofing()
        if not spoofing_started:
            print_warning("eBPF spoofing configuration failed, but continuing for compatibility")
        else:
            print_success("eBPF spoofing started successfully")
        
        # Send ready signal for compatibility (always send, even if eBPF config failed)
        spoofer.send_ready_signal(attack_queue_num)
        
        # Keep the program running
        if spoofing_started:
            print_info("eBPF spoofer running with active kernel spoofing. Press Ctrl+C to stop.")
        else:
            print_info("eBPF spoofer running in compatibility mode (no kernel spoofing). Press Ctrl+C to stop.")
        
        while not spoofer.should_stop:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print_info("Keyboard interrupt received, stopping spoofing...")
    except Exception as e:
        print_error(f"Unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        spoofer.stop_spoofing()
        print_success("eBPF Spoofer cleanup completed.")


if __name__ == "__main__":
    main()
