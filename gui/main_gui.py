"""
Simplified SIP-Only GUI for StormShadow.
Single attack mode with hardcoded attack paths and simple configuration.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QGroupBox,
    QFormLayout, QSpinBox, QLineEdit, QProgressBar, QStatusBar,
    QSplitter, QFrame, QMessageBox, QCheckBox, QRadioButton
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtGui import QFont

# Import our modules
from config_manager import ConfigManager
from attack_runner import AttackRunner
from sip_shell_manager import SipShellManager
from sip_utils_bridge import SipUtilsBridge


class ThreadSafeSignaler(QObject):
    """Thread-safe signaler for communicating between threads and GUI."""
    status_updated = Signal(str)
    output_appended = Signal(str)


class SipOnlyGUI(QMainWindow):
    """Simplified SIP attack GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIP-Only Attack Tool")
        self.setMinimumSize(1000, 700)
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.attack_runner = AttackRunner(self.config_manager)
        self.shell_manager = SipShellManager(self.config_manager)
        self.utils_bridge = SipUtilsBridge(self.config_manager)
        
        self.current_process = None
        self.attack_thread = None
        
        # Connect attack runner signals
        self.attack_runner.output_signal.connect(self.append_output)
        self.attack_runner.finished_signal.connect(self.on_attack_finished)
        self.attack_runner.error_signal.connect(self.on_attack_error)
        
        self.init_ui()
        self.load_config()
        
    def setup_logging(self):
        """Set up logging configuration."""
        log_level = self.config.get("general", "log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Configuration
        config_panel = self.create_config_panel()
        splitter.addWidget(config_panel)
        
        # Right panel - Output and status
        output_panel = self.create_output_panel()
        splitter.addWidget(output_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Apply theme
        self.apply_theme()
        
    def create_config_panel(self) -> QWidget:
        """Create the configuration panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Attack selection
        attack_group = QGroupBox("Attack Configuration")
        attack_layout = QFormLayout()
        attack_group.setLayout(attack_layout)
        
        self.attack_combo = QComboBox()
        self.attack_combo.addItems(["inviteflood", "basic", "custom"])
        attack_layout.addRow("Attack Type:", self.attack_combo)
        
        layout.addWidget(attack_group)
        
        # Target configuration
        target_group = QGroupBox("Target Configuration")
        target_layout = QFormLayout()
        target_group.setLayout(target_layout)
        
        self.target_ip = QLineEdit()
        self.target_port = QSpinBox()
        self.target_port.setRange(1, 65535)
        self.target_domain = QLineEdit()
        
        target_layout.addRow("Target IP:", self.target_ip)
        target_layout.addRow("Target Port:", self.target_port)
        target_layout.addRow("Domain:", self.target_domain)
        
        layout.addWidget(target_group)
        
        # Attack parameters
        params_group = QGroupBox("Attack Parameters")
        params_layout = QFormLayout()
        params_group.setLayout(params_layout)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setSuffix(" seconds")
        
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(1, 10000)
        self.rate_spin.setSuffix(" pps")
        
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 100)
        
        params_layout.addRow("Duration:", self.duration_spin)
        params_layout.addRow("Rate:", self.rate_spin)
        params_layout.addRow("Threads:", self.threads_spin)
        
        layout.addWidget(params_group)
        
        # Enhanced Network Options Section
        network_group = QGroupBox("Network Configuration")
        network_layout = QFormLayout()
        
        # Enable Spoofing checkbox
        self.enable_spoofing = QCheckBox("Enable IP Spoofing")
        self.enable_spoofing.toggled.connect(self.on_spoofing_toggled)
        network_layout.addRow(self.enable_spoofing)
        
        # Return Path Options (hidden by default)
        self.return_path_group = QGroupBox("Return Path Configuration")
        self.return_path_group.setVisible(False)
        return_path_layout = QVBoxLayout()
        
        # Return path radio buttons
        self.return_path_nat = QRadioButton("NAT Translation")
        self.return_path_nat.setChecked(True)
        self.return_path_route = QRadioButton("Custom Routing")
        self.return_path_bridge = QRadioButton("Bridge Mode")
        
        return_path_layout.addWidget(self.return_path_nat)
        return_path_layout.addWidget(self.return_path_route)
        return_path_layout.addWidget(self.return_path_bridge)
        self.return_path_group.setLayout(return_path_layout)
        
        network_layout.addRow(self.return_path_group)
        
        # Lab Management Section
        lab_group = QGroupBox("Lab Management")
        lab_layout = QHBoxLayout()
        
        self.start_lab_btn = QPushButton("Start Lab")
        self.stop_lab_btn = QPushButton("Stop Lab")
        self.lab_status_label = QLabel("Lab Status: Stopped")
        
        self.start_lab_btn.clicked.connect(self.start_lab)
        self.stop_lab_btn.clicked.connect(self.stop_lab)
        
        lab_layout.addWidget(self.start_lab_btn)
        lab_layout.addWidget(self.stop_lab_btn)
        lab_layout.addWidget(self.lab_status_label)
        lab_group.setLayout(lab_layout)
        
        network_layout.addRow(lab_group)
        network_group.setLayout(network_layout)
        
        layout.addWidget(network_group)
        
        # Control buttons
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()
        control_group.setLayout(control_layout)
        
        self.start_button = QPushButton("Start Attack")
        self.start_button.clicked.connect(self.start_attack)
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.stop_button = QPushButton("Stop Attack")
        self.stop_button.clicked.connect(self.stop_attack)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        
        layout.addWidget(control_group)
        
        # Save/Load buttons
        file_group = QGroupBox("Configuration")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)
        
        self.save_button = QPushButton("Save Config")
        self.save_button.clicked.connect(self.save_config)
        
        self.load_button = QPushButton("Load Config")
        self.load_button.clicked.connect(self.load_config)
        
        file_layout.addWidget(self.save_button)
        file_layout.addWidget(self.load_button)
        
        layout.addWidget(file_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def create_output_panel(self) -> QWidget:
        """Create the output panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Status group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #e8f5e8; border-radius: 4px; }")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # Output group
        output_group = QGroupBox("Attack Output")
        output_layout = QVBoxLayout()
        output_group.setLayout(output_layout)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #ffffff; }")
        
        # Clear output button
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        
        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.clear_button)
        
        layout.addWidget(output_group)
        
        return panel
        
    def load_settings(self):
        """Load settings from configuration."""
        # Target settings
        self.target_ip.setText(self.config_manager.get("target", "ip", "192.168.1.100"))
        self.target_port.setValue(self.config_manager.get("target", "port", 5060))
        self.target_domain.setText(self.config_manager.get("target", "domain", "example.com"))
        
        # Attack parameters
        self.duration_spin.setValue(self.config_manager.get("attacks", "duration", 30))
        self.rate_spin.setValue(self.config_manager.get("attacks", "rate", 100))
        self.threads_spin.setValue(self.config_manager.get("attacks", "threads", 4))
        
        # Window size
        width = self.config_manager.get("general", "window_width", 1000)
        height = self.config_manager.get("general", "window_height", 700)
        self.resize(width, height)
        
    def save_config(self):
        """Save current settings to configuration."""
        # Target settings
        self.config_manager.set("target", "ip", self.target_ip.text())
        self.config_manager.set("target", "port", self.target_port.value())
        self.config_manager.set("target", "domain", self.target_domain.text())
        
        # Attack parameters
        self.config_manager.set("attacks", "duration", self.duration_spin.value())
        self.config_manager.set("attacks", "rate", self.rate_spin.value())
        self.config_manager.set("attacks", "threads", self.threads_spin.value())
        
        # Window size
        self.config_manager.set("general", "window_width", self.width())
        self.config_manager.set("general", "window_height", self.height())
        
        # Save to file
        self.config_manager.save_config()
        self.update_status("Configuration saved")
        
    def load_config(self):
        """Load configuration from file."""
        self.config_manager.load_config()
        self.load_settings()
        self.update_status("Configuration loaded")
        
    def on_spoofing_toggled(self, checked):
        """Handle spoofing checkbox toggle."""
        self.return_path_group.setVisible(checked)
        if checked:
            self.append_output("IP Spoofing enabled - Return path configuration available")
        else:
            self.append_output("IP Spoofing disabled")
    
    def start_lab(self):
        """Start the lab environment."""
        try:
            self.append_output("Starting lab environment...")
            self.shell_manager.start_lab()
            self.lab_status_label.setText("Lab Status: Starting...")
            # Update status after a brief delay to check if lab started
            QTimer.singleShot(3000, self.check_lab_status)
        except Exception as e:
            self.append_output(f"Error starting lab: {e}")
    
    def stop_lab(self):
        """Stop the lab environment."""
        try:
            self.append_output("Stopping lab environment...")
            self.shell_manager.stop_lab()
            self.lab_status_label.setText("Lab Status: Stopping...")
            QTimer.singleShot(2000, self.check_lab_status)
        except Exception as e:
            self.append_output(f"Error stopping lab: {e}")
    
    def check_lab_status(self):
        """Check and update lab status."""
        try:
            status = self.shell_manager.get_lab_status()
            self.lab_status_label.setText(f"Lab Status: {status}")
        except Exception as e:
            self.lab_status_label.setText("Lab Status: Unknown")
            self.append_output(f"Error checking lab status: {e}")
    
    def on_attack_finished(self, success):
        """Handle attack finished signal."""
        if success:
            self.append_output("Attack completed successfully!")
            self.update_status("Attack completed")
        else:
            self.append_output("Attack finished with errors")
            self.update_status("Attack failed")
        
        self.reset_ui_after_attack()
    
    def on_attack_error(self, error_message):
        """Handle attack error signal."""
        self.append_output(f"Attack error: {error_message}")
        self.update_status("Attack error")
        self.reset_ui_after_attack()
        
    def start_attack(self):
        """Start the selected attack."""
        try:
            # Check if already running
            if self.attack_runner.is_attack_running():
                self.update_status("Attack already running!")
                return
                
            # Save current config
            self.save_config()
            
            # Setup network configuration if spoofing is enabled
            if self.enable_spoofing.isChecked():
                self.append_output("Setting up IP spoofing...")
                
                # Determine return path method
                return_path_method = "nat"
                if self.return_path_route.isChecked():
                    return_path_method = "route"
                elif self.return_path_bridge.isChecked():
                    return_path_method = "bridge"
                
                # Configure spoofing and return path
                if not self.shell_manager.setup_spoofing(return_path_method):
                    self.append_output("Warning: Failed to setup spoofing configuration")
                else:
                    self.append_output(f"Spoofing configured with {return_path_method} return path")
            
            # Get selected attack type
            attack_type = self.attack_combo.currentText()
            
            # Validate attack type
            available_attacks = self.attack_runner.get_available_attacks()
            if attack_type not in available_attacks:
                self.update_status(f"Attack type '{attack_type}' not available")
                return
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Clear output
            self.clear_output()
            
            # Start attack
            self.update_status(f"Starting {attack_type} attack...")
            success = self.attack_runner.start_attack(attack_type)
            if not success:
                self.reset_ui_after_attack()
                
        except Exception as e:
            self.update_status(f"Error starting attack: {str(e)}")
            self.reset_ui_after_attack()
            
    def stop_attack(self):
        """Stop the current attack."""
        try:
            self.attack_runner.stop_attack()
            self.reset_ui_after_attack()
        except Exception as e:
            self.update_status(f"Error stopping attack: {str(e)}")
            self.reset_ui_after_attack()
        
    def reset_ui_after_attack(self):
        """Reset UI state after attack stops."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
    def update_status_safe(self, message: str):
        """Thread-safe status update method."""
        try:
            self.status_label.setText(message)
            self.status_bar.showMessage(message)
        except Exception as e:
            print(f"Error updating status: {e}")
            
    def append_output_safe(self, text: str):
        """Thread-safe output append method."""
        try:
            self.output_text.append(text)
            # Auto-scroll to bottom
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"Error appending output: {e}")
        
    def update_status(self, message: str):
        """Update status message (legacy method for direct calls)."""
        self.update_status_safe(message)
        
    def append_output(self, text: str):
        """Append text to output area (legacy method for direct calls)."""
        self.append_output_safe(text)
        
    def clear_output(self):
        """Clear the output text area."""
        try:
            self.output_text.clear()
        except Exception as e:
            print(f"Error clearing output: {e}")
        
    def update_ui_status(self):
        """Update UI status periodically."""
        if not self.attack_runner.is_attack_running():
            if self.stop_button.isEnabled():
                self.reset_ui_after_attack()
                
    def apply_theme(self):
        """Apply theme based on configuration."""
        theme = self.config_manager.get("general", "theme", "light")
        
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 8px;
                    background-color: #404040;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QLineEdit, QSpinBox, QComboBox {
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                    background-color: #404040;
                }
                QFrame {
                    border: 1px solid #555555;
                }
            """)
        else:
            # Light theme (default)
            self.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 8px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QFrame {
                    border: 1px solid #cccccc;
                }
            """)
            
    def closeEvent(self, event):
        """Handle application close."""
        # Stop any running attack
        if self.attack_runner.is_attack_running():
            reply = QMessageBox.question(
                self, 
                'Close Application',
                'An attack is currently running. Do you want to stop it and exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.attack_runner.stop_attack()
                self.save_config()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_config()
            event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("StormShadow SIP-Only")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StormShadow")
    
    # Create and show main window
    window = SipOnlyGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
