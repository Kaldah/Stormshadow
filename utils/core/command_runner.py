"""
Command runner utilities for StormShadow.

This module provides utilities for executing shell commands safely.
"""

import subprocess
import logging
from typing import List, Optional, Union, Any
from subprocess import CompletedProcess


def run_command(
    command: Union[str, List[str]],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None
) -> CompletedProcess[str]:
    """
    Execute a shell command safely.

    Args:
        command: Command to execute (string or list of strings)
        check: Whether to raise exception on non-zero exit code
        capture_output: Whether to capture stdout and stderr
        text: Whether to return output as text (vs bytes)
        cwd: Working directory for the command
        env: Environment variables for the command
        timeout: Timeout in seconds

    Returns:
        CompletedProcess: Result of the command execution

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        subprocess.TimeoutExpired: If command times out
    """
    try:
        # Convert string command to list if needed
        if isinstance(command, str):
            command_list = command.split()
        else:
            command_list = command

        logging.debug(f"Executing command: {' '.join(command_list)}")

        result = subprocess.run(
            command_list,
            check=check,
            capture_output=capture_output,
            text=text,
            cwd=cwd,
            env=env,
            timeout=timeout
        )

        if capture_output:
            logging.debug(f"Command output: {result.stdout}")
            if result.stderr:
                logging.debug(f"Command stderr: {result.stderr}")

        return result

    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Return code: {e.returncode}")
        if e.stdout:
            logging.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logging.error(f"Stderr: {e.stderr}")
        raise

    except subprocess.TimeoutExpired as e:
        logging.error(f"Command timed out: {e}")
        raise

    except Exception as e:
        logging.error(f"Unexpected error running command: {e}")
        raise


def run_command_safe(
    command: Union[str, List[str]],
    default_return_code: int = 1,
    **kwargs: Any
) -> CompletedProcess[str]:
    """
    Execute a command safely without raising exceptions.

    Args:
        command: Command to execute
        default_return_code: Return code to use if command fails
        **kwargs: Additional arguments for run_command

    Returns:
        CompletedProcess: Result with guaranteed return code
    """
    try:
        return run_command(command, check=False, **kwargs)
    except Exception as e:
        logging.warning(f"Command execution failed safely: {e}")
        # Return a fake CompletedProcess for safety
        return CompletedProcess(
            args=command if isinstance(command, list) else command.split(),
            returncode=default_return_code,
            stdout="",
            stderr=str(e)
        )


def command_exists(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Args:
        command: Command name to check

    Returns:
        bool: True if command exists
    """
    try:
        result = run_command(
            ["which", command],
            check=False,
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False


def get_command_output(
    command: Union[str, List[str]],
    strip: bool = True,
    **kwargs: Any
) -> str:
    """
    Get the output of a command as a string.

    Args:
        command: Command to execute
        strip: Whether to strip whitespace from output
        **kwargs: Additional arguments for run_command

    Returns:
        str: Command output (empty string if command fails)
    """
    try:
        result = run_command(
            command,
            check=False,
            capture_output=True,
            **kwargs
        )

        if result.returncode == 0 and result.stdout:
            output = result.stdout
            return output.strip() if strip else output

        return ""

    except Exception as e:
        logging.warning(f"Failed to get command output: {e}")
        return ""
