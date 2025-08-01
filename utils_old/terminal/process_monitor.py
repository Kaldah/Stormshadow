"""
Process monitor for background process management.

This module provides background process management with output capture
and monitoring capabilities.
"""

import os
import time
import threading
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..core import print_error, print_warning, print_info, print_success


@dataclass
class ProcessInfo:
    """Information about a monitored process."""
    id: str
    pid: Optional[int]
    command: str
    start_time: float
    is_running: bool = True
    exit_code: Optional[int] = None
    output: List[str] = None

    def __post_init__(self):
        if self.output is None:
            self.output = []


class ProcessMonitor:
    """
    Monitors and manages background processes.

    Provides methods for:
    - Starting background processes
    - Monitoring process status
    - Capturing process output
    - Process cleanup
    """

    def __init__(self):
        """Initialize process monitor."""
        self.processes: Dict[str, ProcessInfo] = {}
        self.process_handles: Dict[str, subprocess.Popen] = {}
        self._process_counter = 0
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._start_monitor_thread()

    def _start_monitor_thread(self) -> None:
        """Start the process monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
            self._monitor_thread.start()

    def _monitor_processes(self) -> None:
        """Monitor background processes."""
        while not self._stop_monitoring.wait(1.0):  # Check every second
            with self._lock:
                for process_id in list(self.processes.keys()):
                    self._update_process_status(process_id)

    def _update_process_status(self, process_id: str) -> None:
        """Update status of a specific process."""
        if process_id not in self.processes:
            return

        process_info = self.processes[process_id]
        process_handle = self.process_handles.get(process_id)

        if not process_handle:
            process_info.is_running = False
            return

        # Check if process is still running
        poll_result = process_handle.poll()

        if poll_result is not None:
            # Process has finished
            process_info.is_running = False
            process_info.exit_code = poll_result

            # Capture any remaining output
            try:
                if process_handle.stdout:
                    remaining_output = process_handle.stdout.read()
                    if remaining_output:
                        process_info.output.append(remaining_output)
            except Exception:
                pass  # Ignore errors reading remaining output

    def start_process(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True
    ) -> Optional[str]:
        """
        Start a background process.

        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            capture_output: Whether to capture process output

        Returns:
            Optional[str]: Process ID or None if failed
        """
        with self._lock:
            self._process_counter += 1
            process_id = f"proc_{self._process_counter}"

        print_info(f"Starting background process: {command}")

        try:
            # Prepare subprocess arguments
            kwargs = {
                'shell': True,
                'cwd': cwd,
                'env': env
            }

            if capture_output:
                kwargs.update({
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                    'text': True,
                    'bufsize': 1,  # Line buffered
                    'universal_newlines': True
                })

            # Start process
            process = subprocess.Popen(command, **kwargs)

            # Create process info
            process_info = ProcessInfo(
                id=process_id,
                pid=process.pid,
                command=command,
                start_time=time.time()
            )

            # Store process info and handle
            with self._lock:
                self.processes[process_id] = process_info
                self.process_handles[process_id] = process

            print_success(f"Background process started: {process_id} (PID: {process.pid})")
            return process_id

        except Exception as e:
            print_error(f"Failed to start background process: {e}")
            return None

    def stop_process(self, process_id: str, timeout: float = 10.0) -> bool:
        """
        Stop a background process.

        Args:
            process_id: Process identifier
            timeout: Timeout for graceful shutdown

        Returns:
            bool: True if process stopped successfully
        """
        if process_id not in self.processes:
            print_warning(f"Process not found: {process_id}")
            return False

        process_handle = self.process_handles.get(process_id)
        if not process_handle:
            print_warning(f"Process handle not found: {process_id}")
            return False

        print_info(f"Stopping background process: {process_id}")

        try:
            # Try graceful termination first
            process_handle.terminate()

            try:
                process_handle.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination failed
                print_warning(f"Process {process_id} did not terminate gracefully, killing...")
                process_handle.kill()
                process_handle.wait()

            # Update process info
            process_info = self.processes[process_id]
            process_info.is_running = False
            process_info.exit_code = process_handle.returncode

            print_success(f"Process stopped: {process_id}")
            return True

        except Exception as e:
            print_error(f"Error stopping process {process_id}: {e}")
            return False

    def get_process_output(self, process_id: str) -> Optional[str]:
        """
        Get output from a background process.

        Args:
            process_id: Process identifier

        Returns:
            Optional[str]: Process output or None
        """
        if process_id not in self.processes:
            return None

        process_info = self.processes[process_id]
        process_handle = self.process_handles.get(process_id)

        output_lines = []

        # Get buffered output
        output_lines.extend(process_info.output)

        # Get any new output
        if process_handle and process_handle.stdout:
            try:
                # Read available output without blocking
                import select
                if hasattr(select, 'select'):
                    # Unix-like systems
                    ready, _, _ = select.select([process_handle.stdout], [], [], 0)
                    if ready:
                        line = process_handle.stdout.readline()
                        if line:
                            process_info.output.append(line)
                            output_lines.append(line)
                else:
                    # Windows or other systems - try non-blocking read
                    try:
                        line = process_handle.stdout.readline()
                        if line:
                            process_info.output.append(line)
                            output_lines.append(line)
                    except:
                        pass  # Ignore read errors
            except Exception:
                pass  # Ignore output reading errors

        return ''.join(output_lines) if output_lines else None

    def get_process_info(self, process_id: str) -> Optional[ProcessInfo]:
        """
        Get information about a process.

        Args:
            process_id: Process identifier

        Returns:
            Optional[ProcessInfo]: Process information or None
        """
        return self.processes.get(process_id)

    def list_processes(self) -> List[Dict[str, Any]]:
        """
        List all monitored processes.

        Returns:
            List[Dict[str, Any]]: List of process information
        """
        processes = []

        with self._lock:
            for process_id, process_info in self.processes.items():
                self._update_process_status(process_id)

                processes.append({
                    'id': process_info.id,
                    'pid': process_info.pid,
                    'command': process_info.command,
                    'start_time': process_info.start_time,
                    'is_running': process_info.is_running,
                    'exit_code': process_info.exit_code,
                    'uptime': time.time() - process_info.start_time,
                    'output_lines': len(process_info.output)
                })

        return processes

    def cleanup_finished_processes(self) -> int:
        """
        Clean up finished processes.

        Returns:
            int: Number of processes cleaned up
        """
        cleaned_count = 0

        with self._lock:
            finished_processes = [
                pid for pid, info in self.processes.items()
                if not info.is_running
            ]

            for process_id in finished_processes:
                if process_id in self.process_handles:
                    del self.process_handles[process_id]
                del self.processes[process_id]
                cleaned_count += 1

        if cleaned_count > 0:
            print_info(f"Cleaned up {cleaned_count} finished processes")

        return cleaned_count

    def cleanup_all_processes(self) -> bool:
        """
        Stop and clean up all processes.

        Returns:
            bool: True if cleanup successful
        """
        print_info("Cleaning up all background processes...")

        # Stop monitoring
        self._stop_monitoring.set()

        success = True

        # Stop all running processes
        with self._lock:
            process_ids = list(self.processes.keys())

        for process_id in process_ids:
            if not self.stop_process(process_id):
                success = False

        # Clear all data
        with self._lock:
            self.processes.clear()
            self.process_handles.clear()

        if success:
            print_success("All background processes cleaned up")
        else:
            print_warning("Some processes could not be cleaned up")

        return success

    def __del__(self):
        """Cleanup when object is destroyed."""
        self._stop_monitoring.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
