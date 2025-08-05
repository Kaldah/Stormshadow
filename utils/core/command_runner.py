"""
Command runner utilities for StormShadow.

This module provides utilities for executing shell commands safely.
"""

import subprocess
import logging
from typing import Dict, List, Optional, Union, Any
from subprocess import CompletedProcess



def run_command(
    command: Union[str, List[str]],
    capture_output: bool = True,
    check: bool = True,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
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
    try:
        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=capture_output,
            check=check,
            cwd=cwd,
            env=env,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' failed with exit code {e.returncode}")
        logging.error(f"Output: {e.output}")
        logging.error(f"Error: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command '{command}': {e}")
        raise
