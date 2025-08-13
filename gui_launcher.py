#!/usr/bin/env python3
"""
StormShadow GUI Launcher

A simple launcher script that starts the StormShadow GUI directly.
This can be used independently of the main CLI application.
"""

import sys
from pathlib import Path

def main():
    """Launch the StormShadow GUI."""
    # Add the project root to the Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        print("🚀 Starting StormShadow GUI...")
        
        # Import and start the GUI
        from gui import StormShadowGUI
        
        # Create and run the GUI application
        app = StormShadowGUI()
        app.run()
        
        print("✅ StormShadow GUI closed successfully.")
        return 0
        
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        print("💡 Make sure you're in the StormShadow project directory")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 GUI startup interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
