"""
Command runner utilities for StormShadow.

This module provides utilities for executing shell commands safely.
"""

import logging
import os
import subprocess
from typing import Dict, Optional
from subprocess import CalledProcessError, CompletedProcess, Popen, run

from utils.core.printing import print_debug, print_in_dev
from utils.core.system_utils import check_root

def get_python_launcher(sudo: bool) -> str:
    """
    Get the Python launcher command based on the current environment.
    
    Returns:
        str: The command to launch Python.
    """
    if sudo and check_root():
        sudo_option = "| grep sudo"
    else:
        sudo_option = ""
    command = f"ps -eo pid,ppid,cmd | grep python {sudo_option} | grep main.py"
    # Use subprocess to run the command and capture the output
    # This will return the command used to launch the main.py script
    # We assume the first line of output contains the command we want

    try:
        print_in_dev(f"Running command to get Python launcher: {command}")
        result = run(command, shell=True, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        print_in_dev(f"Output from command to get Python launcher: {lines}")
        if lines:
            if lines[0].split()[2] == "sudo":  # Extract the command part
                # If the command was run with sudo, we include it in the launcher
                return lines[0].split()[2] + " " + lines[0].split()[3]
            else:
                return lines[0].split()[2]  # Extract the command part
        else:
            logging.error("No output from command to get Python launcher.")
            return "python3"
    except Exception as e:
        logging.error(f"Error occurred while getting Python launcher: {e}")
        return "python3"


def run_command(
    command: str,
    capture_output: bool = True,
    check: bool = True,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    sudo: bool = False
) -> CompletedProcess[str]:
    """
    Run a shell command and return the completed process.

    Args:
        command (Union[str, List[str]]): The command to run.
        capture_output (bool): Whether to capture stdout and stderr.
        check (bool): Whether to raise an error on non-zero exit status.
        cwd (Optional[str]): The working directory to run the command in.
        env (Optional[dict]): Environment variables to set for the command.

    Returns:
        CompletedProcess: The result of the executed command.
    """

    if sudo:
        try:
            sudo_prefix = "sudo " * check_root()  # Ensure the function is called with root privileges
        except Exception as e:
            sudo_prefix = ""
        command = sudo_prefix + command 

    try:
        print_debug(f"Trying to run : {command}")
        result = run(
            command,
            shell=True,
            capture_output=capture_output,
            check=check,
            cwd=cwd,
            env=env,
            text=True
        )
        return result
    except CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' failed with exit code {e.returncode}")
        logging.error(f"Output: {e.output}")
        logging.error(f"Error: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command '{command}': {e}")
        raise

def run_process(command: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    sudo: bool = False,
    keep_alive: bool = False,
    new_terminal: bool = False) -> Popen[bytes]:

    """
    Run a shell command in a real terminal (PTY).
    Args:
        command (str): The command to run.
        cwd (str, optional): Working directory.
        env (dict, optional): Environment variables.
    Returns:
        int: The exit code of the command.
    """
    # Print the command to be run in the terminal
    print_in_dev(f"Running command in terminal: {command}")

    if keep_alive:
        print_debug("Keep alive on, terminal will stay open")
        bash_suffix = "; exec bash"
    else:
        bash_suffix = ""

    command = command.strip()

    if sudo:
        try:
            sudo_prefix = "sudo " * check_root()  # Ensure the function is called with root privileges
        except Exception as e:
            print_debug(f"Failed to check root privileges, using empty sudo prefix : {e}")
            sudo_prefix = ""
        if command[:4] != "sudo":
            command = sudo_prefix + command
        else:
            print_debug("Already using sudo")
    if env == None:
        env = dict(os.environ)
        print_debug("Using default environment variables")
    if new_terminal:
        commands = ['gnome-terminal', '--', 'bash', '-c', f'{command}{bash_suffix}']
        print_in_dev(f"Running in new terminal : {commands}")
        return subprocess.Popen(commands, cwd=cwd, env=env)
    else:
        print_debug("Running in background")
        return subprocess.Popen(command, cwd=cwd, env=env)

def run_python_script(file_path: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    sudo: bool = False,
    new_terminal: bool = False,
    keep_alive: bool = False) -> Popen[bytes]:
    """
    Run a shell command in a real terminal (PTY).
    Args:
        command (str): The command to run.
        cwd (str, optional): Working directory.
        env (dict, optional): Environment variables.
    Returns:
        int: The exit code of the command.
    """

    # Print the command to be run in the terminal
    command = get_python_launcher(sudo=sudo) + " " + file_path  # Prepend the Python launcher command used to run the script
    return run_process(command=command, cwd=cwd, sudo=sudo, keep_alive=keep_alive, env=env, new_terminal=new_terminal)
