"""
Text Unifier Plugin Implementation.

Provides advanced text unification and scaling functionality for AutoCAD drawings
with intelligent clustering, column detection, and multiple unification strategies.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QCheckBox, QRadioButton, QButtonGroup, QComboBox, QListWidget, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QLabel, QFrame, QGridLayout,
    QScrollArea, QWidget, QSpinBox, QDoubleSpinBox, QSlider, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont

from plugins.base_plugin import BasePlugin
from core.geometry import BBox
from .text_item import TextItem
from .text_group import TextGroup
from .text_unifier_core import TextUnifierCore
from .scaling_tool import ScalingTool


class TextUnifierPlugin(BasePlugin):
    """
    Text Unifier plugin for advanced text processing in AutoCAD drawings.
    
    Features:
    - Intelligent text clustering and grouping
    - Column detection and alignment
    - Multiple unification strategies (Nudge, Mask, Move)
    - Text wrapping and scaling
    - Preview system with visual feedback
    - Scaling tool for text height adjustments
    """
    
    # Additional signals
    groups_updated = Signal()
    preview_updated = Signal()
    
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        
        # Plugin metadata
        self._plugin_name = "Text Unifier"
        self._plugin_version = "2.0.0"
        self._plugin_description = "Advanced text unification and scaling for AutoCAD"
        
        # Core components
        self.text_unifier_core: Optional[TextUnifierCore] = None
        self.scaling_tool: Optional[ScalingTool] = None
        
        # UI components
        self.groups_list: Optional[QListWidget] = None
        self.settings_widget: Optional[QWidget] = None
        self.preview_active = False
        
        # Text groups
        self.text_groups: List[TextGroup] = []
        
    def setup_ui(self):
        """Setup the plugin user interface."""
        layout = QVBoxLayout(self)
        
        # Create main content
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Left panel - Groups and controls
        left_panel = self._create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Right panel - Settings and scaling
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, 1)
        
        layout.addWidget(content_widget)
        
        # Initialize core components
        self._initialize_components()
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with groups and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Groups section
        layout.addWidget(self._create_groups_section())
        
        # Control buttons
        layout.addWidget(self._create_control_buttons())
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with settings and scaling."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Settings section
        layout.addWidget(self._create_settings_section())
        
        # Scaling tool section
        layout.addWidget(self._create_scaling_section())
        
        layout.addStretch()
        
        return panel
    
    def _create_groups_section(self) -> QGroupBox:
        """Create text groups section."""
        group = QGroupBox("Text Groups")
        layout = QVBoxLayout(group)
        
        # Groups list
        self.groups_list = QListWidget()
        self.groups_list.setMinimumHeight(300)
        self.groups_list.itemChanged.connect(self._on_group_item_changed)
        self.groups_list.itemDoubleClicked.connect(self._edit_group_text)
        layout.addWidget(self.groups_list)
        
        # Group controls
        controls_layout = QHBoxLayout()
        
        edit_btn = QPushButton("Edit Text")
        edit_btn.clicked.connect(self._edit_group_text)
        controls_layout.addWidget(edit_btn)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_groups)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self._select_no_groups)
        controls_layout.addWidget(select_none_btn)
        
        layout.addLayout(controls_layout)
        
        return group
    
    def _create_control_buttons(self) -> QGroupBox:
        """Create main control buttons."""
        group = QGroupBox("Operations")
        layout = QVBoxLayout(group)
        
        # Main operation buttons
        button_layout = QGridLayout()
        
        collect_btn = QPushButton("Collect Text")
        collect_btn.clicked.connect(self._collect_text)
        button_layout.addWidget(collect_btn, 0, 0)
        
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._toggle_preview)
        button_layout.addWidget(preview_btn, 0, 1)
        
        resolve_btn = QPushButton("Resolve")
        resolve_btn.clicked.connect(self._resolve_groups)
        button_layout.addWidget(resolve_btn, 1, 0)
        
        convert_btn = QPushButton("Convert")
        convert_btn.clicked.connect(self._convert_groups)
        button_layout.addWidget(convert_btn, 1, 1)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        return group
    
    def _create_settings_section(self) -> QGroupBox:
        """Create settings section."""
        group = QGroupBox("Unification Settings")
        layout = QFormLayout(group)
        
        # Text style
        self.style_combo = QComboBox()
        self.style_combo.setEditable(True)
        self.style_combo.addItems(["Standard", "ROMANS", "Arial"])
        layout.addRow("Text Style:", self.style_combo)
        
        # Plot height
        self.plot_height_spin = QDoubleSpinBox()
        self.plot_height_spin.setRange(0.01, 10.0)
        self.plot_height_spin.setValue(0.125)
        self.plot_height_spin.setSingleStep(0.01)
        self.plot_height_spin.setDecimals(3)
        layout.addRow("Plot Height:", self.plot_height_spin)
        
        # Angle tolerance
        self.angle_tolerance_spin = QDoubleSpinBox()
        self.angle_tolerance_spin.setRange(0.0, 45.0)
        self.angle_tolerance_spin.setValue(5.0)
        self.angle_tolerance_spin.setSuffix("°")
        layout.addRow("Angle Tolerance:", self.angle_tolerance_spin)
        
        # Distance tolerance
        self.distance_tolerance_spin = QDoubleSpinBox()
        self.distance_tolerance_spin.setRange(0.01, 10.0)
        self.distance_tolerance_spin.setValue(0.5)
        self.distance_tolerance_spin.setSingleStep(0.1)
        layout.addRow("Distance Tolerance:", self.distance_tolerance_spin)
        
        # Strategy selection
        strategy_group = QGroupBox("Unification Strategy")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self.strategy_group = QButtonGroup()
        
        self.nudge_radio = QRadioButton("Nudge (Align existing text)")
        self.nudge_radio.setChecked(True)
        self.strategy_group.addButton(self.nudge_radio, 0)
        strategy_layout.addWidget(self.nudge_radio)
        
        self.mask_radio = QRadioButton("Mask (Hide duplicates)")
        self.strategy_group.addButton(self.mask_radio, 1)
        strategy_layout.addWidget(self.mask_radio)
        
        self.move_radio = QRadioButton("Move (Create new MText)")
        self.strategy_group.addButton(self.move_radio, 2)
        strategy_layout.addWidget(self.move_radio)
        
        layout.addRow(strategy_group)
        
        # Additional options
        self.wrap_text_check = QCheckBox("Enable text wrapping")
        layout.addRow(self.wrap_text_check)
        
        self.preserve_formatting_check = QCheckBox("Preserve text formatting")
        self.preserve_formatting_check.setChecked(True)
        layout.addRow(self.preserve_formatting_check)
        
        return group
    
    def _create_scaling_section(self) -> QGroupBox:
        """Create scaling tool section."""
        group = QGroupBox("Scaling Tool")
        layout = QVBoxLayout(group)
        
        # Scale factor
        scale_layout = QFormLayout()
        
        self.scale_factor_spin = QDoubleSpinBox()
        self.scale_factor_spin.setRange(0.1, 10.0)
        self.scale_factor_spin.setValue(1.0)
        self.scale_factor_spin.setSingleStep(0.1)
        self.scale_factor_spin.setDecimals(2)
        scale_layout.addRow("Scale Factor:", self.scale_factor_spin)
        
        layout.addLayout(scale_layout)
        
        # Scale buttons
        scale_buttons = QHBoxLayout()
        
        scale_up_btn = QPushButton("Scale Up (×1.25)")
        scale_up_btn.clicked.connect(lambda: self._quick_scale(1.25))
        scale_buttons.addWidget(scale_up_btn)
        
        scale_down_btn = QPushButton("Scale Down (×0.8)")
        scale_down_btn.clicked.connect(lambda: self._quick_scale(0.8))
        scale_buttons.addWidget(scale_down_btn)
        
        layout.addLayout(scale_buttons)
        
        # Apply scaling
        apply_scale_btn = QPushButton("Apply Scaling")
        apply_scale_btn.clicked.connect(self._apply_scaling)
        layout.addWidget(apply_scale_btn)
        
        return group
    
    def _initialize_components(self):
        """Initialize core components."""
        self.text_unifier_core = TextUnifierCore(self.get_autocad_bridge())
        self.scaling_tool = ScalingTool(self.get_autocad_bridge())
    
    def _collect_text(self):
        """Collect text from AutoCAD and create groups."""
        try:
            self.status_label.setText("Collecting text...")
            
            # Get settings
            settings = self._get_unification_settings()
            
            # Collect and group text
            self.text_groups = self.text_unifier_core.collect_and_group_text(settings)
            
            # Update UI
            self._update_groups_list()
            
            self.status_label.setText(f"Found {len(self.text_groups)} text groups")
            self.groups_updated.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to collect text: {e}")
            self.status_label.setText("Error collecting text")
    
    def _update_groups_list(self):
        """Update the groups list widget."""
        self.groups_list.clear()
        
        for i, group in enumerate(self.text_groups):
            item = QListWidgetItem()
            item.setText(f"Group {i+1}: {group.get_display_text()}")
            item.setCheckState(Qt.Checked if group.selected else Qt.Unchecked)
            item.setData(Qt.UserRole, i)  # Store group index
            
            self.groups_list.addItem(item)
    
    def _on_group_item_changed(self, item: QListWidgetItem):
        """Handle group item check state change."""
        group_index = item.data(Qt.UserRole)
        if 0 <= group_index < len(self.text_groups):
            self.text_groups[group_index].selected = (item.checkState() == Qt.Checked)
    
    def _edit_group_text(self):
        """Edit the text of the selected group."""
        current_item = self.groups_list.currentItem()
        if not current_item:
            return
        
        group_index = current_item.data(Qt.UserRole)
        if not (0 <= group_index < len(self.text_groups)):
            return
        
        group = self.text_groups[group_index]
        
        # Show edit dialog (simplified - in full implementation would be a proper dialog)
        from PySide6.QtWidgets import QInputDialog
        
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Group Text",
            f"Edit text for Group {group_index + 1}:",
            group.unified_text
        )
        
        if ok:
            group.unified_text = new_text
            self._update_groups_list()
    
    def _select_all_groups(self):
        """Select all groups."""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            item.setCheckState(Qt.Checked)
            
            group_index = item.data(Qt.UserRole)
            if 0 <= group_index < len(self.text_groups):
                self.text_groups[group_index].selected = True
    
    def _select_no_groups(self):
        """Deselect all groups."""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            item.setCheckState(Qt.Unchecked)
            
            group_index = item.data(Qt.UserRole)
            if 0 <= group_index < len(self.text_groups):
                self.text_groups[group_index].selected = False
    
    def _toggle_preview(self):
        """Toggle preview mode."""
        if self.preview_active:
            self._clear_preview()
        else:
            self._show_preview()
    
    def _show_preview(self):
        """Show preview of unification."""
        try:
            selected_groups = [g for g in self.text_groups if g.selected]
            if not selected_groups:
                QMessageBox.warning(self, "No Selection", "Please select groups to preview.")
                return
            
            settings = self._get_unification_settings()
            
            # Create preview
            self.text_unifier_core.create_preview(selected_groups, settings)
            
            self.preview_active = True
            self.status_label.setText(f"Preview active for {len(selected_groups)} groups")
            self.preview_updated.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to create preview: {e}")
    
    def _clear_preview(self):
        """Clear preview objects."""
        try:
            self.text_unifier_core.clear_preview()
            self.preview_active = False
            self.status_label.setText("Preview cleared")
            self.preview_updated.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to clear preview: {e}")
    
    def _resolve_groups(self):
        """Resolve selected groups (apply unification)."""
        try:
            selected_groups = [g for g in self.text_groups if g.selected]
            if not selected_groups:
                QMessageBox.warning(self, "No Selection", "Please select groups to resolve.")
                return
            
            # Confirm action
            reply = QMessageBox.question(
                self,
                "Confirm Resolution",
                f"This will apply unification to {len(selected_groups)} groups. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            settings = self._get_unification_settings()
            
            # Apply unification
            result = self.text_unifier_core.resolve_groups(selected_groups, settings)
            
            self.status_label.setText(f"Resolved {result['resolved']} groups")
            
            # Clear preview if active
            if self.preview_active:
                self._clear_preview()
            
            # Refresh groups
            self._collect_text()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to resolve groups: {e}")
    
    def _convert_groups(self):
        """Convert selected groups to final format."""
        try:
            selected_groups = [g for g in self.text_groups if g.selected]
            if not selected_groups:
                QMessageBox.warning(self, "No Selection", "Please select groups to convert.")
                return
            
            settings = self._get_unification_settings()
            
            # Convert groups
            result = self.text_unifier_core.convert_groups(selected_groups, settings)
            
            self.status_label.setText(f"Converted {result['converted']} groups")
            
            # Clear preview if active
            if self.preview_active:
                self._clear_preview()
            
            # Refresh groups
            self._collect_text()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to convert groups: {e}")
    
    def _quick_scale(self, factor: float):
        """Apply quick scaling factor."""
        self.scale_factor_spin.setValue(factor)
    
    def _apply_scaling(self):
        """Apply scaling to selected text."""
        try:
            scale_factor = self.scale_factor_spin.value()
            
            # Apply scaling using scaling tool
            result = self.scaling_tool.scale_selected_text(scale_factor)
            
            self.status_label.setText(f"Scaled {result['count']} text entities")
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to apply scaling: {e}")
    
    def _get_unification_settings(self) -> Dict[str, Any]:
        """Get current unification settings."""
        strategy_map = {0: "nudge", 1: "mask", 2: "move"}
        strategy = strategy_map.get(self.strategy_group.checkedId(), "nudge")
        
        return {
            'text_style': self.style_combo.currentText(),
            'plot_height': self.plot_height_spin.value(),
            'angle_tolerance': self.angle_tolerance_spin.value(),
            'distance_tolerance': self.distance_tolerance_spin.value(),
            'strategy': strategy,
            'wrap_text': self.wrap_text_check.isChecked(),
            'preserve_formatting': self.preserve_formatting_check.isChecked()
        }
    
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
            'text_style': self.style_combo.currentText(),
            'plot_height': self.plot_height_spin.value(),
            'angle_tolerance': self.angle_tolerance_spin.value(),
            'distance_tolerance': self.distance_tolerance_spin.value(),
            'strategy': self.strategy_group.checkedId(),
            'wrap_text': self.wrap_text_check.isChecked(),
            'preserve_formatting': self.preserve_formatting_check.isChecked(),
            'scale_factor': self.scale_factor_spin.value()
        }
    
    def load_settings(self, settings: Dict[str, Any]):
        """Load plugin settings."""
        # Text style
        style = settings.get('text_style', 'Standard')
        index = self.style_combo.findText(style)
        if index >= 0:
            self.style_combo.setCurrentIndex(index)
        else:
            self.style_combo.setCurrentText(style)
        
        # Numeric settings
        self.plot_height_spin.setValue(settings.get('plot_height', 0.125))
        self.angle_tolerance_spin.setValue(settings.get('angle_tolerance', 5.0))
        self.distance_tolerance_spin.setValue(settings.get('distance_tolerance', 0.5))
        self.scale_factor_spin.setValue(settings.get('scale_factor', 1.0))
        
        # Strategy
        strategy_id = settings.get('strategy', 0)
        if 0 <= strategy_id <= 2:
            self.strategy_group.button(strategy_id).setChecked(True)
        
        # Checkboxes
        self.wrap_text_check.setChecked(settings.get('wrap_text', False))
        self.preserve_formatting_check.setChecked(settings.get('preserve_formatting', True))
    
    def cleanup(self):
        """Cleanup plugin resources."""
        if self.preview_active:
            self._clear_preview()
        
        super().cleanup()
