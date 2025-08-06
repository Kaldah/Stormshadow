import os
from subprocess import CalledProcessError, Popen
from typing import Optional
from ipaddress import ip_network, IPv4Network, IPv6Network
from utils.core.command_runner import run_command, run_python_script
from utils.core.printing import print_debug, print_error, print_in_dev, print_warning
from netfilterqueue import NetfilterQueue
from time import sleep
import socket


def wait_ready_signal(queue_num:int, timeout:int=5):
    sock_path = f'/tmp/spoofer_ready_{queue_num}.sock'
    if os.path.exists(sock_path):
        os.remove(sock_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(sock_path)
    server.settimeout(timeout)  # Use the provided timeout

    try:
        data, _ = server.recvfrom(1024)
        if data == b'ready':
            print_debug("Spoofer signaled ready!")
    except:
        print_warning("Timed out")
    finally:
        server.close()
        os.remove(sock_path)

class SipPacketSpoofer:
    """
    Class to handle packet spoofing using iptables and netfilterqueue.
    """

    def __init__(self, attack_queue_num: int, spoofed_subnet: str, victim_port: int = 0, victim_ip: str = "", attacker_port: int = 0):
        self.spoofed_subnet : IPv4Network | IPv6Network = ip_network(spoofed_subnet)  # Format : xxx.xxx.0/24
        self.attack_queue_num : int = attack_queue_num
        self.attacker_port : int = attacker_port
        self.victim_ip : str = victim_ip
        self.victim_port : int = victim_port

        self.next_ip_number: int = 0
        self.spoofed_ips : list[str] = [str(ip) for ip in self.spoofed_subnet.hosts()]  # List of spoofed IPs in the subnet
        self.netfilter_spoofing_queue: Optional[NetfilterQueue] = None
        self.spoofer_process: Optional[Popen[bytes]] = None

    def stop_spoofing(self) -> bool:
        """
        Deactivate spoofing by removing iptables rules.

        Returns:
            bool: True if the rule was successfully removed, False otherwise.
        """
        source_port = f"--sport {self.attacker_port}" if self.attacker_port != 0 else ""
        dst_ip = f"-d {self.victim_ip}" if self.victim_ip != "" else ""
        dst_port = f"--dport {self.victim_port}" if self.victim_port != 0 else ""

        # Unbind the spoofing function from the queue

        if self.spoofer_process is not None:
            # print_in_dev("Terminating process")
            self.spoofer_process.terminate()

        command = f"iptables -D OUTPUT -p udp {source_port} {dst_ip} {dst_port} -j NFQUEUE --queue-num {self.attack_queue_num}"
        print_debug(f"Deactivating spoofing with command: {command}")
        
        try:
            # Run the command to remove the iptables rule
            run_command(command, capture_output=False, check=True, sudo=True)
            print_debug(f"Successfully deactivated spoofing for packet going to {self.victim_ip}:{self.victim_port} on queue {self.attack_queue_num}")
            return True
        except CalledProcessError as e:
            print_debug(f"Failed to deactivate spoofing - maybe no rules existed: {e}")
            return False
        except Exception as e:
            print_error(f"An unexpected error occurred while deactivating spoofing: {e}")
            return False

    def start_spoofing(self) -> bool:
        """
        Activate spoofing by creating iptables rules to redirect traffic.

        Args:
            receiver_ip: IP address of the receiver.
            receiver_port: Port of the receiver.
            spoofed_subnet: Subnet to be spoofed.
            src_port: Source port of the UDP flow.

        Returns:
            bool: True if the rule was successfully created, False otherwise.
        """

        source_port = f"--sport {self.attacker_port}" if self.attacker_port != 0 else ""
        dst_ip = f"-d {self.victim_ip}" if self.victim_ip != "" else ""
        dst_port = f"--dport {self.victim_port}" if self.victim_port != 0 else ""
        
        # Check if the queue is already set
        if self.netfilter_spoofing_queue is not None:
            self.stop_spoofing()  # Stop any existing spoofing before starting a new one
            print_debug("Stopping existing spoofing before starting a new one.")

        command = f"iptables -A OUTPUT -p udp {source_port} {dst_ip} {dst_port} -j NFQUEUE --queue-num {self.attack_queue_num}"
        print_debug(f"Activating spoofing with command: {command}")
        
        try:
            run_command(command, capture_output=False, check=True, sudo=True)
            print_debug(f"Successfully activated spoofing for packet going to {self.victim_ip}:{self.victim_port} on queue {self.attack_queue_num}")
        except CalledProcessError as e:
            print_warning(f"Failed to activate spoofing: {e}")
            return False
        except Exception as e:
            print_warning(f"An unexpected error occurred while activating spoofing: {e}")
            return False
        try:
            print_debug("Trying to start spoofer")
            self.spoofer_process = run_python_script("-m sip_attacks.spoofer {} {} {} {} {}".format(
                self.attack_queue_num,
                self.spoofed_subnet,
                self.victim_ip,
                self.victim_port,
                self.attacker_port
            ), sudo=True,
            new_terminal=True,
            keep_alive=False,
            env=None
            )
            # We wait for the spoofer to be ready
            wait_ready_signal(self.attack_queue_num)
            return True
        except Exception as e:
            print_warning(f"Failed to bind spoofing function to queue {self.attack_queue_num}: {e}")
            return False
            
