"""
Find & Replace Plugin Implementation.

Provides a comprehensive interface for batch text replacement in AutoCAD drawings
with advanced features like title block management and reporting.
"""

import os
import re
import getpass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QCheckBox, QRadioButton, QButtonGroup, QComboBox, QListWidget, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QLabel, QFrame, QGridLayout,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont

from plugins.base_plugin import BasePlugin
from .find_replace_worker import FindReplaceWorker
from .replacement_rule import ReplacementRule
from .title_block_manager import TitleBlockManager


class FindReplacePlugin(BasePlugin):
    """
    Find & Replace plugin for batch text processing in AutoCAD drawings.
    
    Features:
    - Multiple find/replace rules with regex support
    - Directory or file selection modes
    - Title block management with revision tracking
    - Stamp/layer management for different issue types
    - Preview mode for safe testing
    - Excel reporting with detailed change logs
    - Progress tracking and cancellation
    """
    
    # Additional signals
    processing_started = Signal()
    processing_finished = Signal(bool, str)  # success, message
    file_processed = Signal(str, bool)  # file_path, success
    
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        
        # Plugin metadata
        self._plugin_name = "Find & Replace"
        self._plugin_version = "2.0.0"
        self._plugin_description = "Batch find and replace text in AutoCAD drawings"
        
        # UI components
        self.path_entry: Optional[QLineEdit] = None
        self.mode_group: Optional[QButtonGroup] = None
        self.replacement_rules: List[ReplacementRule] = []
        self.title_block_manager: Optional[TitleBlockManager] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.log_text: Optional[QTextEdit] = None
        
        # Processing
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[FindReplaceWorker] = None
        
        # Settings
        self.max_replacements = 10
        
    def setup_ui(self):
        """Setup the plugin user interface."""
        layout = QVBoxLayout(self)
        
        # Create scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Project selection
        content_layout.addWidget(self._create_project_selection_group())
        
        # Replacement rules
        content_layout.addWidget(self._create_replacement_rules_group())
        
        # Options
        content_layout.addWidget(self._create_options_group())
        
        # Title block management
        content_layout.addWidget(self._create_title_block_group())
        
        # Stamp management
        content_layout.addWidget(self._create_stamp_group())
        
        # Control buttons and progress
        content_layout.addWidget(self._create_control_group())
        
        # Add stretch to push everything to top
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Status and log at bottom (not scrolled)
        layout.addWidget(self._create_log_group())
    
    def _create_project_selection_group(self) -> QGroupBox:
        """Create project selection group."""
        group = QGroupBox("Project Selection")
        layout = QVBoxLayout(group)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        
        self.mode_group = QButtonGroup()
        
        self.dir_radio = QRadioButton("Entire Project Directory (Recursive)")
        self.dir_radio.setChecked(True)
        self.mode_group.addButton(self.dir_radio, 0)
        mode_layout.addWidget(self.dir_radio)
        
        self.files_radio = QRadioButton("Select Specific Files")
        self.mode_group.addButton(self.files_radio, 1)
        mode_layout.addWidget(self.files_radio)
        
        layout.addLayout(mode_layout)
        
        # Path selection
        path_layout = QHBoxLayout()
        
        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText("Select directory or files...")
        path_layout.addWidget(self.path_entry)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        # Connect mode change
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        
        return group
    
    def _create_replacement_rules_group(self) -> QGroupBox:
        """Create replacement rules group."""
        group = QGroupBox("Text Replacement Rules")
        layout = QVBoxLayout(group)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Find"))
        header_layout.addWidget(QLabel("Replace With"))
        header_layout.addWidget(QLabel("Options"))
        header_layout.addWidget(QLabel(""))  # For remove button
        layout.addLayout(header_layout)
        
        # Rules container
        self.rules_widget = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_widget)
        self.rules_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for rules
        rules_scroll = QScrollArea()
        rules_scroll.setWidget(self.rules_widget)
        rules_scroll.setWidgetResizable(True)
        rules_scroll.setMaximumHeight(200)
        layout.addWidget(rules_scroll)
        
        # Add rule button
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self._add_replacement_rule)
        layout.addWidget(add_btn)
        
        # Add initial rule
        self._add_replacement_rule()
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create options group."""
        group = QGroupBox("Options")
        layout = QHBoxLayout(group)
        
        self.preview_check = QCheckBox("Preview Mode (No Changes Saved)")
        layout.addWidget(self.preview_check)
        
        self.recursive_check = QCheckBox("Include Subdirectories")
        layout.addWidget(self.recursive_check)
        
        return group
    
    def _create_title_block_group(self) -> QGroupBox:
        """Create title block management group."""
        group = QGroupBox("Title Block Management")
        
        self.title_block_manager = TitleBlockManager()
        layout = QVBoxLayout(group)
        layout.addWidget(self.title_block_manager)
        
        return group
    
    def _create_stamp_group(self) -> QGroupBox:
        """Create stamp management group."""
        group = QGroupBox("Stamp Management")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("Issue Type:"))
        
        self.stamp_combo = QComboBox()
        self.stamp_combo.addItems([
            "(leave as-is)",
            "APPROVAL",
            "PRELIM", 
            "CONSTRUCTION",
            "BID",
            "AS-BUILT",
            "REFERENCE"
        ])
        layout.addWidget(self.stamp_combo)
        
        self.stamp_apply_check = QCheckBox("Apply stamp changes")
        self.stamp_apply_check.setChecked(True)
        layout.addWidget(self.stamp_apply_check)
        
        layout.addStretch()
        
        return group
    
    def _create_control_group(self) -> QGroupBox:
        """Create control buttons and progress group."""
        group = QGroupBox("Processing")
        layout = QVBoxLayout(group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._start_processing)
        button_layout.addWidget(self.run_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        return group
    
    def _create_log_group(self) -> QGroupBox:
        """Create log display group."""
        group = QGroupBox("Processing Log")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        return group
    
    def _browse_path(self):
        """Browse for directory or files."""
        if self.dir_radio.isChecked():
            # Directory mode
            path = QFileDialog.getExistingDirectory(
                self, 
                "Select Project Directory",
                self.path_entry.text()
            )
            if path:
                self.path_entry.setText(path)
        else:
            # Files mode
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select DWG Files",
                self.path_entry.text(),
                "AutoCAD Drawings (*.dwg)"
            )
            if paths:
                self.path_entry.setText(";".join(paths))
    
    def _on_mode_changed(self):
        """Handle mode change."""
        self.path_entry.clear()
        
        if self.dir_radio.isChecked():
            self.path_entry.setPlaceholderText("Select directory...")
            self.recursive_check.setEnabled(True)
        else:
            self.path_entry.setPlaceholderText("Select DWG files...")
            self.recursive_check.setEnabled(False)
    
    def _add_replacement_rule(self):
        """Add a new replacement rule."""
        if len(self.replacement_rules) >= self.max_replacements:
            QMessageBox.warning(
                self, 
                "Maximum Rules", 
                f"Maximum of {self.max_replacements} replacement rules allowed."
            )
            return
        
        rule = ReplacementRule()
        rule.remove_requested.connect(self._remove_replacement_rule)
        
        self.replacement_rules.append(rule)
        self.rules_layout.addWidget(rule)
    
    def _remove_replacement_rule(self, rule: ReplacementRule):
        """Remove a replacement rule."""
        if rule in self.replacement_rules:
            self.replacement_rules.remove(rule)
            self.rules_layout.removeWidget(rule)
            rule.deleteLater()
    
    def _start_processing(self):
        """Start the find and replace processing."""
        # Validate inputs
        if not self._validate_inputs():
            return
        
        # Disable UI
        self._set_processing_state(True)
        
        # Clear log
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # Get settings
        settings = self._get_processing_settings()
        
        # Create worker thread
        self.worker_thread = QThread()
        self.worker = FindReplaceWorker(settings)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.process)
        self.worker.finished.connect(self._on_processing_finished)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self._add_log_message)
        self.worker.file_processed.connect(self.file_processed.emit)
        
        # Start processing
        self.worker_thread.start()
        self.processing_started.emit()
        
        self._add_log_message("Processing started...")
    
    def _cancel_processing(self):
        """Cancel the current processing."""
        if self.worker:
            self.worker.cancel()
        
        self._add_log_message("Cancelling processing...")
    
    def _validate_inputs(self) -> bool:
        """Validate user inputs."""
        # Check path
        path = self.path_entry.text().strip()
        if not path:
            QMessageBox.warning(self, "Invalid Input", "Please select a directory or files.")
            return False
        
        # Check replacement rules
        valid_rules = [rule for rule in self.replacement_rules if rule.is_valid()]
        if not valid_rules and not self.title_block_manager.has_changes():
            QMessageBox.warning(
                self, 
                "No Rules", 
                "Please add at least one replacement rule or title block change."
            )
            return False
        
        # Validate regex patterns
        for rule in valid_rules:
            if rule.use_regex and not rule.is_valid_regex():
                QMessageBox.warning(
                    self,
                    "Invalid Regex",
                    f"Invalid regular expression: {rule.find_text}"
                )
                return False
        
        return True
    
    def _get_processing_settings(self) -> Dict[str, Any]:
        """Get current processing settings."""
        return {
            'path': self.path_entry.text().strip(),
            'mode': 'directory' if self.dir_radio.isChecked() else 'files',
            'recursive': self.recursive_check.isChecked(),
            'preview': self.preview_check.isChecked(),
            'replacement_rules': [rule.to_dict() for rule in self.replacement_rules if rule.is_valid()],
            'title_block_settings': self.title_block_manager.get_settings(),
            'stamp_settings': {
                'issue_type': self.stamp_combo.currentText(),
                'apply': self.stamp_apply_check.isChecked()
            },
            'autocad_bridge': self.get_autocad_bridge()
        }
    
    def _set_processing_state(self, processing: bool):
        """Set UI state for processing."""
        self.run_btn.setEnabled(not processing)
        self.cancel_btn.setEnabled(processing)
        
        # Disable input controls during processing
        self.path_entry.setEnabled(not processing)
        self.browse_btn.setEnabled(not processing)
        self.dir_radio.setEnabled(not processing)
        self.files_radio.setEnabled(not processing)
        
        for rule in self.replacement_rules:
            rule.setEnabled(not processing)
    
    def _on_processing_finished(self, success: bool, message: str):
        """Handle processing completion."""
        # Clean up worker
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None
        
        # Update UI
        self._set_processing_state(False)
        self.progress_bar.setValue(100 if success else 0)
        
        # Show completion message
        self._add_log_message(f"Processing {'completed' if success else 'failed'}: {message}")
        
        # Emit signal
        self.processing_finished.emit(success, message)
        
        # Show message box
        if success:
            QMessageBox.information(self, "Processing Complete", message)
        else:
            QMessageBox.warning(self, "Processing Failed", message)
    
    def _add_log_message(self, message: str):
        """Add message to log."""
        timestamp = QTimer().currentTime().toString("hh:mm:ss")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Also log to application
        self.log_message(message)
    
    def get_plugin_info(self) -> Dict[str, str]:
        """Get plugin information."""
        return {
            "name": self._plugin_name,
            "version": self._plugin_version,
            "description": self._plugin_description,
            "author": self._plugin_author
        }
    
    def save_settings(self) -> Dict[str, Any]:
        """Save plugin settings."""
        return {
            'mode': 'directory' if self.dir_radio.isChecked() else 'files',
            'path': self.path_entry.text(),
            'recursive': self.recursive_check.isChecked(),
            'preview': self.preview_check.isChecked(),
            'replacement_rules': [rule.to_dict() for rule in self.replacement_rules],
            'title_block_settings': self.title_block_manager.get_settings() if self.title_block_manager else {},
            'stamp_settings': {
                'issue_type': self.stamp_combo.currentText(),
                'apply': self.stamp_apply_check.isChecked()
            }
        }
    
    def load_settings(self, settings: Dict[str, Any]):
        """Load plugin settings."""
        # Load mode
        if settings.get('mode') == 'files':
            self.files_radio.setChecked(True)
        else:
            self.dir_radio.setChecked(True)
        
        # Load path
        self.path_entry.setText(settings.get('path', ''))
        
        # Load options
        self.recursive_check.setChecked(settings.get('recursive', False))
        self.preview_check.setChecked(settings.get('preview', False))
        
        # Load replacement rules
        rules_data = settings.get('replacement_rules', [])
        for rule_data in rules_data:
            if len(self.replacement_rules) < self.max_replacements:
                self._add_replacement_rule()
                self.replacement_rules[-1].from_dict(rule_data)
        
        # Load title block settings
        if self.title_block_manager:
            self.title_block_manager.load_settings(settings.get('title_block_settings', {}))
        
        # Load stamp settings
        stamp_settings = settings.get('stamp_settings', {})
        issue_type = stamp_settings.get('issue_type', '(leave as-is)')
        index = self.stamp_combo.findText(issue_type)
        if index >= 0:
            self.stamp_combo.setCurrentIndex(index)
        self.stamp_apply_check.setChecked(stamp_settings.get('apply', True))
    
    def cleanup(self):
        """Cleanup plugin resources."""
        if self.worker_thread and self.worker_thread.isRunning():
            if self.worker:
                self.worker.cancel()
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        super().cleanup()
