"""
File utilities for StormShadow.

This module provides utilities for file and directory operations.
"""

import shutil
from pathlib import Path
from typing import Optional, Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        Path: Absolute path to the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj.absolute()


def get_absolute_path(path: Union[str, Path]) -> Path:
    """
    Get the absolute path for a given path.

    Args:
        path: Relative or absolute path

    Returns:
        Path: Absolute path
    """
    return Path(path).absolute()


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists.

    Args:
        path: Path to file

    Returns:
        bool: True if file exists
    """
    return Path(path).is_file()


def directory_exists(path: Union[str, Path]) -> bool:
    """
    Check if a directory exists.

    Args:
        path: Path to directory

    Returns:
        bool: True if directory exists
    """
    return Path(path).is_dir()


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.

    Args:
        path: Path to file

    Returns:
        int: File size in bytes (0 if file doesn't exist)
    """
    try:
        return Path(path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Copy a file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        bool: True if copy successful
    """
    try:
        shutil.copy2(source, destination)
        return True
    except Exception:
        return False


def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Move a file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        bool: True if move successful
    """
    try:
        shutil.move(str(source), str(destination))
        return True
    except Exception:
        return False


def delete_file(path: Union[str, Path]) -> bool:
    """
    Delete a file.

    Args:
        path: Path to file

    Returns:
        bool: True if deletion successful
    """
    try:
        Path(path).unlink()
        return True
    except Exception:
        return False


def delete_directory(path: Union[str, Path], recursive: bool = False) -> bool:
    """
    Delete a directory.

    Args:
        path: Path to directory
        recursive: Whether to delete recursively

    Returns:
        bool: True if deletion successful
    """
    try:
        path_obj = Path(path)
        if recursive:
            shutil.rmtree(path_obj)
        else:
            path_obj.rmdir()
        return True
    except Exception:
        return False


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True
) -> list[Path]:
    """
    Find files matching a pattern in a directory.

    Args:
        directory: Directory to search
        pattern: File pattern (glob)
        recursive: Whether to search recursively

    Returns:
        list[Path]: List of matching file paths
    """
    try:
        path_obj = Path(directory)
        if recursive:
            return list(path_obj.rglob(pattern))
        else:
            return list(path_obj.glob(pattern))
    except Exception:
        return []


def get_project_root() -> Optional[Path]:
    """
    Get the project root directory by looking for common markers.

    Returns:
        Optional[Path]: Project root path or None if not found
    """
    current = Path.cwd()

    # Look for common project markers
    markers = [
        "setup.py",
        "pyproject.toml",
        "requirements.txt",
        ".git",
        "README.md"
    ]

    for parent in [current] + list(current.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent

    return None


def ensure_file_directory(file_path: Union[str, Path]) -> Path:
    """
    Ensure the directory containing a file exists.

    Args:
        file_path: Path to a file

    Returns:
        Path: Absolute path to the file's directory
    """
    file_path_obj = Path(file_path)
    directory = file_path_obj.parent
    return ensure_directory(directory)
