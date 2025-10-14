"""
Find & Replace Plugin for AutoCAD Text Tools.

This plugin provides comprehensive text find and replace functionality with:
- Batch processing of DWG files
- Regular expression support
- Title block management
- Stamp/layer management
- Excel reporting
- Preview mode
"""

from .find_replace_plugin import FindReplacePlugin

__all__ = ['FindReplacePlugin']
