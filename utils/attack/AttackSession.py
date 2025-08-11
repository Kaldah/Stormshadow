from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
from types import ModuleType
from typing import Optional, Type

from utils.config.config import Parameters
from utils.core.printing import print_debug, print_error, print_in_dev, print_info, print_success, print_warning
from utils.interfaces.attack_interface import AttackInterface, create_attack_instance
from .attack_enums import AttackProtocol, AttackStatus, AttackType

def find_attack_main_class(module: ModuleType) -> Optional[Type[AttackInterface]]:
    """
    Find the main attack class in the given module.

    Args:
        module: The module to search for the attack class.

    Returns:
        The first class found that implements AttackInterface, or None if not found.
    """
    print_debug("Searching for attack class in module...")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, AttackInterface) and attr is not AttackInterface:
            print_debug(f"Found attack class: {attr_name}")
            return attr  # This is the class with the AttackInterface implementation
    
    print_debug("No attack class found in module.")
    return None

class AttackSession:
    """
    Base class for all attack modules.
    """

    def __init__(self, name: str, main_attack: AttackInterface, enable_spoofing: bool) -> None:
        self.name = name
        self.protocol = AttackProtocol.SIP

        self.main_attack : AttackInterface = main_attack  # Instance of the attack interface

        self.status = AttackStatus.INITIALIZED  # Status of the attack module
        self.own_spoofing = main_attack.spoofing_implemented  # Whether the attack module is already spoofing or not
        self.enable_spoofing = enable_spoofing  # Whether spoofing is enabled or not

    def start(self) -> None:
        """
        Start the attack.
        """
        if self.main_attack.dry_run:
            print_info("Running in dry-run mode, no actual attack will be performed.")
            if not self.main_attack.dry_run_implemented:
                print_warning("Dry-run mode is not implemented for this attack module\nModule content not available in dry-run.")
                return
            else:
                print_info("Dry-run mode is implemented, proceeding with dry-run.")
                self.main_attack.dry_run = True
        print_info(f"Starting attack: {self.name}")
        self.status = AttackStatus.RUNNING
        # Implement logic to start the attack
        print_in_dev(f"Spooging state is set to: {self.enable_spoofing}")
        if self.enable_spoofing:
            print_info("Spoofing is enabled, starting spoofing...")
            self.main_attack.start_spoofing()
        self.main_attack.run()
        print_success(f"Attack {self.name} started successfully.")

    def stop(self) -> None:
        """
        Stop the attack.
        """
        print_info(f"Stopping attack: {self.name}")
        # Implement logic to stop the attack
        try:
            if self.main_attack.dry_run:
                if not self.main_attack.dry_run_implemented:
                    print_warning("Dry-run mode is enabled, no actual attack will be stopped.")
                    return
                else:
                    print_info("Dry-run mode is implemented, proceeding with stopping the (fake) attack.")
            
            self.main_attack.stop()
            self.status = AttackStatus.STOPPED
            print_info(f"Attack {self.name} stopped successfully.")
            if self.enable_spoofing:
                self.main_attack.stop_spoofing()
        except Exception as e:
            print_error(f"Error stopping attack {self.name}: {e}")

    def resume(self) -> None:
        """
        Resume the attack if it was stopped.
        """
        print_info(f"Resuming attack: {self.name}")

        if self.main_attack.dry_run:
            if not self.main_attack.dry_run_implemented:
                print_warning("Dry-run mode is enabled, no actual attack will be resumed.")
                return
            else:
                print_info("Dry-run mode is implemented, proceeding with resuming the (fake) attack.")

        try :
            if self.main_attack.resume_implemented:
                self.status = AttackStatus.RUNNING
                print_info(f"Resuming attack {self.name}...")
                self.main_attack.resume()
                print_info(f"Attack {self.name} resumed successfully.")
            else:
                print_warning(f"Attack {self.name} cannot be resumed, it was not implemented in the attack module.")
        except Exception as e:
            print_error(f"Error resuming attack {self.name}: {e}")
            self.status = AttackStatus.FAILED
            print_error(f"Trying to clean up after failed resume of attack {self.name}.")
            self.main_attack.cleanup()
    
    def cleanup(self) -> None:
        """
        Cleanup resources used by the attack.
        """
        print_info(f"Cleaning up attack: {self.name}")
        # Implement logic to clean up resources
        pass
    def get_status(self) -> AttackStatus:
        """
        Get the status of the attack module.
        """
        return self.status

    def get_name(self) -> str:
        """
        Get the name of the attack module.
        """
        return self.name

    def get_type(self) -> AttackType:
        """
        Get the type of the attack module.
        """
        return self.main_attack.get_attack_type()

