"""
Plugin management system for AutoCAD Text Tools.

This module handles plugin discovery, loading, and lifecycle management.
Plugins are discovered automatically from the plugins directory.
"""

import logging
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Type, List, Any, Optional

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin discovery and loading.
    
    Automatically discovers plugins in the plugins directory and provides
    methods to load and manage plugin instances.
    """
    
    def __init__(self, app):
        self.app = app
        self.plugins_dir = Path(__file__).parent.parent / "plugins"
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_classes: Dict[str, Type] = {}
        
        # Ensure plugins directory exists
        self.plugins_dir.mkdir(exist_ok=True)
        
        logger.info(f"Plugin manager initialized, plugins dir: {self.plugins_dir}")
    
    def discover_plugins(self) -> Dict[str, Type]:
        """
        Discover all available plugins.
        
        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        plugins = {}
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return plugins
        
        # Look for plugin directories
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
                continue
            
            plugin_name = plugin_dir.name
            plugin_file = plugin_dir / "__init__.py"
            
            if not plugin_file.exists():
                logger.debug(f"Skipping {plugin_name}: no __init__.py found")
                continue
            
            try:
                plugin_class = self._load_plugin_class(plugin_name, plugin_file)
                if plugin_class:
                    plugins[plugin_name] = plugin_class
                    logger.info(f"Discovered plugin: {plugin_name}")
                
            except Exception as e:
                logger.error(f"Failed to discover plugin {plugin_name}: {e}", exc_info=True)
        
        self.plugin_classes = plugins
        return plugins
    
    def _load_plugin_class(self, plugin_name: str, plugin_file: Path) -> Optional[Type]:
        """Load a plugin class from a file."""
        try:
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", 
                plugin_file
            )
            
            if not spec or not spec.loader:
                logger.error(f"Could not create spec for plugin {plugin_name}")
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module, plugin_name)
            
            if not plugin_class:
                logger.error(f"No valid plugin class found in {plugin_name}")
                return None
            
            return plugin_class
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            return None
    
    def _find_plugin_class(self, module, plugin_name: str) -> Optional[Type]:
        """Find the main plugin class in a module."""
        from plugins.base_plugin import BasePlugin
        
        # Look for classes that inherit from BasePlugin
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (obj != BasePlugin and 
                issubclass(obj, BasePlugin) and 
                obj.__module__ == module.__name__):
                return obj
        
        # Fallback: look for class with specific naming patterns
        class_names = [
            f"{plugin_name.title()}Plugin",
            f"{plugin_name.title()}Widget",
            f"{plugin_name.replace('_', '').title()}Plugin",
            "Plugin",
            "Widget"
        ]
        
        for class_name in class_names:
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                if inspect.isclass(cls):
                    return cls
        
        return None
    
    def load_plugin(self, plugin_name: str) -> Optional[Any]:
        """
        Load and instantiate a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            Plugin instance or None if loading failed
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]
        
        if plugin_name not in self.plugin_classes:
            logger.error(f"Plugin {plugin_name} not found in discovered plugins")
            return None
        
        try:
            plugin_class = self.plugin_classes[plugin_name]
            plugin_instance = plugin_class(self.app)
            
            self.loaded_plugins[plugin_name] = plugin_instance
            logger.info(f"Loaded plugin: {plugin_name}")
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            return None
    
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin."""
        if plugin_name in self.loaded_plugins:
            try:
                plugin = self.loaded_plugins[plugin_name]
                if hasattr(plugin, 'cleanup'):
                    plugin.cleanup()
                
                del self.loaded_plugins[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
                
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")
    
    def reload_plugin(self, plugin_name: str) -> Optional[Any]:
        """Reload a plugin."""
        self.unload_plugin(plugin_name)
        
        # Clear from plugin classes to force rediscovery
        if plugin_name in self.plugin_classes:
            del self.plugin_classes[plugin_name]
        
        # Rediscover and load
        self.discover_plugins()
        return self.load_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a loaded plugin instance."""
        return self.loaded_plugins.get(plugin_name)
    
    def get_loaded_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugin instances."""
        return self.loaded_plugins.copy()
    
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugin names."""
        return list(self.plugin_classes.keys())
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self.loaded_plugins
    
    def cleanup(self):
        """Cleanup all plugins."""
        for plugin_name in list(self.loaded_plugins.keys()):
            self.unload_plugin(plugin_name)
        
        self.plugin_classes.clear()
        logger.info("Plugin manager cleaned up")
