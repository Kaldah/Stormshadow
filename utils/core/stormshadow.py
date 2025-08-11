# utils/core/stormshadow.py

"""StormShadow core orchestrator module.
This module serves as the main entry point for the StormShadow application,
handling the initialization and orchestration of various components.
It manages configuration, attack modules, and lab modules, providing a unified interface for the application.
Author: Corentin COUSTY
"""

from pathlib import Path
from typing import Optional

from ..config.config import Config, ConfigType, Parameters
from utils.attack.attack_manager import AttackManager
from utils.config.config_manager import ConfigManager
from .printing import print_info, print_warning, print_error, print_success, print_debug
from utils.lab_manager import LabManager

class StormShadow:
    """
    Main class for the StormShadow application.
    """

    def __init__(self, CLI_Args: Parameters, default_config_path: Optional[Path] = None) -> None:
        print_info("Initializing StormShadow...")
        # Initialize the configuration manager with CLI arguments and default config path
        print_debug("Initializing ConfigManager with CLI arguments and default config path.")        
        self.configManager = ConfigManager(CLI_Args=CLI_Args, default_config_path=default_config_path)
        print_debug("ConfigManager initialized with CLI arguments and default config path.")
        # Load configurations
        print_debug("Loading app configurations...")
        self.parameters : Parameters = self.configManager.get_config(ConfigType.APP).parameters
        print_debug("App configurations loaded successfully.")
        # If active, a simulation will be run instead of a real attack / lab
        self.dry_run = self.parameters.get("dry_run", False, path=["enabled"])

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

    def setup(self) -> None:
        """
        Run the StormShadow application.
        """
        print_info("Starting StormShadow...")

        # Initialize managers based on configuration
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
    
        if self.attack_on:
            try:
                print_debug("Attack mode is enabled, initializing attack manager...")
                attack_modules_path = Path("sip_attacks")
                self.attack_manager = AttackManager(self.configManager.get_config(ConfigType.ATTACK), attack_modules_path, spoofing_enabled=self.spoofing_on, return_path_enabled=self.return_path_on)
                print_success("Attack mode is enabled.")
            except Exception as e:
                print_error(f"Failed to initialize attack manager: {e}")
                self.attack_manager = None
        else:
            print_debug("Attack mode is disabled.")
            self.attack_manager = None

    def run(self) -> None:
        """
        Start the features of the StormShadow application.
        For CLI mode, this will start the main application loop.
        """
        print_info("Starting features...")

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
    
    def stop(self) -> None:
        """
        Stop the features of the StormShadow application.
        For CLI mode, this will stop the main application loop.
        """
        
        print_info("Stopping features...")

        if self.attack_on and self.attack_manager:
            try:
                print_info("Stopping attack manager...")
                self.attack_manager.stop()
            except Exception as e:
                print_error(f"Failed to stop attack manager: {e}")

        if self.lab_on and self.lab_manager:
            try:
                self.lab_manager.stop()
            except Exception as e:
                print_error(f"Failed to stop lab manager: {e}")
