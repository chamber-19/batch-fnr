"""
Main application class for AutoCAD Text Tools.

This module provides the main application window and coordinates all plugins.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QStatusBar, QTextEdit, QSplitter, QMessageBox,
    QToolBar, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap

from .plugin_manager import PluginManager
from .settings_manager import SettingsManager
from .autocad_bridge import AutoCADBridge

logger = logging.getLogger(__name__)


class AutoCADTextToolsApp(QMainWindow):
    """
    Main application window for AutoCAD Text Tools.
    
    Provides a tabbed interface for plugins and manages the overall application state.
    """
    
    # Signals
    autocad_connected = Signal(bool)
    plugin_loaded = Signal(str)
    plugin_error = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("AutoCAD Text Tools v2.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Core components
        self.settings_manager = SettingsManager()
        self.plugin_manager = PluginManager(self)
        self.autocad_bridge: Optional[AutoCADBridge] = None
        
        # UI components
        self.tab_widget: Optional[QTabWidget] = None
        self.log_widget: Optional[QTextEdit] = None
        self.status_label: Optional[QLabel] = None
        
        # Plugin tracking
        self.loaded_plugins: Dict[str, QWidget] = {}
        
        # Initialize UI
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Load plugins
        self._load_plugins()
        
        # Setup AutoCAD connection check
        self._setup_autocad_check()
        
        logger.info("AutoCAD Text Tools application initialized")
    
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for main content and log
        splitter = QSplitter(Qt.Vertical)
        
        # Tab widget for plugins
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        splitter.addWidget(self.tab_widget)
        
        # Log widget
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        log_header = QLabel("Application Log")
        log_header.setStyleSheet("font-weight: bold; padding: 5px;")
        log_layout.addWidget(log_header)
        
        self.log_widget = QTextEdit()
        self.log_widget.setMaximumHeight(200)
        self.log_widget.setReadOnly(True)
        self.log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """)
        log_layout.addWidget(self.log_widget)
        
        splitter.addWidget(log_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(splitter)
        
        # Apply dark theme
        self._apply_theme()
    
    def _setup_menus(self):
        """Setup application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # AutoCAD connection
        connect_action = QAction("Connect to &AutoCAD", self)
        connect_action.triggered.connect(self._connect_autocad)
        tools_menu.addAction(connect_action)
        
        # Refresh plugins
        refresh_action = QAction("&Refresh Plugins", self)
        refresh_action.triggered.connect(self._reload_plugins)
        tools_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # AutoCAD connection status
        self.autocad_status_btn = QPushButton("AutoCAD: Disconnected")
        self.autocad_status_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.autocad_status_btn.clicked.connect(self._connect_autocad)
        toolbar.addWidget(self.autocad_status_btn)
        
        toolbar.addSeparator()
        
        # Plugin reload button
        reload_btn = QPushButton("Reload Plugins")
        reload_btn.clicked.connect(self._reload_plugins)
        toolbar.addWidget(reload_btn)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        # Plugin count
        plugin_count_label = QLabel("Plugins: 0")
        status_bar.addPermanentWidget(plugin_count_label)
        self.plugin_count_label = plugin_count_label
    
    def _apply_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
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
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #1e90ff;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #1e90ff;
            }
            QToolBar {
                background-color: #404040;
                border: none;
                spacing: 5px;
            }
            QStatusBar {
                background-color: #404040;
                color: #ffffff;
            }
        """)
    
    def _load_plugins(self):
        """Load all available plugins."""
        try:
            plugins = self.plugin_manager.discover_plugins()
            
            for plugin_name, plugin_class in plugins.items():
                try:
                    # Create plugin instance
                    plugin_widget = plugin_class(self)
                    
                    # Add to tab widget
                    self.tab_widget.addTab(plugin_widget, plugin_name)
                    self.loaded_plugins[plugin_name] = plugin_widget
                    
                    self.plugin_loaded.emit(plugin_name)
                    logger.info(f"Loaded plugin: {plugin_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to load plugin {plugin_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    self.plugin_error.emit(plugin_name, str(e))
            
            # Update plugin count
            self.plugin_count_label.setText(f"Plugins: {len(self.loaded_plugins)}")
            
            if not self.loaded_plugins:
                self._show_no_plugins_message()
                
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Error", f"Failed to load plugins: {e}")
    
    def _show_no_plugins_message(self):
        """Show message when no plugins are available."""
        no_plugins_widget = QWidget()
        layout = QVBoxLayout(no_plugins_widget)
        
        message = QLabel("No plugins found. Please check the plugins directory.")
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("font-size: 14pt; color: #888888;")
        layout.addWidget(message)
        
        self.tab_widget.addTab(no_plugins_widget, "No Plugins")
    
    def _setup_autocad_check(self):
        """Setup periodic AutoCAD connection check."""
        self.autocad_timer = QTimer()
        self.autocad_timer.timeout.connect(self._check_autocad_connection)
        self.autocad_timer.start(5000)  # Check every 5 seconds
    
    def _check_autocad_connection(self):
        """Check AutoCAD connection status."""
        if self.autocad_bridge:
            is_connected = self.autocad_bridge.is_connected()
            self._update_autocad_status(is_connected)
    
    def _update_autocad_status(self, connected: bool):
        """Update AutoCAD connection status in UI."""
        if connected:
            self.autocad_status_btn.setText("AutoCAD: Connected")
            self.autocad_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #388e3c;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2e7d32;
                }
            """)
        else:
            self.autocad_status_btn.setText("AutoCAD: Disconnected")
            self.autocad_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
            """)
        
        self.autocad_connected.emit(connected)
    
    def _connect_autocad(self):
        """Connect to AutoCAD."""
        try:
            if not self.autocad_bridge:
                self.autocad_bridge = AutoCADBridge(self.log_message)
            
            self.autocad_bridge.connect()
            self._update_autocad_status(True)
            self.log_message("Connected to AutoCAD successfully")
            
        except Exception as e:
            self._update_autocad_status(False)
            error_msg = f"Failed to connect to AutoCAD: {e}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.warning(self, "AutoCAD Connection", error_msg)
    
    def _reload_plugins(self):
        """Reload all plugins."""
        # Clear existing plugins
        self.tab_widget.clear()
        self.loaded_plugins.clear()
        
        # Reload plugin manager
        self.plugin_manager = PluginManager(self)
        
        # Load plugins again
        self._load_plugins()
        
        self.log_message("Plugins reloaded")
    
    def _show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog not yet implemented")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About AutoCAD Text Tools", 
                         "AutoCAD Text Tools v2.0\n\n"
                         "A unified application for AutoCAD text processing.\n\n"
                         "© 2025 Root3Power LLC\n"
                         "All rights reserved.")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to application log."""
        timestamp = QTimer().currentTime().toString("hh:mm:ss")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        self.log_widget.append(formatted_message)
        
        # Also log to Python logger
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def get_autocad_bridge(self) -> Optional[AutoCADBridge]:
        """Get the AutoCAD bridge instance."""
        return self.autocad_bridge
    
    def get_settings_manager(self) -> SettingsManager:
        """Get the settings manager instance."""
        return self.settings_manager
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Cleanup AutoCAD connection
        if self.autocad_bridge:
            try:
                self.autocad_bridge.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from AutoCAD: {e}")
        
        # Save settings
        try:
            self.settings_manager.save_settings()
        except Exception as e:
            logger.warning(f"Error saving settings: {e}")
        
        logger.info("AutoCAD Text Tools application closed")
        event.accept()
