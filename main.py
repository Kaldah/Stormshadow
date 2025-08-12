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

from pathlib import Path
import sys
import platform
import argparse
from typing import Optional
from types import FrameType

from utils.config.config import Parameters
from utils.core.printing import print_in_dev, print_info
from utils.core.stormshadow import StormShadow

import signal

def print_banner() -> None:
    """Print application banner."""
    print_info(f"""
╔══════════════════════════════════════════════════════════════╗
║                    StormShadow SIP-Only                      ║
║                  Simplified SIP Testing                      ║
║                                                              ║
║  Platform: {platform.system():<50}║
║  Modular shell scripts with simplified configuration         ║
╚══════════════════════════════════════════════════════════════╝
    """)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="StormShadow SIP-Only - Modular SIP Attack / Lab Testing Toolkit",
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

  # Run with venv
  sudo /home/[username]/venvs/[venv_name]/bin/python3 main.py --mode attack --attack-name invite-flood
  # Use custom config
  python3 main.py --config attack-sip-config.yaml --mode attack
        """
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["lab", "attack", "both", "gui"],
        default="attack",
        help="Operation mode"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--target-ip",
        help="Target IP address for attack mode"
    )
    parser.add_argument(
        "--target-port",
        type=int,
        help="Target port for attack mode",
    )
    parser.add_argument(
        "--attack-name",
        type=str,
        help="Name of SIP attack module to run (see --mode test for list)"
    )
    parser.add_argument(
        "--verbosity", "-v",
        choices=["quiet", "info", "debug"],
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
    parser.add_argument(
        "--dry-run", "-dr",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable dry run mode"
    )
    parser.add_argument(
        "--attack", "-a",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable attack mode"
    )
    parser.add_argument(
        "--lab", "-l",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable lab mode"
    )
    parser.add_argument(
        "--keep-lab-open", "-klo",
        action=argparse.BooleanOptionalAction,
        help="Keep lab running in terminal even when main program exits"
    )
    parser.add_argument(
        "--max_count", "-mc",
        type=int,
        help="Maximum number of attack packets"
    )
    parser.add_argument(
        "--metrics", "-mtr",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable metrics mode"
    )
    parser.add_argument(
        "--defense", "-d",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable defense mode"
    )
    parser.add_argument(
        "--gui", "-g",
        action=argparse.BooleanOptionalAction,
        help="Enable/disable GUI mode"
    )
    parser.add_argument(
        "--log-file", "-lf",
        type=Path,
        help="Path to log file"
    )
    return parser

def argToParameters(args: argparse.Namespace, unknown_args: list[str]) -> Parameters:
    """
    Convert command line arguments to Parameters object.

    Args:
        args: Parsed command line arguments

    Returns:
        Parameters: Parameters object with the provided arguments
    """
    print_info(f"Converting command line parameters to Config: {args}")

    parameters = Parameters()

    # Add unknown args as key-value pairs to params
    i = 0
    while i < len(unknown_args):
        key = unknown_args[i]
        if key.startswith('--'):
            key = key[2:]
        elif key.startswith('-'):
            key = key[1:]
        # Check if next item is a value or another flag
        if i + 1 < len(unknown_args) and not unknown_args[i + 1].startswith('-'):
            value = unknown_args[i + 1]
            i += 2
        else:
            value = True  # flag with no value
            i += 1
        parameters.set(key.replace('-', '_'), value)

    for key, value in vars(args).items():
        if value is not None:
            parameters.set(key, value)

    return parameters

def signal_handler(stormshadow_instance: 'StormShadow'):
    """Create a signal handler that properly cleans up the StormShadow instance."""
    def handler(signum: int, frame: Optional[FrameType]) -> None:
        print_info(f"\nReceived signal {signum}. Initiating clean shutdown...")
        try:
            stormshadow_instance.stop()
        except Exception as e:
            print_info(f"Error during cleanup: {e}")
        finally:
            print_info("Clean shutdown completed.")
            sys.exit(0)
    return handler

def main() -> int:
    """Main entry point."""
    print_banner()

    # Create argument parser
    parser = create_argument_parser()
    args, unknown_args = parser.parse_known_args()
    print_in_dev(f"Parsed args: {args}")
    # Transform CLI args to Parameters
    # params : Parameters = Parameters(vars(args)) # Put None values to every non provided argument

    params : Parameters = argToParameters(args, unknown_args)
    stormshadow = StormShadow(CLI_Args=params, default_config_path=args.config)

    stormshadow.setup()
    
    # Set up signal handlers for clean shutdown
    handler = signal_handler(stormshadow)
    signal.signal(signal.SIGINT, handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, handler)  # Termination signal
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, handler)   # Hangup signal (Unix only)
    if hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, handler)  # Quit signal (Unix only)

    try:
        stormshadow.run()
        
        # Wait for signals (Ctrl+C, SIGTERM, etc.)
        print_info("StormShadow is running. Press Ctrl+C to stop...")
        
        # Block until a signal is received
        signal.pause()
        
    except Exception as e:
        print_info(f"Unexpected error: {e}. Initiating clean shutdown...")
        stormshadow.stop()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit((main()))
