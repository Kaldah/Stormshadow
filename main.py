#!/usr/bin/env python3
"""
StormShadow SIP-Only - Simplified SIP Testing Toolkit

A simplified version of StormShadow focused on SIP attacks with:
- Modular shell scripts for iptables and Docker management
- Simplified configuration with YAML files
- Reuse of existing utils from the main StormShadow project
- Support for lab and attack modes separately or combined

Author: Corentin COUSTY
License: Educational Use Only
"""

import sys
import platform
import argparse
import asyncio

from utils.config.config_manager import ConfigManager
from utils.core.printing import print_info

def print_banner() -> None:
    """Print application banner."""
    print_info(f"""
╔══════════════════════════════════════════════════════════════╗
║                    StormShadow SIP-Only                      ║
║                  Simplified SIP Testing                      ║
║                                                              ║
║  Platform: {platform.system():<50} ║
║  Modular shell scripts with simplified configuration        ║
╚══════════════════════════════════════════════════════════════╝
    """)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="StormShadow SIP-Only - Modular SIP Attack Testing Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run lab (victim) mode
  sudo python3 main.py --mode lab

  # Run attack mode with target
  sudo python3 main.py --mode attack --target-ip 192.168.1.100 --attack-name invite_flood

  # Run both lab and attack
  sudo python3 main.py --mode both

  # Run GUI
  python3 main.py --mode gui

  # Use custom config
  python3 main.py --config attack-sip-config.yaml --mode attack
        """
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["lab", "attack", "both", "gui", "test"],
        default="gui",
        help="Operation mode (default: gui)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--target-ip",
        help="Target IP address for attack mode"
    )
    parser.add_argument(
        "--target-port",
        type=int,
        help="Target port (default: 5060)"
    )
    parser.add_argument(
        "--attack-name",
        type=str,
        help="Name of SIP attack module to run (see --mode test for list)"
    )
    parser.add_argument(
        "--verbosity", "-v",
        choices=["quiet", "info", "debug"],
        default="info",
        help="Logging verbosity level"
    )
    parser.add_argument(
        "--spoofing/--no-spoofing",
        dest="spoofing_enabled",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable spoofing"
    )
    parser.add_argument(
        "--return-path/--no-return-path",
        dest="return_path_enabled", 
        action=argparse.BooleanOptionalAction,
        help="Enable/disable return path"
    )
    return parser


async def main() -> int:
    """Main entry point."""
    print_banner()

    # Load configuration
    config_manager = ConfigManager()
    # Get configurations
    config_manager.get_all_configs()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
