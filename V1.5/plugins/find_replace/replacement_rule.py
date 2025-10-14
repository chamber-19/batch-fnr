"""
Replacement Rule Widget for Find & Replace Plugin.

Provides a UI widget for configuring individual find/replace rules with
support for regular expressions and case sensitivity options.
"""

import re
from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QCheckBox, QPushButton, QLabel
)
from PySide6.QtCore import Signal


class ReplacementRule(QWidget):
    """
    Widget for configuring a single find/replace rule.
    
    Provides:
    - Find text input
    - Replace text input
    - Case sensitivity option
    - Regular expression option
    - Remove button
    """
    
    remove_requested = Signal(object)  # Emits self when remove is requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.find_entry: QLineEdit = None
        self.replace_entry: QLineEdit = None
        self.case_check: QCheckBox = None
        self.regex_check: QCheckBox = None
        self.remove_btn: QPushButton = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI for the replacement rule."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Find text
        self.find_entry = QLineEdit()
        self.find_entry.setPlaceholderText("Text to find...")
        self.find_entry.setMinimumWidth(200)
        layout.addWidget(self.find_entry)
        
        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-weight: bold; color: #1e90ff;")
        layout.addWidget(arrow_label)
        
        # Replace text
        self.replace_entry = QLineEdit()
        self.replace_entry.setPlaceholderText("Replace with...")
        self.replace_entry.setMinimumWidth(200)
        layout.addWidget(self.replace_entry)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.case_check = QCheckBox("Ignore Case")
        self.case_check.setToolTip("Ignore case when matching text")
        options_layout.addWidget(self.case_check)
        
        self.regex_check = QCheckBox("Use Regex")
        self.regex_check.setToolTip("Use regular expressions for advanced pattern matching")
        options_layout.addWidget(self.regex_check)
        
        layout.addLayout(options_layout)
        
        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setMaximumWidth(80)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(self.remove_btn)
        
        # Connect validation
        self.find_entry.textChanged.connect(self._validate_regex)
        self.regex_check.toggled.connect(self._validate_regex)
    
    def _on_remove_clicked(self):
        """Handle remove button click."""
        self.remove_requested.emit(self)
    
    def _validate_regex(self):
        """Validate regex pattern and update UI."""
        if self.regex_check.isChecked():
            pattern = self.find_entry.text()
            if pattern:
                try:
                    re.compile(pattern)
                    # Valid regex
                    self.find_entry.setStyleSheet("")
                    self.find_entry.setToolTip("")
                except re.error as e:
                    # Invalid regex
                    self.find_entry.setStyleSheet("border: 2px solid red;")
                    self.find_entry.setToolTip(f"Invalid regex: {e}")
            else:
                self.find_entry.setStyleSheet("")
                self.find_entry.setToolTip("")
        else:
            self.find_entry.setStyleSheet("")
            self.find_entry.setToolTip("")
    
    @property
    def find_text(self) -> str:
        """Get the find text."""
        return self.find_entry.text().strip()
    
    @find_text.setter
    def find_text(self, value: str):
        """Set the find text."""
        self.find_entry.setText(value)
    
    @property
    def replace_text(self) -> str:
        """Get the replace text."""
        return self.replace_entry.text()
    
    @replace_text.setter
    def replace_text(self, value: str):
        """Set the replace text."""
        self.replace_entry.setText(value)
    
    @property
    def ignore_case(self) -> bool:
        """Get the ignore case setting."""
        return self.case_check.isChecked()
    
    @ignore_case.setter
    def ignore_case(self, value: bool):
        """Set the ignore case setting."""
        self.case_check.setChecked(value)
    
    @property
    def use_regex(self) -> bool:
        """Get the use regex setting."""
        return self.regex_check.isChecked()
    
    @use_regex.setter
    def use_regex(self, value: bool):
        """Set the use regex setting."""
        self.regex_check.setChecked(value)
    
    def is_valid(self) -> bool:
        """Check if the rule is valid."""
        return bool(self.find_text)
    
    def is_valid_regex(self) -> bool:
        """Check if the regex pattern is valid."""
        if not self.use_regex:
            return True
        
        try:
            re.compile(self.find_text)
            return True
        except re.error:
            return False
    
    def apply_replacement(self, text: str) -> str:
        """
        Apply this replacement rule to text.
        
        Args:
            text: Input text
            
        Returns:
            Text with replacements applied
        """
        if not self.is_valid() or not text:
            return text
        
        find_text = self.find_text
        replace_text = self.replace_text
        
        if self.use_regex:
            # Use regular expressions
            flags = re.IGNORECASE if self.ignore_case else 0
            try:
                return re.sub(find_text, replace_text, text, flags=flags)
            except re.error:
                # Invalid regex, return original text
                return text
        else:
            # Simple text replacement
            if self.ignore_case:
                # Case-insensitive replacement
                # Find all occurrences with case-insensitive search
                pattern = re.escape(find_text)
                return re.sub(pattern, replace_text, text, flags=re.IGNORECASE)
            else:
                # Case-sensitive replacement
                return text.replace(find_text, replace_text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization."""
        return {
            'find_text': self.find_text,
            'replace_text': self.replace_text,
            'ignore_case': self.ignore_case,
            'use_regex': self.use_regex
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load rule from dictionary."""
        self.find_text = data.get('find_text', '')
        self.replace_text = data.get('replace_text', '')
        self.ignore_case = data.get('ignore_case', False)
        self.use_regex = data.get('use_regex', False)
    
    def __str__(self) -> str:
        """String representation of the rule."""
        options = []
        if self.ignore_case:
            options.append("ignore case")
        if self.use_regex:
            options.append("regex")
        
        options_str = f" ({', '.join(options)})" if options else ""
        return f"'{self.find_text}' → '{self.replace_text}'{options_str}"
