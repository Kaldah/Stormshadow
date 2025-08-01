"""
This module defines the configuration management system for the StormShadow application.
It includes configuration types and data structures.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
from ..core.printing import print_debug, print_info, print_warning

class ConfigType(Enum):
    DEFAULT = "default"
    APP = "app"
    LOG = "log"
    GUI = "gui"
    SIP_ATTACK = "sip_attack"
    ATTACK = "sip_attack"
    LAB = "lab"
    METRICS = "metrics"
    DEFENSE = "defense"
    CUSTOM = "custom"

@dataclass
class Parameters(Dict[str, Any]):
    def __init__(self, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize Parameters with an optional dictionary.
        
        Args:
            parameters: Optional dictionary of parameters
        """
        if parameters is None:
            parameters = {}
        super().__init__(parameters)
        self.parameters = self  # Keep reference for existing code
    
    def get(self, name: str, default: Any = None, path: list[str] = []) -> Any:
        """
        Get the value of a parameter by its name with a default value.
        
        Args:
            name: The name of the parameter to retrieve.
            default: The default value to return if the parameter is not found.
        
        Returns:
            The value of the parameter or the default value if not found.
        """

        print_debug(f"Getting parameter '{name}' with default '{default}'")

        def _get_recursive(d: Dict[str, Any], path: list[str]) -> Any:
            if not path:
                print_debug(f"Returning parameter '{name}' with the value from {d}'")
                return Dict.get(d, name, default) # type: ignore
            key = path[0]
            print_debug(f"Checking path '{key}' in parameters")

            if key not in d:
                print_info(f"Path '{key}' not found in parameters, returning default value.")
                return default
           
            else:
                return _get_recursive(d[key], path[1:])

        return _get_recursive(self.parameters, path)

    def set(self, name: str, value: Any, path: list[str] = []) -> None:
        """
        Set the value of a parameter by its name.
        
        Args:
            name: The name of the parameter to set.
            value: The value to assign to the parameter.
        """
        if not isinstance(value, (str, int, float, bool, list, dict)):
            raise ValueError(f"Unsupported type for parameter '{name}': {type(value)}")
        print_debug(f"Setting parameter '{name}' to '{value}' with path '{path}'")
        def _set_recursive(d: Dict[str, Any], path: list[str]) -> None:
            if not path:
                d[name] = value
                return
            
            key = path[0]
            
            if key not in d:
                if len(path) > 1:
                    print_warning(f"Creating new path '{key}' in parameters because it does not exist.")
                    d[key] = {}
                else:
                    print_warning(f"Creating new key '{key}' in parameters because it does not exist.")
                    d[key] = value
                    return
            if len(path) == 1:
                d[key][name] = value
            else:
                _set_recursive(d[key], path[1:])
            
        _set_recursive(self.parameters, path)

@dataclass
class Config:
    # Contain the configuration type
    config_type: ConfigType
    # Contain the configuration data with Parameters-Value pairs
    parameters: Parameters


def UpdateConfig(config: Config, args: Parameters) -> None:
    """
    Convert command line parameters to a Config object.
    
    Args:
        params: Dictionary of command line parameters
    
    Returns:
        Config: Config object with the provided parameters
    """
    print_debug(f"Converting command line parameters to Config: {args}")

    parameters = config.parameters

    for key, value in args.items():
        match key:
            case "mode":
                # Set the mode in the parameters
                print_debug(f"Setting mode to '{value}'")

                match value:
                    case "lab":
                        parameters.set("lab", True, ["app", "enabled"])
                        parameters.set("attack", False, ["app", "enabled"])
                    case "attack":
                        parameters.set("attack", True, ["app", "enabled"])
                        parameters.set("lab", False, ["app", "enabled"])
                    case "both":
                        parameters.set("lab", True, ["app", "enabled"])
                        parameters.set("attack", True, ["app", "enabled"])
                    case "gui":
                        parameters.set("gui", True, ["app", "enabled"])
                    case _ :
                        print_warning(f"Unknown mode '{value}', default parameters will be used.")
                        pass
            case "verbosity":
                # Set the verbosity level
                print_info(f"Setting verbosity level to '{value}'")
                parameters.set("verbosity_level", value, ["log"])
            case "dry_run":
                # Set dry run mode
                print_debug(f"Setting dry run mode to '{value}'")
                parameters.set("dry_run", value, ["app", "enabled"])
            case "target_ip":
                # Set the target IP address
                print_debug(f"Setting target IP to '{value}'")
                parameters.set("target_ip", value, ["attack"])
            case "target_port":
                # Set the target port
                print_debug(f"Setting target port to '{value}'")
                parameters.set("target_port", value, ["attack"])
            case "attack_name":
                # Set the attack name
                print_debug(f"Setting attack name to '{value}'")
                parameters.set("attack_name", value, ["attack"])
            case "spoofing_enabled":
                # Set spoofing enabled/disabled
                print_debug(f"Setting spoofing enabled to '{value}'")
                parameters.set("spoofing", value, ["app", "enabled"])
            case "return_path_enabled":
                # Set return path enabled/disabled
                print_debug(f"Setting return path enabled to '{value}'")
                parameters.set("return_path", value, ["app", "enabled"])
            case "log_file_on":
                # Set log file enabled/disabled
                print_debug(f"Setting log file enabled to '{value}'")
                parameters.set("log_file", value, ["app", "enabled"])
            case "metrics_on":
                # Set metrics enabled/disabled
                print_debug(f"Setting metrics enabled to '{value}'")
                parameters.set("metrics", value, ["app", "enabled"])
            case "log_file":
                # Set log file path
                if isinstance(value, str):
                    print_debug(f"Setting log file path to '{value}'")
                    parameters.set("file", value, ["log"])
            case "log_format":
                # Set log format
                if isinstance(value, str):
                    print_debug(f"Setting log format to '{value}'")
                    print_warning("Not implemented yet, will be set in the logger setup"
                                  "with simple format settings with simple letters like "
                                  "--log_format anlm for asctime, name, levelname and message")
                pass
            
            case _:
                print_debug(f"Setting custom parameter '{key}' to '{value}'")
                parameters.set(key, value, ["custom"])

    config.parameters = parameters
    print_debug(f"Updated config parameters: {config.parameters}")