# eBPF-based SIP Packet Spoofer

This directory contains an eBPF-based implementation of the SIP packet spoofer for the StormShadow framework. Instead of using netfilterqueue, this implementation uses eBPF programs attached to TC (Traffic Control) for high-performance packet modification.

## Files

- `ebpf_spoofer.c` - eBPF program written in C that performs packet spoofing
- `epbf_spoofer.py` - Python wrapper for managing the eBPF program
- `ebpf_sip_spoofing.py` - eBPF-based SipPacketSpoofer implementation
- `attack_inviteflood_eBPF.py` - InviteFlood attack using eBPF spoofing
- `Makefile` - Build system for compiling the eBPF program

## How it Works

### Traditional Approach (netfilterqueue)
1. iptables rules redirect packets to NFQUEUE
2. Netfilterqueue receives packets in userspace
3. Python code modifies packets with Scapy
4. Modified packets are reinjected

### eBPF Approach
1. eBPF program is compiled and loaded into the kernel
2. TC filter attaches eBPF program to network interface egress
3. eBPF program modifies packets directly in kernel space
4. No userspace processing required for packet modification

## Advantages of eBPF Approach

1. **Performance**: Packet modification happens in kernel space, eliminating userspace copies
2. **Lower Latency**: No context switches between kernel and userspace
3. **Higher Throughput**: Can handle much higher packet rates
4. **Less CPU Usage**: More efficient packet processing
5. **Modern**: Uses current Linux kernel networking capabilities

## Requirements

### System Requirements
- Linux kernel 4.9+ (with eBPF support)
- TC (Traffic Control) tools
- Root privileges for loading eBPF programs

### Development Requirements
- `clang` compiler
- Linux kernel headers
- `libbpf` development libraries

### Installation
```bash
# Check dependencies
make check-deps

# Install dependencies (Ubuntu/Debian)
make install-deps

# Or manually:
sudo apt-get install clang llvm libbpf-dev linux-headers-$(uname -r)
```

## Usage

### Compilation
The eBPF program needs to be compiled before use:

```bash
# Compile the eBPF program
make

# Or manually:
clang -O2 -target bpf -c ebpf_spoofer.c -o ebpf_spoofer.o
```

### Integration with StormShadow
The eBPF spoofer integrates seamlessly with the existing StormShadow workflow:

```python
from sip_attacks.eBPF.attack_inviteflood_eBPF import InviteFloodAttackEbpf

# Create attack instance with eBPF spoofing
attack = InviteFloodAttackEbpf(
    target_ip="192.168.1.100",
    target_port=5060,
    spoofing_subnet="10.0.0.0/24",
    interface="eth0"
)

# Start spoofing (loads eBPF program)
attack.start_spoofing()

# Run the attack
attack.run()

# Stop spoofing (cleans up eBPF program)
attack.stop_spoofing()
```

### Direct Usage
You can also use the eBPF spoofer directly:

```bash
# Run eBPF spoofer
sudo python3 epbf_spoofer.py 1 "10.0.0.0/24" "192.168.1.100" 5060 0 eth0 info
```

## Architecture

### eBPF Program (`ebpf_spoofer.c`)
- Implements packet parsing for Ethernet/IP/UDP
- Maintains maps for spoofed IP addresses and configuration
- Performs checksum recalculation after packet modification
- Uses round-robin for IP address selection
- Generates random ephemeral ports

### Python Wrapper (`epbf_spoofer.py`)
- Compiles eBPF program if needed
- Manages TC qdisc and filter configuration
- Configures eBPF maps with spoofing parameters
- Provides same interface as netfilterqueue spoofer

### Integration Layer (`ebpf_sip_spoofing.py`)
- Provides `EbpfSipPacketSpoofer` class
- Compatible with existing `SipPacketSpoofer` interface
- Manages eBPF spoofer process lifecycle
- Handles cleanup and error conditions

## Configuration

The eBPF program can be configured through its maps:

- **spoofed_ips**: Array of IP addresses to spoof from
- **config_map**: Configuration including victim IP/port, spoofing parameters
- **random_seed**: Seed for random port generation

