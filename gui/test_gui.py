#!/usr/bin/env python3
"""
Quick test script for the StormShadow GUI

This script performs basic checks to ensure the GUI can be imported and started.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all GUI components can be imported."""
    print("Testing GUI imports...")
    
    try:
        # Test core GUI import
        print("  ✓ Importing main GUI...")
        from gui.main_gui import StormShadowGUI
        
        print("  ✓ Importing GUI manager...")
        from gui.managers.gui_storm_manager import GUIStormManager
        
        print("  ✓ Importing components...")
        from gui.components.main_window import MainWindow
        from gui.components.attack_panel import AttackPanel
        from gui.components.lab_panel import LabPanel
        from gui.components.status_panel import StatusPanel
        from gui.components.menu_bar import MenuBar
        
        print("  ✓ Importing utils...")
        from gui.utils.themes import apply_modern_theme
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_gui_creation():
    """Test that the GUI can be created (but not shown)."""
    print("\nTesting GUI creation...")
    
    try:
        from gui.main_gui import StormShadowGUI
        
        # Create GUI instance (but don't run main loop)
        print("  ✓ Creating GUI instance...")
        app = StormShadowGUI()
        
        print("  ✓ GUI created successfully!")
        
        # Clean up
        app.root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI creation error: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    print("\nTesting dependencies...")
    
    try:
        import tkinter
        print("  ✓ tkinter available")
        
        import tkinter.ttk
        print("  ✓ tkinter.ttk available")
        
        # Test utils imports
        from utils.config.config import Parameters
        print("  ✓ StormShadow utils available")
        
        from utils.core.stormshadow import StormShadow
        print("  ✓ StormShadow core available")
        
        print("✅ All dependencies available!")
        return True
        
    except ImportError as e:
        print(f"❌ Dependency error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all tests."""
    print("StormShadow GUI Test Suite")
    print("=" * 40)
    
    success = True
    
    # Test dependencies first
    if not test_dependencies():
        success = False
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test GUI creation (only if running in a display environment)
    if os.environ.get('DISPLAY') or sys.platform == 'win32':
        if not test_gui_creation():
            success = False
    else:
        print("\n⚠️  Skipping GUI creation test (no display environment)")
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! GUI is ready to use.")
        print("\nTo start the GUI:")
        print("  python3 main.py --mode gui")
        print("  or")
        print("  python3 gui/main_gui.py")
    else:
        print("❌ Some tests failed. Check errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
