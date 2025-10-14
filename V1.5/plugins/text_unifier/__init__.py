"""
Text Unifier Plugin for AutoCAD Text Tools.

This plugin provides advanced text unification and scaling functionality with:
- Text clustering and grouping
- Column detection
- Multiple unification strategies (Nudge, Mask, Move)
- Text wrapping and scaling
- Preview system with visual feedback
"""

from .text_unifier_plugin import TextUnifierPlugin

__all__ = ['TextUnifierPlugin']