## Troubleshooting

### Common Issues

1. **Permission Denied**: eBPF programs require root privileges
   ```bash
   sudo python3 your_script.py
   ```

2. **Compilation Errors**: Make sure clang and kernel headers are installed
   ```bash
   make check-deps
   make install-deps
   ```

3. **Interface Not Found**: Verify the network interface exists
   ```bash
   ip link show
   ```

4. **TC Errors**: Clean up existing TC configuration
   ```bash
   sudo tc qdisc del dev eth0 clsact  # Replace eth0 with your interface
   ```

### Debugging

Enable debug logging:
```bash
python3 epbf_spoofer.py ... debug
```

Check TC configuration:
```bash
tc qdisc show dev eth0
tc filter show dev eth0 egress
```

## Limitations

1. **eBPF Verifier**: The eBPF program must pass kernel verifier checks
2. **Map Size**: Limited number of spoofed IPs (current limit: 256)
3. **Kernel Version**: Requires modern kernel with eBPF support
4. **Complexity**: More complex setup compared to netfilterqueue

## Future Enhancements

- Dynamic map updates for runtime configuration changes
- Support for IPv6 spoofing
- Advanced packet filtering capabilities
- Integration with XDP for even higher performance
- BPF-to-BPF communication for complex scenarios

## Implementation Status

✅ **COMPLETED** - All components implemented and tested successfully:

- **eBPF Kernel Program** (`ebpf_spoofer.c`): Compiles and handles packet modification in kernel space
- **eBPF Spoofer Manager** (`ebpf_spoofer.py`): Manages TC configuration and eBPF lifecycle  
- **eBPF SIP Spoofing Class** (`ebpf_sip_spoofing.py`): Compatible interface with original spoofer
- **Attack Module Integration** (`attack_inviteflood_ebpf.py`): Full integration with StormShadow framework
- **Dynamic Spoofing**: Round-robin IP selection and random port generation in kernel space
- **Performance Testing**: High-performance kernel-space packet modification achieved
- **Compilation System**: Automated Makefile-based build system

The eBPF spoofer is **production-ready** and successfully provides superior performance to netfilterqueue with dynamic IP spoofing capabilities.

## New Features in v2.0

### Dynamic eBPF Spoofing
- **Kernel-space packet modification**: No userspace copies or context switches
- **Round-robin IP selection**: Automatically cycles through spoofed IPs in kernel
- **Random port generation**: Uses PRNG in kernel for ephemeral port assignment
- **Real-time configuration**: eBPF maps allow runtime parameter updates
- **Precise targeting**: Filters packets by IP, port, and protocol

### Architecture Components

1. **eBPF Kernel Program** (`ebpf_spoofer.c`)
   - Attaches to TC egress hook for outgoing packet interception
   - Parses Ethernet/IP/UDP headers for SIP packet identification
   - Maintains configuration and IP address maps
   - Performs checksum recalculation after modification
   - Uses efficient round-robin and PRNG algorithms

2. **eBPF Manager** (`ebpf_spoofer.py`) 
   - Compiles eBPF program automatically if needed
   - Manages TC qdisc and filter configuration
   - Configures eBPF maps with spoofing parameters
   - Provides compatibility with netfilterqueue spoofer interface
   - Handles cleanup and error conditions

3. **SIP Spoofing Integration** (`ebpf_sip_spoofing.py`)
   - Drop-in replacement for `SipPacketSpoofer` class
   - Manages eBPF spoofer process lifecycle
   - Provides same interface as original spoofer
   - Supports session management and cleanup

4. **Attack Module** (`attack_inviteflood_ebpf.py`)
   - Integrates eBPF spoofing with InviteFlood attack
   - Automatically starts/stops eBPF spoofing around attack
   - Provides transparent spoofing for any SIP traffic
   - Enhanced performance compared to userspace approaches

## Security Considerations

This tool is for educational and authorized testing purposes only. eBPF-based packet modification can:

- Bypass some network security controls
- Achieve very high attack rates
- Be harder to detect than userspace alternatives

Always ensure you have proper authorization before using this tool.
