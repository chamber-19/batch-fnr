"""
Settings management for AutoCAD Text Tools.

This module handles application and plugin settings using YAML configuration files.
Provides centralized settings storage with validation and defaults.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Manages application and plugin settings.
    
    Uses YAML files for configuration storage with support for:
    - Application-wide settings
    - Plugin-specific settings
    - User preferences
    - Default configurations
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        # Determine config directory
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration files
        self.app_config_file = self.config_dir / "app_settings.yaml"
        self.user_config_file = self.config_dir / "user_settings.yaml"
        self.plugin_config_dir = self.config_dir / "plugins"
        self.plugin_config_dir.mkdir(exist_ok=True)
        
        # Settings storage
        self._app_settings: Dict[str, Any] = {}
        self._user_settings: Dict[str, Any] = {}
        self._plugin_settings: Dict[str, Dict[str, Any]] = {}
        
        # Load settings
        self._load_default_settings()
        self._load_app_settings()
        self._load_user_settings()
        self._load_plugin_settings()
        
        logger.info(f"Settings manager initialized, config dir: {self.config_dir}")
    
    def _load_default_settings(self):
        """Load default application settings."""
        self._app_settings = {
            "application": {
                "name": "AutoCAD Text Tools",
                "version": "2.0.0",
                "author": "Root3Power LLC",
                "window": {
                    "width": 1400,
                    "height": 900,
                    "min_width": 1200,
                    "min_height": 800
                },
                "theme": "dark",
                "log_level": "INFO",
                "autocad": {
                    "connection_timeout": 30,
                    "retry_attempts": 3,
                    "check_interval": 5
                }
            },
            "plugins": {
                "auto_load": True,
                "load_order": ["find_replace", "text_unifier", "scaling_tool"]
            }
        }
    
    def _load_app_settings(self):
        """Load application settings from file."""
        if not yaml:
            logger.warning("PyYAML not available, using default settings only")
            return
        
        if self.app_config_file.exists():
            try:
                with open(self.app_config_file, 'r', encoding='utf-8') as f:
                    file_settings = yaml.safe_load(f) or {}
                
                # Merge with defaults
                self._deep_merge(self._app_settings, file_settings)
                logger.info("Loaded application settings")
                
            except Exception as e:
                logger.error(f"Failed to load app settings: {e}")
    
    def _load_user_settings(self):
        """Load user settings from file."""
        if not yaml or not self.user_config_file.exists():
            return
        
        try:
            with open(self.user_config_file, 'r', encoding='utf-8') as f:
                self._user_settings = yaml.safe_load(f) or {}
            
            logger.info("Loaded user settings")
            
        except Exception as e:
            logger.error(f"Failed to load user settings: {e}")
    
    def _load_plugin_settings(self):
        """Load all plugin settings."""
        if not yaml:
            return
        
        for config_file in self.plugin_config_dir.glob("*.yaml"):
            plugin_name = config_file.stem
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    plugin_config = yaml.safe_load(f) or {}
                
                self._plugin_settings[plugin_name] = plugin_config
                logger.debug(f"Loaded settings for plugin: {plugin_name}")
                
            except Exception as e:
                logger.error(f"Failed to load settings for plugin {plugin_name}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """
        Get application setting using dot notation.
        
        Args:
            key: Setting key (e.g., "application.window.width")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self._get_nested_value(self._app_settings, key, default)
    
    def set_app_setting(self, key: str, value: Any):
        """
        Set application setting using dot notation.
        
        Args:
            key: Setting key (e.g., "application.window.width")
            value: Value to set
        """
        self._set_nested_value(self._app_settings, key, value)
    
    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """
        Get user setting using dot notation.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self._get_nested_value(self._user_settings, key, default)
    
    def set_user_setting(self, key: str, value: Any):
        """
        Set user setting using dot notation.
        
        Args:
            key: Setting key
            value: Value to set
        """
        self._set_nested_value(self._user_settings, key, value)
    
    def get_plugin_setting(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """
        Get plugin setting.
        
        Args:
            plugin_name: Name of the plugin
            key: Setting key (can use dot notation)
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        if plugin_name not in self._plugin_settings:
            return default
        
        return self._get_nested_value(self._plugin_settings[plugin_name], key, default)
    
    def set_plugin_setting(self, plugin_name: str, key: str, value: Any):
        """
        Set plugin setting.
        
        Args:
            plugin_name: Name of the plugin
            key: Setting key (can use dot notation)
            value: Value to set
        """
        if plugin_name not in self._plugin_settings:
            self._plugin_settings[plugin_name] = {}
        
        self._set_nested_value(self._plugin_settings[plugin_name], key, value)
    
    def get_plugin_settings(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get all settings for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary of plugin settings
        """
        return self._plugin_settings.get(plugin_name, {}).copy()
    
    def set_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]):
        """
        Set all settings for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            settings: Dictionary of settings
        """
        self._plugin_settings[plugin_name] = settings.copy()
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """Set nested dictionary value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_settings(self):
        """Save all settings to files."""
        if not yaml:
            logger.warning("PyYAML not available, cannot save settings")
            return
        
        try:
            # Save application settings
            with open(self.app_config_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._app_settings, f, default_flow_style=False, 
                             allow_unicode=True, sort_keys=False)
            
            # Save user settings
            if self._user_settings:
                with open(self.user_config_file, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(self._user_settings, f, default_flow_style=False,
                                 allow_unicode=True, sort_keys=False)
            
            # Save plugin settings
            for plugin_name, settings in self._plugin_settings.items():
                if settings:
                    config_file = self.plugin_config_dir / f"{plugin_name}.yaml"
                    with open(config_file, 'w', encoding='utf-8') as f:
                        yaml.safe_dump(settings, f, default_flow_style=False,
                                     allow_unicode=True, sort_keys=False)
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._user_settings.clear()
        self._plugin_settings.clear()
        self._load_default_settings()
        logger.info("Settings reset to defaults")
    
    def export_settings(self, file_path: Union[str, Path]) -> bool:
        """
        Export all settings to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        if not yaml:
            logger.error("PyYAML not available for export")
            return False
        
        try:
            export_data = {
                "application": self._app_settings,
                "user": self._user_settings,
                "plugins": self._plugin_settings
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(export_data, f, default_flow_style=False,
                             allow_unicode=True, sort_keys=False)
            
            logger.info(f"Settings exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: Union[str, Path]) -> bool:
        """
        Import settings from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        if not yaml:
            logger.error("PyYAML not available for import")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = yaml.safe_load(f) or {}
            
            if "application" in import_data:
                self._deep_merge(self._app_settings, import_data["application"])
            
            if "user" in import_data:
                self._user_settings.update(import_data["user"])
            
            if "plugins" in import_data:
                self._plugin_settings.update(import_data["plugins"])
            
            logger.info(f"Settings imported from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
