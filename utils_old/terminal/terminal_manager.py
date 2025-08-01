"""
Terminal manager for StormShadow operations.

This module provides high-level terminal management functionality
including command execution, session management, and output handling.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from ..core import print_error, print_warning, print_info, print_success, run_command
from .process_monitor import ProcessMonitor


@dataclass
class TerminalSession:
    """Represents a terminal session."""
    id: str
    name: str
    working_directory: str
    environment: Dict[str, str]
    is_active: bool = True
    start_time: float = 0.0
    last_activity: float = 0.0

    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()
        if self.last_activity == 0.0:
            self.last_activity = time.time()


class TerminalManager:
    """
    Manages terminal operations and sessions.

    Provides methods for:
    - Terminal session management
    - Command execution with environment control
    - Background process management
    - Output capture and monitoring
    """

    def __init__(self):
        """Initialize terminal manager."""
        self.sessions: Dict[str, TerminalSession] = {}
        self.process_monitor = ProcessMonitor()
        self.default_environment = os.environ.copy()
        self._session_counter = 0
        self._lock = threading.Lock()

    def create_session(
        self,
        name: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new terminal session.

        Args:
            name: Session name (auto-generated if None)
            working_directory: Working directory for session
            environment: Environment variables

        Returns:
            str: Session ID
        """
        with self._lock:
            self._session_counter += 1
            session_id = f"session_{self._session_counter}"

            if name is None:
                name = f"Terminal Session {self._session_counter}"

            if working_directory is None:
                working_directory = str(Path.cwd())

            if environment is None:
                environment = self.default_environment.copy()
            else:
                # Merge with default environment
                merged_env = self.default_environment.copy()
                merged_env.update(environment)
                environment = merged_env

            session = TerminalSession(
                id=session_id,
                name=name,
                working_directory=working_directory,
                environment=environment
            )

            self.sessions[session_id] = session
            print_info(f"Created terminal session: {name} ({session_id})")

            return session_id

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """
        Get terminal session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Optional[TerminalSession]: Session object or None
        """
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[TerminalSession]:
        """
        List all terminal sessions.

        Returns:
            List[TerminalSession]: List of active sessions
        """
        return list(self.sessions.values())

    def close_session(self, session_id: str) -> bool:
        """
        Close a terminal session.

        Args:
            session_id: Session identifier

        Returns:
            bool: True if session closed successfully
        """
        session = self.sessions.get(session_id)
        if not session:
            print_warning(f"Session not found: {session_id}")
            return False

        session.is_active = False
        del self.sessions[session_id]
        print_info(f"Closed terminal session: {session.name}")
        return True

    def execute_command(
        self,
        command: str,
        session_id: Optional[str] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
        background: bool = False
    ) -> Any:
        """
        Execute command in terminal session.

        Args:
            command: Command to execute
            session_id: Session to use (creates new if None)
            capture_output: Whether to capture command output
            timeout: Command timeout in seconds
            background: Run command in background

        Returns:
            Command result or process handle for background commands
        """
        # Get or create session
        if session_id is None:
            session_id = self.create_session()

        session = self.get_session(session_id)
        if not session:
            print_error(f"Session not found: {session_id}")
            return None

        # Update session activity
        session.last_activity = time.time()

        print_info(f"Executing command in {session.name}: {command}")

        try:
            if background:
                # Start background process
                process_id = self.process_monitor.start_process(
                    command=command,
                    cwd=session.working_directory,
                    env=session.environment,
                    capture_output=capture_output
                )

                if process_id:
                    print_success(f"Background process started: {process_id}")
                    return process_id
                else:
                    print_error("Failed to start background process")
                    return None
            else:
                # Run synchronous command
                result = run_command(
                    command=command,
                    cwd=session.working_directory,
                    env=session.environment,
                    capture_output=capture_output,
                    timeout=timeout
                )

                if result.returncode == 0:
                    if capture_output:
                        print_success("Command executed successfully")
                    return result
                else:
                    print_error(f"Command failed with exit code {result.returncode}")
                    return result

        except Exception as e:
            print_error(f"Error executing command: {e}")
            return None

    def execute_script(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute a script file.

        Args:
            script_path: Path to script file
            args: Script arguments
            session_id: Session to use
            **kwargs: Additional execution options

        Returns:
            Command result or process handle
        """
        script = Path(script_path)
        if not script.exists():
            print_error(f"Script not found: {script_path}")
            return None

        # Build command
        command_parts = [str(script)]
        if args:
            command_parts.extend(args)

        command = ' '.join(command_parts)

        return self.execute_command(
            command=command,
            session_id=session_id,
            **kwargs
        )

    def change_directory(self, session_id: str, directory: str) -> bool:
        """
        Change working directory for session.

        Args:
            session_id: Session identifier
            directory: New working directory

        Returns:
            bool: True if change successful
        """
        session = self.get_session(session_id)
        if not session:
            print_error(f"Session not found: {session_id}")
            return False

        dir_path = Path(directory)
        if not dir_path.exists():
            print_error(f"Directory does not exist: {directory}")
            return False

        if not dir_path.is_dir():
            print_error(f"Path is not a directory: {directory}")
            return False

        session.working_directory = str(dir_path.absolute())
        session.last_activity = time.time()
        print_info(f"Changed directory to: {session.working_directory}")
        return True

    def set_environment_variable(
        self,
        session_id: str,
        name: str,
        value: str
    ) -> bool:
        """
        Set environment variable for session.

        Args:
            session_id: Session identifier
            name: Variable name
            value: Variable value

        Returns:
            bool: True if set successfully
        """
        session = self.get_session(session_id)
        if not session:
            print_error(f"Session not found: {session_id}")
            return False

        session.environment[name] = value
        session.last_activity = time.time()
        print_info(f"Set environment variable: {name}={value}")
        return True

    def get_environment_variable(
        self,
        session_id: str,
        name: str
    ) -> Optional[str]:
        """
        Get environment variable from session.

        Args:
            session_id: Session identifier
            name: Variable name

        Returns:
            Optional[str]: Variable value or None
        """
        session = self.get_session(session_id)
        if not session:
            print_error(f"Session not found: {session_id}")
            return None

        return session.environment.get(name)

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed session status.

        Args:
            session_id: Session identifier

        Returns:
            Optional[Dict[str, Any]]: Session status or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            'id': session.id,
            'name': session.name,
            'working_directory': session.working_directory,
            'is_active': session.is_active,
            'start_time': session.start_time,
            'last_activity': session.last_activity,
            'uptime': time.time() - session.start_time,
            'idle_time': time.time() - session.last_activity,
            'environment_vars': len(session.environment)
        }

    def cleanup_inactive_sessions(self, max_idle_time: float = 3600) -> int:
        """
        Clean up inactive sessions.

        Args:
            max_idle_time: Maximum idle time in seconds (default: 1 hour)

        Returns:
            int: Number of sessions cleaned up
        """
        current_time = time.time()
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            idle_time = current_time - session.last_activity
            if idle_time > max_idle_time or not session.is_active:
                sessions_to_remove.append(session_id)

        cleaned_count = 0
        for session_id in sessions_to_remove:
            if self.close_session(session_id):
                cleaned_count += 1

        if cleaned_count > 0:
            print_info(f"Cleaned up {cleaned_count} inactive sessions")

        return cleaned_count

    def get_background_processes(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get background processes for session or all sessions.

        Args:
            session_id: Specific session ID (all if None)

        Returns:
            List[Dict[str, Any]]: List of background processes
        """
        return self.process_monitor.list_processes()

    def stop_background_process(self, process_id: str) -> bool:
        """
        Stop a background process.

        Args:
            process_id: Process identifier

        Returns:
            bool: True if process stopped successfully
        """
        return self.process_monitor.stop_process(process_id)

    def get_process_output(self, process_id: str) -> Optional[str]:
        """
        Get output from background process.

        Args:
            process_id: Process identifier

        Returns:
            Optional[str]: Process output or None
        """
        return self.process_monitor.get_process_output(process_id)

    def cleanup_all_sessions(self) -> bool:
        """
        Clean up all sessions and background processes.

        Returns:
            bool: True if cleanup successful
        """
        print_info("Cleaning up all terminal sessions...")

        # Stop all background processes
        self.process_monitor.cleanup_all_processes()

        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.close_session(session_id)

        print_success("All terminal sessions cleaned up")
        return True