def try_loading_main_attack(py_file: Path) -> Optional[Type[AttackInterface]]:
    """
    Try to load the attack module from a specific file.
    
    Args:
        module: Path to the attack module.
    
    Returns:
        An instance of the attack module.
    """
    print_debug(f"Trying to load attack module from {py_file}")
    try:
        spec = spec_from_file_location("attack_module", str(py_file))
        if spec is None:
            print_debug(f"Failed to load attack module from {py_file}: Spec is None")
            return None
        # Dynamically load the module
        attack_module : ModuleType = module_from_spec(spec)
        # Verify if the module has the required interface
        if spec.loader is None:
            print_debug(f"Failed to load attack module from {py_file}: Loader is None")
            return None
        # Load all classes, functions and variables from the module
        print_debug(f"Loading attack module from {py_file}")
        spec.loader.exec_module(attack_module)

        # Look for the main attack class implementing the AttackInterface
        print_debug(f"Looking for main attack class in {py_file}")
        main_attack_class : Optional[Type[AttackInterface]] = find_attack_main_class(attack_module)

        if main_attack_class is None:
            print_warning(f"No valid attack class found in {py_file}")
            return None
        print_info(f"Successfully loaded attack module: {py_file}")
        return main_attack_class

    except Exception as e:
        print_debug(f"Failed to import attack module from {py_file} : {e}")
        return None

def build_attack_from_module(module: Path, attack_params: Parameters, enable_spoofing: bool, open_window: bool = False) -> Optional[AttackSession]:
    """
    Build an attack instance from a module path.
    
    Args:
        module: Path to the attack module.
        attack_params: Parameters for the attack instance.

    Returns:
        An instance of the attack module.
    """

    print_debug(f"Creating attack session from module: {module}")

    if not module.exists():
        print_error(f"Module path does not exist: {module}")
        raise FileNotFoundError(f"Module path does not exist: {module}")
    
    if not module.is_dir():
        print_error(f"Module path is not a directory: {module}")
        raise NotADirectoryError(f"Module path is not a directory: {module}")
    
    # Load the module dynamically
    try:
        main_attack_class: Optional[Type[AttackInterface]] = None
        print_debug(f"Loading attack module from path: {module}")
        print_debug(f"module contents: {list(module.glob('*.py'))}")
        for py_file in module.glob("*.py"):
            found_class = try_loading_main_attack(py_file)
            if found_class is None:
                print_debug(f"No valid attack class found in {py_file}, skipping.")
            else:
                print_debug(f"Found valid attack class in {py_file}: {found_class.__name__}")
                main_attack_class = found_class
                break
                
        if main_attack_class is None:
            print_error(f"No valid attack module found in {module}")
            raise ImportError(f"No valid attack module found in {module}")
        
        # Create an instance of the attack using the class
        main_attack = create_attack_instance(main_attack_class, attack_params)
        
        # Create an instance of the attack session
        attack_session = AttackSession(name=main_attack.attack_name, main_attack=main_attack, enable_spoofing=enable_spoofing)
        print_info(f"Attack session created successfully: {attack_session.get_name()}")
        return attack_session
    except ImportError as e:
        print_error(f"Error importing attack module. No valid attack module found in {module}: {e}")
        return None