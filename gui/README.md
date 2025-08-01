# StormShadow SIP-Only GUI

A simplified, standalone GUI for running SIP attacks with hardcoded attack paths and simple configuration.

## Features

- **Single Attack Mode**: Focus on one attack at a time with clear status feedback
- **Hardcoded Attack Paths**: No complex configuration needed - attack scripts are predefined
- **Simple Configuration**: Single TOML config file for all settings
- **Real-time Output**: Live output display from running attacks
- **Theme Support**: Light and dark themes
- **Auto-save**: Configuration is automatically saved

## Attack Types Supported

The GUI supports three hardcoded attack types:

1. **InviteFlood**: SIP INVITE flood attack using the `inviteflood` tool
   - Path: `/home/kaldah/Documents/Projets/StormShadow/Python/attack/inviteflood/attack_inviteflood.py`
   
2. **Basic**: Basic SIP attack implementation
   - Path: `/home/kaldah/Documents/Projets/StormShadow/Python/attack/basic/basic_attack.py`
   
3. **Custom**: Your custom attack implementation
   - Path: `/home/kaldah/Documents/Projets/StormShadow/Python/attack/your_attack/your_attack_algo.py`

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The `config.toml` file contains all settings:

```toml
[general]
theme = "light"          # light or dark
log_level = "INFO"
window_width = 1000
window_height = 700

[target]
ip = "192.168.1.100"     # Target SIP server IP
port = 5060              # Target SIP port
domain = "example.com"   # SIP domain

[attacks]
duration = 30            # Attack duration in seconds
rate = 100              # Packets per second
threads = 4             # Number of threads

[inviteflood]
from_user = "attacker"
to_user = "victim"
user_agent = "StormShadow-SIP"
call_id_prefix = "storm"

[basic]
packet_size = 512
timeout = 5

[custom]
payload_type = "custom"
encoding = "utf-8"
```

## Usage

1. **Start the GUI**:
   ```bash
   python sip_only_gui.py
   ```

2. **Configure Target**:
   - Set the target IP address and port
   - Configure the SIP domain if needed

3. **Set Attack Parameters**:
   - Choose attack duration (seconds)
   - Set packet rate (packets per second)
   - Configure number of threads

4. **Select Attack Type**:
   - Choose from InviteFlood, Basic, or Custom attack

5. **Run Attack**:
   - Click "Start Attack" to begin
   - Monitor real-time output in the right panel
   - Click "Stop Attack" to terminate early

6. **Save Configuration**:
   - Click "Save Config" to persist current settings
   - Settings are auto-saved when starting attacks

## File Structure

```
sip_only_gui/
├── sip_only_gui.py      # Main GUI application
├── config_manager.py    # Configuration management
├── attack_runner.py     # Attack execution logic
├── config.toml          # Configuration file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Customizing Attack Paths

To use different attack scripts, modify the `ATTACK_PATHS` dictionary in `attack_runner.py`:

```python
ATTACK_PATHS = {
    "basic": "/path/to/your/basic/attack.py",
    "inviteflood": "/path/to/your/inviteflood/attack.py",
    "custom": "/path/to/your/custom/attack.py"
}
```

## Theme Support

The GUI supports both light and dark themes. Change the theme in the configuration:

```toml
[general]
theme = "dark"  # or "light"
```

## Logging

Log level can be configured in the config file:

```toml
[general]
log_level = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

## Attack Output

The right panel shows:
- **Status**: Current attack status and progress
- **Output**: Real-time output from the running attack command
- **Clear**: Button to clear the output area

## Safety Features

- Confirmation dialog when closing while an attack is running
- Automatic process cleanup when stopping attacks
- Auto-save configuration to prevent data loss

## Troubleshooting

1. **Attack script not found**: Verify the paths in `ATTACK_PATHS` exist
2. **Permission errors**: Ensure the attack scripts are executable
3. **GUI not starting**: Check PySide6 installation with `pip install PySide6`
4. **Config errors**: Delete `config.toml` to regenerate with defaults

## Dependencies

- **PySide6**: Qt6-based GUI framework
- **toml**: TOML configuration file parsing
- **Python 3.8+**: Required for all functionality
