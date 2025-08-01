# utils/core/stormshadow.py

"""StormShadow core orchestrator module.
This module serves as the main entry point for the StormShadow application,
handling the initialization and orchestration of various components.
"""

from typing import Optional
from config.config import Config, ConfigType, Parameters
from utils.attack_manager import AttackManager
from utils.config.config_manager import ConfigManager
from printing import print_info, print_warning, print_error, print_success, print_debug
from utils.lab_manager import LabManager

class StormShadow:
    """
    Main class for the StormShadow application.
    """

    def __init__(self):

        self.configManager = ConfigManager()

        # Load configurations
        self.parameters : Parameters = self.configManager.get_config(ConfigType.APP).parameters

        # If active, a simulation will be run instead of a real attack / lab
        self.dry_run = self.parameters.get("dry_run", False, path=["app"])

        if self.dry_run:
            print_warning("Dry run mode is enabled. No real attacks and no features will be executed.")
            print_warning("This is useful for testing configurations without affecting real systems.")

        self.attack_on = self.parameters.get("attack", path=["enabled"]) # Enable attack mode by default
        self.custom_payload_on = self.parameters.get("custom_payload", path=["enabled"])  # Allow the use of a custom payload for some attacks
        self.spoofing_on = self.parameters.get("spoofing", path=["enabled"])  # Enable spoofing by default

        # Activate lab features
        self.lab_on = self.parameters.get("lab", path=["enabled"])  # Enable lab mode by default
        self.defense_on = self.parameters.get("defense", path=["enabled"])  # Enable defense mode by default
        self.return_path_on = self.parameters.get("return_path", path=["enabled"])  # Enable return path

        # Other features
        self.metrics_on = self.parameters.get("metrics", path=["enabled"])  # Enable metrics collection by default
        self.log_file_on = self.parameters.get("log_file", path=["enabled"])  # Enable logging to a file
        self.metrics_config : Config = self.configManager.get_config(ConfigType.METRICS)
        self.defense_config : Config = self.configManager.get_config(ConfigType.DEFENSE)
        self.gui_config : Config = self.configManager.get_config(ConfigType.GUI)
        self.custom_configs : Config = self.configManager.get_config(ConfigType.CUSTOM)
    
    def update_config(self, config: Config) -> None:
        """
        Update the StormShadow configuration.
        
        Args:
            config: New configuration to apply
        """
        self.configManager.update_config(config)
        self.parameters = self.configManager.get_config(ConfigType.APP).parameters

        # Reinitialize managers with new configuration
        if self.attack_manager:
            self.attack_manager.config = self.configManager.get_config(ConfigType.ATTACK)
        
        if self.lab_manager:
            self.lab_manager.config = self.configManager.get_config(ConfigType.LAB)

    def setup(self, command_config: Optional[Config] = None) -> None:
        """
        Run the StormShadow application.
        """
        print("Starting StormShadow...")
        print_debug(f"Command configuration: {command_config}")

        if command_config != None:
            print_info("Running command with provided configuration...")
            self.update_config(command_config)
        else:
            print_info("Running with default configuration...")

        # Initialize managers based on configuration
        if self.attack_on:
            try:
                print_debug("Attack mode is enabled, initializing attack manager...")
                self.attack_manager = AttackManager(self.configManager.get_config(ConfigType.ATTACK))
            except Exception as e:
                print_error(f"Failed to initialize attack manager: {e}")
                self.attack_manager = None
        else:
            print_debug("Attack mode is disabled.")
            self.attack_manager = None
        
        if self.lab_on:
            try :
                print_debug("Lab mode is enabled, initializing lab manager...")
                self.lab_manager = LabManager(self.configManager.get_config(ConfigType.LAB))
                print_success("Lab mode is enabled.")
            except Exception as e:
                print_error(f"Failed to initialize lab manager: {e}")
                self.lab_manager = None
        else:
            print_debug("Lab mode is disabled.")
            self.lab_manager = None

    def run(self) -> None:
        """
        Start the features of the StormShadow application.
        For CLI mode, this will start the main application loop.
        """
        print("Starting features...")

        if self.lab_on :
            if self.lab_manager:
               try :
                    print_info("Starting lab manager...")
                    self.lab_manager.start()
               except Exception as e:
                    print_error(f"Failed to start lab manager: {e}")
                    self.lab_manager = None
            else:
                print_error("Lab manager is not initialized but should be. Skipping lab features.")

        if self.attack_on :
            if self.attack_manager:
                try:
                    print_info("Starting attack manager...")
                    self.attack_manager.start()
                except Exception as e:
                    print_error(f"Failed to start attack manager: {e}")
                    self.attack_manager = None
            else:
                print_error("Attack manager is not initialized but should be. Skipping attack features.")