"""
Terminal utilities for StormShadow.

This module provides terminal detection and configuration utilities.
"""

import os
import sys
import shutil
from typing import Dict, Optional, Tuple, List

from ..core import print_error, print_warning, print_info


def get_terminal_info() -> dict:
    """
    Get information about the current terminal.

    Returns:
        dict: Terminal information
    """
    return {
        'term': os.environ.get('TERM', 'unknown'),
        'shell': os.environ.get('SHELL', 'unknown'),
        'user': os.environ.get('USER', 'unknown'),
        'home': os.environ.get('HOME', 'unknown'),
        'pwd': os.getcwd(),
        'is_tty': sys.stdout.isatty(),
        'supports_color': _supports_color(),
        'terminal_size': get_terminal_size(),
        'available_commands': _get_available_commands()
    }


def is_terminal_available() -> bool:
    """
    Check if terminal is available and interactive.

    Returns:
        bool: True if terminal is available
    """
    return (
        sys.stdout.isatty() and
        sys.stdin.isatty() and
        os.environ.get('TERM') is not None
    )


def setup_terminal_environment() -> bool:
    """
    Setup optimal terminal environment.

    Returns:
        bool: True if setup successful
    """
    try:
        # Set basic environment variables if not present
        if not os.environ.get('TERM'):
            os.environ['TERM'] = 'xterm-256color'

        # Enable color support if available
        if _supports_color():
            os.environ['FORCE_COLOR'] = '1'

        print_info("Terminal environment configured")
        return True

    except Exception as e:
        print_error(f"Failed to setup terminal environment: {e}")
        return False


def get_terminal_size() -> Tuple[int, int]:
    """
    Get terminal size (width, height).

    Returns:
        Tuple[int, int]: (width, height) in characters
    """
    try:
        size = shutil.get_terminal_size()
        return (size.columns, size.lines)
    except Exception:
        return (80, 24)  # Default size


def _supports_color() -> bool:
    """
    Check if terminal supports color output.

    Returns:
        bool: True if color is supported
    """
    # Check if NO_COLOR environment variable is set
    if os.environ.get('NO_COLOR'):
        return False

    # Check if FORCE_COLOR is set
    if os.environ.get('FORCE_COLOR'):
        return True

    # Check if stdout is a tty
    if not sys.stdout.isatty():
        return False

    # Check TERM environment variable
    term = os.environ.get('TERM', '').lower()
    if any(color_term in term for color_term in ['color', '256', 'ansi']):
        return True

    # Platform-specific checks
    if sys.platform == 'win32':
        # Windows 10 and later support ANSI escape codes
        try:
            import winver
            version = winver.get_winver()
            return version >= (10, 0, 10586)  # Windows 10 TH2
        except ImportError:
            return False

    return True


def _get_available_commands() -> List[str]:
    """
    Get list of commonly used commands that are available.

    Returns:
        List[str]: List of available commands
    """
    common_commands = [
        'bash', 'sh', 'zsh', 'fish',
        'git', 'docker', 'python', 'python3',
        'pip', 'pip3', 'node', 'npm',
        'curl', 'wget', 'grep', 'awk', 'sed',
        'ps', 'top', 'htop', 'netstat', 'ss',
        'iptables', 'ip', 'ifconfig', 'route',
        'tcpdump', 'wireshark', 'nmap',
        'make', 'cmake', 'gcc', 'g++',
        'vim', 'nano', 'emacs'
    ]

    available = []
    for cmd in common_commands:
        if shutil.which(cmd):
            available.append(cmd)

    return available


def clear_terminal() -> None:
    """Clear the terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def set_terminal_title(title: str) -> None:
    """
    Set terminal window title.

    Args:
        title: Window title to set
    """
    if is_terminal_available():
        # ANSI escape sequence for setting title
        sys.stdout.write(f'\033]0;{title}\007')
        sys.stdout.flush()


def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Get user input with optional default value.

    Args:
        prompt: Input prompt
        default: Default value if user just presses enter

    Returns:
        str: User input or default value
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        user_input = input(full_prompt).strip()

        if not user_input and default:
            return default

        return user_input

    except (KeyboardInterrupt, EOFError):
        print()  # New line after Ctrl+C
        return ""


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user for yes/no confirmation.

    Args:
        prompt: Confirmation prompt
        default: Default response if user just presses enter

    Returns:
        bool: True if user confirmed
    """
    default_text = "Y/n" if default else "y/N"
    full_prompt = f"{prompt} ({default_text}): "

    try:
        response = input(full_prompt).strip().lower()

        if not response:
            return default

        return response in ['y', 'yes', 'true', '1']

    except (KeyboardInterrupt, EOFError):
        print()  # New line after Ctrl+C
        return False


