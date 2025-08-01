# StormShadow Spoofing Module Architecture

## Clean Production Architecture

This document describes the clean, production-ready spoofing module architecture for StormShadow.

### Core Components

#### Main IP Spoofing (`spoofing.py`)
- **Purpose**: Kernel-level IP spoofing using iptables SNAT/DNAT rules
- **Performance**: Maximum performance by avoiding userspace packet processing
- **Integration**: Uses existing `utils.network.IPTablesManager`
- **Class**: `SpoofingManager`
- **Factory**: `create_sip_spoofer()`

#### Integration Layer (`spoofing_integration.py`)
- **Purpose**: Simple high-level API for enabling/disabling spoofing
- **Functions**: `enable_sip_spoofing()`, `disable_sip_spoofing()`, `is_spoofing_active()`
- **Global State**: Manages spoofing across the entire application
- **StormShadow Integration**: Uses existing core utilities for consistent output

#### Protocol Handlers
- **`base_handler.py`**: Abstract base class for packet handlers
- **`sip_handler.py`**: SIP-specific packet manipulation and parsing
- **`spoofing_manager.py`**: Session management utilities (renamed to SessionManager)

### Simple Import Structure

```python
# Main imports for production use
from utils.spoofing import (
    enable_sip_spoofing,     # Enable kernel-level spoofing
    disable_sip_spoofing,    # Disable and cleanup spoofing
    is_spoofing_active,      # Check current spoofing status
    SpoofingManager,         # Direct access to spoofing manager
    create_sip_spoofer       # Factory function
)

# Protocol-specific handlers
from utils.spoofing import (
    BasePacketHandler,       # Base class for packet handlers
    SIPPacketHandler,        # SIP protocol handler
    SessionManager           # Session management (was spoofing_manager)
)
```

### Usage Examples

#### Simple Integration
```python
# Enable spoofing before attacks
enable_sip_spoofing("10.10.123.0/25", "143.53.142.93")

# Run your SIP attacks - packets automatically spoofed at kernel level
# ... attack code ...

# Clean up when done
disable_sip_spoofing()
```

#### Advanced Usage
```python
# Create custom spoofer
spoofer = create_sip_spoofer(
    spoofed_subnet="192.168.1.0/24",
    attacker_ip="203.0.113.1"
)

# Enable spoofing
spoofer.enable_spoofing()

# Get statistics
stats = spoofer.get_statistics()
print(f"Active: {stats['active']}")
print(f"Available IPs: {stats['available_spoofed_ips']}")

# Disable when done
spoofer.disable_spoofing()
```

### Performance Benefits

1. **Kernel-Level Processing**: No userspace packet copying
2. **Existing Infrastructure**: Leverages proven `IPTablesManager`
3. **Minimal Overhead**: SNAT/DNAT rules handle spoofing automatically
4. **Clean Architecture**: Single purpose, well-defined components

### Testing

Use the provided test script to validate the system:

```bash
sudo python3 test_ip_spoofing.py
```

This test validates:
- ✅ Spoofing enable/disable functionality
- ✅ Status monitoring and reporting
- ✅ Proper cleanup and rule management
- ✅ Integration with existing StormShadow utilities

### File Structure

```
utils/spoofing/
├── __init__.py                 # Clean exports with simplified naming
├── spoofing.py                 # Main IP spoofing system
├── spoofing_integration.py     # Simple integration API
├── base_handler.py             # Protocol handler base class
├── sip_handler.py              # SIP protocol specific handling
├── spoofing_manager.py         # Session management utilities (SessionManager)
└── README.md                   # This documentation
```

### Key Improvements

1. **Simplified Naming**: Removed "HighPerformance" prefix since there's only one spoofer
2. **Clean API**: `create_sip_spoofer()` instead of `create_high_performance_sip_spoofer()`
3. **Consistent Classes**: `SpoofingManager` instead of `HighPerformanceSpoofingManager`
4. **Removed Duplicates**: Eliminated redundant implementations
5. **Single Source**: Only one spoofing implementation for consistency

This architecture provides maximum performance while maintaining clean, maintainable code that integrates seamlessly with existing StormShadow infrastructure.
