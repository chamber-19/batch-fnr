"""
Title Block Manager Widget for Find & Replace Plugin.

Provides comprehensive title block management functionality including
revision tracking, field updates, and revision shifting operations.
"""

from typing import Dict, Any, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QListWidget,
    QLabel, QGroupBox, QFrame
)
from PySide6.QtCore import Qt


class TitleBlockManager(QWidget):
    """
    Widget for managing title block operations.
    
    Provides:
    - Revision field management (REV, DESC, BY, CHK, DATE)
    - Revision shifting (up/down)
    - Field clearing operations
    - Standard title block fields (DWNBY, CHKBY, ENGR, etc.)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI components
        self.enable_check: QCheckBox = None
        self.rev_section_combo: QComboBox = None
        self.field_entries: Dict[str, QLineEdit] = {}
        self.shift_down_check: QCheckBox = None
        self.shift_up_check: QCheckBox = None
        self.clear_combo: QComboBox = None
        self.clear_list: QListWidget = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the title block manager UI."""
        layout = QVBoxLayout(self)
        
        # Enable checkbox
        self.enable_check = QCheckBox("Enable Title Block Management")
        layout.addWidget(self.enable_check)
        
        # Main content (disabled when not enabled)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        
        # Revision section
        content_layout.addWidget(self._create_revision_section())
        
        # Standard fields section
        content_layout.addWidget(self._create_standard_fields_section())
        
        # Revision operations
        content_layout.addWidget(self._create_revision_operations_section())
        
        # Clear operations
        content_layout.addWidget(self._create_clear_operations_section())
        
        layout.addWidget(self.content_widget)
        
        # Initially disable content
        self.content_widget.setEnabled(False)
    
    def _create_revision_section(self) -> QGroupBox:
        """Create revision section UI."""
        group = QGroupBox("Revision Entry")
        layout = QGridLayout(group)
        
        # Revision section selector
        layout.addWidget(QLabel("Rev Section:"), 0, 0)
        self.rev_section_combo = QComboBox()
        self.rev_section_combo.addItems(["Rev1", "Rev2", "Rev3", "Rev4", "Rev5"])
        layout.addWidget(self.rev_section_combo, 0, 1)
        
        # Revision fields
        fields = [
            ("REV", "Revision"),
            ("DESC", "Description"),
            ("BY", "By"),
            ("CHK", "Checked By"),
            ("DATE", "Date")
        ]
        
        for i, (field, label) in enumerate(fields):
            layout.addWidget(QLabel(f"{label}:"), 1, i)
            entry = QLineEdit()
            if field == "DATE":
                entry.setPlaceholderText("MM/DD/YY")
            elif field == "DESC":
                entry.setMinimumWidth(200)
            self.field_entries[field] = entry
            layout.addWidget(entry, 2, i)
        
        return group
    
    def _create_standard_fields_section(self) -> QGroupBox:
        """Create standard title block fields section."""
        group = QGroupBox("Standard Fields")
        layout = QGridLayout(group)
        
        # Standard fields
        standard_fields = [
            ("DWNBY", "Drawn By", 0, 0),
            ("DWNDATE", "Drawn Date", 0, 2),
            ("CHKBY", "Checked By", 1, 0),
            ("CHKDATE", "Checked Date", 1, 2),
            ("ENGR", "Engineer", 2, 0),
            ("ENGRDATE", "Engineer Date", 2, 2),
            ("REV", "Overall Revision", 3, 0)
        ]
        
        for field, label, row, col in standard_fields:
            layout.addWidget(QLabel(f"{label}:"), row, col)
            entry = QLineEdit()
            if "DATE" in field:
                entry.setPlaceholderText("MM/DD/YY")
            self.field_entries[field] = entry
            layout.addWidget(entry, row, col + 1)
        
        return group
    
    def _create_revision_operations_section(self) -> QGroupBox:
        """Create revision operations section."""
        group = QGroupBox("Revision Operations")
        layout = QVBoxLayout(group)
        
        # Shift operations
        shift_layout = QHBoxLayout()
        
        self.shift_down_check = QCheckBox("Shift Revisions Down (1→2→3→4→5)")
        self.shift_down_check.setToolTip("Move all revisions down one position")
        shift_layout.addWidget(self.shift_down_check)
        
        self.shift_up_check = QCheckBox("Shift Revisions Up (5→4→3→2→1)")
        self.shift_up_check.setToolTip("Move all revisions up one position")
        shift_layout.addWidget(self.shift_up_check)
        
        layout.addLayout(shift_layout)
        
        # Auto-fill today's date button
        date_layout = QHBoxLayout()
        today_btn = QPushButton("Fill Today's Date")
        today_btn.clicked.connect(self._fill_todays_date)
        date_layout.addWidget(today_btn)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        return group
    
    def _create_clear_operations_section(self) -> QGroupBox:
        """Create clear operations section."""
        group = QGroupBox("Clear Operations")
        layout = QVBoxLayout(group)
        
        # Clear controls
        clear_controls = QHBoxLayout()
        
        clear_controls.addWidget(QLabel("Clear Rev Line:"))
        
        self.clear_combo = QComboBox()
        self.clear_combo.addItems(["Rev", "Rev2", "Rev3", "Rev4", "Rev5"])
        clear_controls.addWidget(self.clear_combo)
        
        add_clear_btn = QPushButton("Add Clear")
        add_clear_btn.clicked.connect(self._add_clear_operation)
        clear_controls.addWidget(add_clear_btn)
        
        remove_clear_btn = QPushButton("Remove Selected")
        remove_clear_btn.clicked.connect(self._remove_clear_operation)
        clear_controls.addWidget(remove_clear_btn)
        
        clear_controls.addStretch()
        layout.addLayout(clear_controls)
        
        # Clear list
        self.clear_list = QListWidget()
        self.clear_list.setMaximumHeight(80)
        layout.addWidget(self.clear_list)
        
        return group
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.enable_check.toggled.connect(self.content_widget.setEnabled)
        
        # Mutual exclusion for shift operations
        self.shift_down_check.toggled.connect(self._on_shift_down_toggled)
        self.shift_up_check.toggled.connect(self._on_shift_up_toggled)
    
    def _on_shift_down_toggled(self, checked: bool):
        """Handle shift down toggle."""
        if checked:
            self.shift_up_check.setChecked(False)
    
    def _on_shift_up_toggled(self, checked: bool):
        """Handle shift up toggle."""
        if checked:
            self.shift_down_check.setChecked(False)
    
    def _fill_todays_date(self):
        """Fill today's date in MM/DD/YY format."""
        today = datetime.now().strftime("%m/%d/%y")
        
        # Fill in DATE field if it exists and is empty
        if "DATE" in self.field_entries:
            date_entry = self.field_entries["DATE"]
            if not date_entry.text().strip():
                date_entry.setText(today)
        
        # Also fill other date fields if they're empty
        date_fields = ["DWNDATE", "CHKDATE", "ENGRDATE"]
        for field in date_fields:
            if field in self.field_entries:
                entry = self.field_entries[field]
                if not entry.text().strip():
                    entry.setText(today)
    
    def _add_clear_operation(self):
        """Add a clear operation to the list."""
        rev_line = self.clear_combo.currentText()
        
        # Check if already in list
        for i in range(self.clear_list.count()):
            if self.clear_list.item(i).text() == rev_line:
                return  # Already exists
        
        self.clear_list.addItem(rev_line)
    
    def _remove_clear_operation(self):
        """Remove selected clear operation."""
        current_row = self.clear_list.currentRow()
        if current_row >= 0:
            self.clear_list.takeItem(current_row)
    
    def has_changes(self) -> bool:
        """Check if any title block changes are configured."""
        if not self.enable_check.isChecked():
            return False
        
        # Check if any fields have values
        for entry in self.field_entries.values():
            if entry.text().strip():
                return True
        
        # Check if any operations are enabled
        if (self.shift_down_check.isChecked() or 
            self.shift_up_check.isChecked() or 
            self.clear_list.count() > 0):
            return True
        
        return False
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current title block settings."""
        if not self.enable_check.isChecked():
            return {}
        
        # Get field values
        fields = {}
        for field, entry in self.field_entries.items():
            value = entry.text().strip()
            if value:
                fields[field] = value
        
        # Get clear operations
        clear_operations = []
        for i in range(self.clear_list.count()):
            clear_operations.append(self.clear_list.item(i).text())
        
        return {
            'enabled': True,
            'rev_section': self.rev_section_combo.currentText(),
            'fields': fields,
            'shift_down': self.shift_down_check.isChecked(),
            'shift_up': self.shift_up_check.isChecked(),
            'clear_operations': clear_operations
        }
    
    def load_settings(self, settings: Dict[str, Any]):
        """Load title block settings."""
        if not settings:
            return
        
        # Enable state
        self.enable_check.setChecked(settings.get('enabled', False))
        
        # Revision section
        rev_section = settings.get('rev_section', 'Rev1')
        index = self.rev_section_combo.findText(rev_section)
        if index >= 0:
            self.rev_section_combo.setCurrentIndex(index)
        
        # Field values
        fields = settings.get('fields', {})
        for field, value in fields.items():
            if field in self.field_entries:
                self.field_entries[field].setText(value)
        
        # Operations
        self.shift_down_check.setChecked(settings.get('shift_down', False))
        self.shift_up_check.setChecked(settings.get('shift_up', False))
        
        # Clear operations
        self.clear_list.clear()
        for operation in settings.get('clear_operations', []):
            self.clear_list.addItem(operation)
    
    def clear_all(self):
        """Clear all settings."""
        self.enable_check.setChecked(False)
        
        for entry in self.field_entries.values():
            entry.clear()
        
        self.shift_down_check.setChecked(False)
        self.shift_up_check.setChecked(False)
        self.clear_list.clear()
        
        self.rev_section_combo.setCurrentIndex(0)