def print_progress_bar(
    iteration: int,
    total: int,
    prefix: str = '',
    suffix: str = '',
    length: int = 50,
    fill: str = '█'
) -> None:
    """
    Print a progress bar.

    Args:
        iteration: Current iteration
        total: Total iterations
        prefix: Prefix string
        suffix: Suffix string
        length: Character length of bar
        fill: Bar fill character
    """
    if total == 0:
        return

    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)

    # Print newline on completion
    if iteration == total:
        print()


def get_command_path(command: str) -> Optional[str]:
    """
    Get full path to a command.

    Args:
        command: Command name

    Returns:
        Optional[str]: Full path to command or None if not found
    """
    return shutil.which(command)


def is_command_available(command: str) -> bool:
    """
    Check if command is available.

    Args:
        command: Command name

    Returns:
        bool: True if command is available
    """
    return shutil.which(command) is not None


def open_new_terminal(command: str, title: str = "StormShadow", working_dir: Optional[str] = None) -> bool:
    """
    Open a new terminal window with a command.

    Args:
        command: Command to run in the new terminal
        title: Terminal window title
        working_dir: Working directory for the new terminal

    Returns:
        bool: True if terminal was opened successfully
    """
    import subprocess
    
    if working_dir is None:
        working_dir = os.getcwd()
    
    # Get the original user when running with sudo
    original_user = os.environ.get('SUDO_USER', None)
    
    # Create a more robust wrapper script
    wrapper_script = f"""#!/bin/bash
cd "{working_dir}"
echo "===== {title} ====="
echo "Working directory: $(pwd)"
echo "Running command: {command}"
echo "=========================="
echo ""

# Run the command with error handling
if {command}; then
    echo ""
    echo "===== Command completed successfully ====="
else
    echo ""
    echo "===== Command failed with exit code: $? ====="
fi

echo ""
echo "Press Enter to close this terminal..."
read -r
"""
    
    # Try different terminal emulators in order of preference
    terminal_commands = []
    
    # Mac-specific terminals
    if sys.platform == 'darwin':
        # macOS Terminal using AppleScript
        applescript = f'''
tell application "Terminal"
    activate
    set newTab to do script "cd '{working_dir}'"
    do script "{command.replace('"', '\\"')}" in newTab
end tell
'''
        terminal_commands.append(['osascript', '-e', applescript])
        
        # iTerm2 if available
        if is_command_available('iterm'):
            iterm_script = f'''
tell application "iTerm"
    activate
    create window with default profile
    tell current session of current window
        write text "cd '{working_dir}'"
        write text "{command.replace('"', '\\"')}"
    end tell
end tell
'''
            terminal_commands.append(['osascript', '-e', iterm_script])
    
    # GNOME Terminal (Linux) - try this first and stop if successful
    if is_command_available('gnome-terminal'):
        # Simple approach without sudo (works in most cases)
        cmd = [
            'gnome-terminal',
            '--title', title,
            '--working-directory', working_dir,
            '--',
            'bash', '-c', wrapper_script
        ]
        
        # Try GNOME Terminal immediately and return if successful
        try:
            env = os.environ.copy()
            print_info(f"Attempting to open GNOME Terminal...")
            
            process = subprocess.Popen(cmd, 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE,
                       env=env)
            
            import time
            time.sleep(0.5)
            
            poll_result = process.poll()
            if poll_result is None or poll_result == 0:
                # GNOME Terminal started successfully
                print_info(f"Opened new GNOME Terminal: {title}")
                return True
            else:
                # GNOME Terminal failed, continue to other terminals
                _, stderr = process.communicate()
                print_warning(f"GNOME Terminal failed with code {poll_result}")
                if stderr:
                    print_warning(f"Error: {stderr.decode().strip()}")
                    
        except Exception as e:
            print_warning(f"Failed to open GNOME Terminal: {e}")
    
    # Only try other terminals if GNOME Terminal failed
    # Konsole (KDE)
    if is_command_available('konsole'):
        cmd = [
            'konsole',
            '--title', title,
            '--workdir', working_dir,
            '-e', 'bash', '-c', wrapper_script
        ]
        
        # If running as root via sudo, run terminal as the original user
        if original_user and os.geteuid() == 0:
            cmd = ['sudo', '-u', original_user, 'DISPLAY=' + os.environ.get('DISPLAY', ':0')] + cmd
            
        terminal_commands.append(cmd)
    
    # xterm (fallback)
    if is_command_available('xterm'):
        cmd = [
            'xterm',
            '-title', title,
            '-hold',  # Keep terminal open
            '-e', 'bash', '-c', wrapper_script
        ]
        
        # If running as root via sudo, run terminal as the original user
        if original_user and os.geteuid() == 0:
            cmd = ['sudo', '-u', original_user, 'DISPLAY=' + os.environ.get('DISPLAY', ':0')] + cmd
            
        terminal_commands.append(cmd)
    
    # Terminator
    if is_command_available('terminator'):
        cmd = [
            'terminator',
            '--title', title,
            '--working-directory', working_dir,
            '-e', f'bash -c "{wrapper_script}"'
        ]
        
        if original_user and os.geteuid() == 0:
            cmd = ['sudo', '-u', original_user, 'DISPLAY=' + os.environ.get('DISPLAY', ':0')] + cmd
            
        terminal_commands.append(cmd)
    
    # Try tmux if available (runs in current terminal)
    if is_command_available('tmux'):
        terminal_commands.append([
            'tmux', 'new-session', '-d', '-s', title.lower().replace(' ', '_'),
            '-c', working_dir, 'bash', '-c', wrapper_script
        ])

    for term_cmd in terminal_commands:
        try:
            # Preserve environment for GUI applications
            env = os.environ.copy()
            
            # Try to preserve display and other GUI environment variables
            if original_user and os.geteuid() == 0:
                env.update({
                    'DISPLAY': os.environ.get('DISPLAY', ':0'),
                    'XAUTHORITY': f'/home/{original_user}/.Xauthority',
                    'USER': original_user,
                    'HOME': f'/home/{original_user}'
                })
            
            print_info(f"Attempting to open terminal with command: {' '.join(term_cmd[:3])}...")
            
            # Start the terminal process
            process = subprocess.Popen(term_cmd, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           env=env)
            
            # For terminals that fork immediately, a successful start (no immediate error) is good enough
            import time
            time.sleep(0.5)  # Shorter wait time
            
            # Check if process failed immediately (exit code available)
            poll_result = process.poll()
            if poll_result is None:
                # Process still running - success!
                print_info(f"Opened new terminal: {title}")
                return True
            elif poll_result == 0:
                # Process exited cleanly (many terminals fork and parent exits with 0) - also success!
                print_info(f"Opened new terminal: {title}")
                return True
            else:
                # Process failed with non-zero exit code
                _, stderr = process.communicate()
                print_warning(f"Terminal process failed with code {poll_result}")
                if stderr:
                    print_warning(f"Error: {stderr.decode().strip()}")
                
        except Exception as e:
            print_warning(f"Failed to open terminal with {term_cmd[0]}: {e}")
            continue
    
    # If all terminal attempts failed, suggest manual approach
    print_error("No suitable terminal emulator found or all failed to start")
    print_info("To run the attack manually, open a new terminal and run:")
    print_info(f"  cd /home/kaldah/Documents/Projets/StormShadow/Python")
    print_info(f"  ./run_attack_terminal.sh")
    return False


def run_in_new_terminal(command: str, 
                       title: str = "StormShadow", 
                       working_dir: Optional[str] = None,
                       persistent: bool = True) -> bool:
    """
    Run a command in a new terminal window.

    Args:
        command: Command to execute
        title: Terminal window title
        working_dir: Working directory
        persistent: Keep terminal open after command finishes

    Returns:
        bool: True if successfully started
    """
    if persistent:
        # Add read command to keep terminal open
        full_command = f'{command}; echo "Command finished. Press Enter to close..."; read'
    else:
        full_command = command
    
    return open_new_terminal(full_command, title, working_dir)
