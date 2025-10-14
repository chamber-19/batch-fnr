"""
Core module for AutoCAD Text Tools.

This module contains the core functionality including:
- Application framework
- Plugin management system
- AutoCAD COM interface
- Settings management
- Threading utilities
"""

__version__ = "2.0.0"
__author__ = "Root3Power LLC"

from .application import AutoCADTextToolsApp
from .autocad_bridge import AutoCADBridge
from .plugin_manager import PluginManager
from .settings_manager import SettingsManager

__all__ = [
    'AutoCADTextToolsApp',
    'AutoCADBridge', 
    'PluginManager',
    'SettingsManager'
]
