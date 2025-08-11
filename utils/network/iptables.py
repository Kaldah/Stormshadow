


import subprocess

from utils.core.printing import print_debug, print_warning
from utils.core.command_runner import run_command_str

def get_current_iptables_queue_num() -> int:
    """
    Get the current number of packets in the iptables queue.
    """
    command = "iptables -S | grep NFQUEUE"
    try:
        print_debug(f"Running command to check current queue number: {command}")
        result = run_command_str(command, capture_output=True, check=True, want_sudo=True)
        lines = result.stdout.strip().split('\n')
        return max(int(line.split('--queue-num ')[1]) for line in lines if '--queue-num ' in line)
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to get current queue number: {e}")
    except IndexError:
        print_debug("No NFQUEUE rules found in iptables. Assuming queue number is -1 for none.")
    return -1  # Default to -1 if no rules found or an error occurs

def create_matching_queue(queue_num: int, chain: str, dst_port: int) -> bool:
    """
    Match the queue number to a specific iptables rule.

    Args:
        queue_num (int): The queue number to match.
        chain (str): The iptables chain to apply the rule to.
    Returns:
        
    """
    command = f"sudo iptables -I {chain} -p udp --dport {dst_port} -j NFQUEUE --queue-num {queue_num}"
    try:
        print_debug(f"Creating matching queue with command: {command}")
        run_command_str(command, capture_output=False, check=True, want_sudo=True)
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to create matching queue: {e}")
        return False
    except Exception as e:
        print_warning(f"An unexpected error occurred while creating matching queue: {e}")
        return False
    print_debug(f"Successfully created matching queue {queue_num} for chain {chain} on port {dst_port}")
    return True

def activate_return_path(receiver_ip: str, receiver_port: int, spoofed_subnet: str, src_port: int = 0) -> None:
    """
    Activate the return path for a specific UDP flow by modifying iptables rules.

    Args:
        src_port: Source port of the UDP flow.
        dst_ip: Destination IP address of the UDP flow.
        ack_port: Acknowledgment port for the UDP flow.
        spoofed_subnet: Spoofed subnet to use for the return path.
    """
    source_port = ""
    if src_port != 0:
        source_port = f"--sport {src_port}"
    else:
        print_warning("No source port specified, all udp packets will be affected.")
    try:
        command = f"sudo iptables -t nat -I OUTPUT -p udp {source_port} -d {spoofed_subnet} -j DNAT --to-destination {receiver_ip}:{receiver_port}"
        print_debug(f"Activating return path with command: {command}")
        run_command_str(command, capture_output=False, check=True, want_sudo=True)
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to activate return path: {e}")
    
def deactivate_return_path(receiver_ip: str, receiver_port: int, spoofed_subnet: str, src_port: int = 0) -> bool:
    """
    Deactivate the return path for a specific UDP flow by removing iptables rules.

    Args:
        src_port: Source port of the UDP flow.
        dst_ip: Destination IP address of the UDP flow.
        ack_port: Acknowledgment port for the UDP flow.
        spoofed_subnet: Spoofed subnet to use for the return path.

    Returns:
        bool: True if the rule was successfully removed, False otherwise.
    """
    source_port = ""
    if src_port != 0:
        source_port = f"--sport {src_port}"
    else:
        print_warning("No source port specified, all udp packets will be affected.")
    try:
        command = f"sudo iptables -t nat -D OUTPUT -p udp {source_port} -d {spoofed_subnet} -j DNAT --to-destination {receiver_ip}:{receiver_port}"
        print_debug(f"Deactivating return path with command: {command}")
        run_command_str(command, capture_output=False, check=True, want_sudo=True)
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to deactivate return path: {e}")
        return False
    
