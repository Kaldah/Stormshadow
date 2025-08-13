#!/usr/bin/env python3
"""
StormShadow SIP-Only GUI Application

A modern Tkinter-based GUI for the StormShadow SIP testing toolkit.
Provides an intuitive interface for running SIP attacks and managing lab environments.

Author: Corentin COUSTY
License: Educational Use Only
"""

import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

# Add the parent directory to sys.path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config.config import Parameters
from utils.core.printing import print_info, print_error, print_success
from utils.core.stormshadow import StormShadow
from gui.components.main_window import MainWindow
from gui.managers.gui_storm_manager import GUIStormManager


class StormShadowGUI:
    """Main GUI application class for StormShadow."""
    
    def __init__(self):
        """Initialize the GUI application."""
        print_info("Initializing StormShadow GUI...")
        
        # Create the main Tkinter root window
        self.root = tk.Tk()
        self.root.title("StormShadow SIP-Only")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Set up the application icon if available
        try:
            # You can add an icon file later
            # self.root.iconbitmap("path/to/icon.ico")
            pass
        except Exception:
            pass
        
        # Initialize the GUI storm manager
        self.gui_manager = GUIStormManager()
        
        # Create the main window components
        self.main_window = MainWindow(self.root, self.gui_manager)
        
        # Configure window closing behavior
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        print_success("StormShadow GUI initialized successfully")
    
    def run(self):
        """Start the GUI application with startup checks."""
        from gui.utils.startup_checks import perform_startup_checks
        
        # Perform startup checks
        if not perform_startup_checks():
            print_info("User chose to exit due to startup check warnings")
            return
        
        try:
            print_info("Starting StormShadow GUI...")
            self.root.mainloop()
        except KeyboardInterrupt:
            print_info("GUI interrupted by user")
        except Exception as e:
            print_error(f"GUI error: {e}")
        finally:
            self._on_closing()
    
    def _on_closing(self):
        """Handle application closing."""
        print_info("Closing StormShadow GUI...")
        
        # Stop any running operations
        self.gui_manager.cleanup()
        
        # Destroy the root window
        self.root.destroy()
        
        print_success("StormShadow GUI closed")


def main():
    """Main entry point for the GUI application."""
    try:
        # Create and run the GUI application
        app = StormShadowGUI()
        app.run()
        return 0
    except KeyboardInterrupt:
        print_info("GUI application interrupted by user")
        return 0
    except Exception as e:
        print_error(f"Failed to start GUI application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
