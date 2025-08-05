from pathlib import Path
from typing import Dict

from utils.core.printing import print_debug, print_warning

def check_attack_module_structure(module_path: Path) -> bool:
    """
    Check if the attack module has the required structure.

    Args:
        module_path: Path to the attack module directory.

    Returns:
        True if the module has the required structure, False otherwise.
    """
    # Check if the module path is a directory
    if not module_path.exists():
        print_warning(f"Module path does not exist: {module_path}")
        return False
    if not module_path.is_dir():
        print_warning(f"Module path is not a directory: {module_path}")
        return False
    return True

def find_attack_modules(attack_modules_folder: Path) -> Dict[str,Path]:
    """
    Discover and return a list of available attack modules.

    Returns:
        A list of Path objects representing the paths to available attack modules folders.
    """
    print_debug(f"Searching for attack modules in: {attack_modules_folder}")
    if not attack_modules_folder.exists() or not attack_modules_folder.is_dir():
        print_warning(f"Attack modules folder does not exist or is not a directory: {attack_modules_folder}")
        return {}
    print_debug(f"Found attack modules folder: {attack_modules_folder}")
    # List all directories in the attack modules folder
    print_debug("Listing all directories in the attack modules folder...")

    attack_modules : Dict[str, Path] = {module.name: module for module in attack_modules_folder.iterdir() if check_attack_module_structure(module)}

    return attack_modules
