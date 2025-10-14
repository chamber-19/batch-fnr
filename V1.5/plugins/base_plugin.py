"""
Base plugin class for AutoCAD Text Tools.

All plugins should inherit from BasePlugin to ensure consistent interface
and integration with the main application.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, QObject

logger = logging.getLogger(__name__)


class BasePlugin(QWidget, ABC):
    """
    Base class for all plugins.
    
    Provides common functionality and interface that all plugins should implement.
    Plugins inherit from QWidget to be displayed in the main application's tab widget.
    """
    
    # Signals
    status_changed = Signal(str)  # Emit status messages
    error_occurred = Signal(str)  # Emit error messages
    progress_updated = Signal(int)  # Emit progress updates (0-100)
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        
        self.app = app  # Reference to main application
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Plugin metadata
        self._plugin_name = self.__class__.__name__
        self._plugin_version = "1.0.0"
        self._plugin_description = "Base plugin"
        self._plugin_author = "Root3Power LLC"
        
        # Initialize UI
        self._setup_base_ui()
        self.setup_ui()
        
        # Connect signals
        self.status_changed.connect(self._on_status_changed)
        self.error_occurred.connect(self._on_error_occurred)
        
        self.logger.info(f"Plugin {self._plugin_name} initialized")
    
    def _setup_base_ui(self):
        """Setup base UI elements common to all plugins."""
        self.setLayout(QVBoxLayout())
        
        # Apply consistent styling
        self.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
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
                background-color: #1e90ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4169e1;
            }
            QPushButton:pressed {
                background-color: #0066cc;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #1e90ff;
            }
            QComboBox {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2c2c2c;
                border: 1px solid #555555;
            }
            QCheckBox::indicator:checked {
                background-color: #1e90ff;
                border: 1px solid #1e90ff;
            }
            QListWidget {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #1e90ff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e90ff;
            }
        """)
    
    @abstractmethod
    def setup_ui(self):
        """Setup plugin-specific UI. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, str]:
        """
        Get plugin information.
        
        Returns:
            Dictionary with plugin metadata (name, version, description, author)
        """
        return {
            "name": self._plugin_name,
            "version": self._plugin_version,
            "description": self._plugin_description,
            "author": self._plugin_author
        }
    
    def get_autocad_bridge(self):
        """Get AutoCAD bridge from main application."""
        return self.app.get_autocad_bridge()
    
    def get_settings_manager(self):
        """Get settings manager from main application."""
        return self.app.get_settings_manager()
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message to the application log."""
        self.app.log_message(message, level)
    
    def emit_status(self, message: str):
        """Emit a status message."""
        self.status_changed.emit(message)
    
    def emit_error(self, message: str):
        """Emit an error message."""
        self.error_occurred.emit(message)
    
    def emit_progress(self, value: int):
        """Emit progress update (0-100)."""
        self.progress_updated.emit(max(0, min(100, value)))
    
    def _on_status_changed(self, message: str):
        """Handle status change."""
        self.log_message(message, "INFO")
    
    def _on_error_occurred(self, message: str):
        """Handle error occurrence."""
        self.log_message(message, "ERROR")
    
    def save_settings(self) -> Dict[str, Any]:
        """
        Save plugin settings.
        
        Returns:
            Dictionary of settings to be saved
        """
        return {}
    
    def load_settings(self, settings: Dict[str, Any]):
        """
        Load plugin settings.
        
        Args:
            settings: Dictionary of settings to load
        """
        pass
    
    def cleanup(self):
        """Cleanup plugin resources. Called when plugin is unloaded."""
        self.logger.info(f"Plugin {self._plugin_name} cleaned up")
    
    def is_autocad_required(self) -> bool:
        """
        Check if this plugin requires AutoCAD connection.
        
        Returns:
            True if AutoCAD is required, False otherwise
        """
        return True
    
    def validate_requirements(self) -> bool:
        """
        Validate that all plugin requirements are met.
        
        Returns:
            True if requirements are met, False otherwise
        """
        if self.is_autocad_required():
            bridge = self.get_autocad_bridge()
            if not bridge or not bridge.is_connected():
                self.emit_error("AutoCAD connection required but not available")
                return False
        
        return True
    
    def get_help_text(self) -> str:
        """
        Get help text for this plugin.
        
        Returns:
            Help text describing plugin functionality
        """
        return f"Help for {self._plugin_name} plugin"
    
    def get_menu_actions(self) -> list:
        """
        Get menu actions for this plugin.
        
        Returns:
            List of QAction objects to add to application menus
        """
        return []
    
    def get_toolbar_actions(self) -> list:
        """
        Get toolbar actions for this plugin.
        
        Returns:
            List of QAction objects to add to application toolbar
        """
        return []
