"""
Scaling Tool for Text Unifier Plugin.

Provides text scaling functionality for AutoCAD text entities
with support for different scaling modes and selection methods.
"""

from typing import List, Dict, Any, Optional
import math

from core.autocad_bridge import AutoCADBridge


class ScalingTool:
    """
    Tool for scaling text entities in AutoCAD.
    
    Provides various scaling operations including:
    - Scale selected text
    - Scale by text style
    - Scale by layer
    - Proportional scaling
    """
    
    def __init__(self, autocad_bridge: AutoCADBridge):
        self.bridge = autocad_bridge
    
    def scale_selected_text(self, scale_factor: float) -> Dict[str, Any]:
        """
        Scale currently selected text entities.
        
        Args:
            scale_factor: Scaling factor (1.0 = no change)
            
        Returns:
            Dictionary with scaling results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        try:
            # Get selection set
            selection = self.bridge.doc.SelectionSets.Add("TempScaling")
            
            try:
                # Get current selection or prompt user to select
                selection.SelectOnScreen()
                
                scaled_count = 0
                
                for entity in selection:
                    if self._is_text_entity(entity):
                        if self._scale_text_entity(entity, scale_factor):
                            scaled_count += 1
                
                return {
                    'count': scaled_count,
                    'scale_factor': scale_factor,
                    'success': True
                }
                
            finally:
                # Clean up selection set
                try:
                    selection.Delete()
                except Exception:
                    pass
                    
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
    
    def scale_by_text_style(self, text_style: str, scale_factor: float) -> Dict[str, Any]:
        """
        Scale all text entities with specified text style.
        
        Args:
            text_style: Name of text style to scale
            scale_factor: Scaling factor
            
        Returns:
            Dictionary with scaling results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        scaled_count = 0
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if (self._is_text_entity(entity) and 
                            self._get_text_style(entity) == text_style):
                            if self._scale_text_entity(entity, scale_factor):
                                scaled_count += 1
                                
                except Exception:
                    continue
            
            return {
                'count': scaled_count,
                'text_style': text_style,
                'scale_factor': scale_factor,
                'success': True
            }
            
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
    
    def scale_by_layer(self, layer_name: str, scale_factor: float) -> Dict[str, Any]:
        """
        Scale all text entities on specified layer.
        
        Args:
            layer_name: Name of layer
            scale_factor: Scaling factor
            
        Returns:
            Dictionary with scaling results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        scaled_count = 0
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if (self._is_text_entity(entity) and 
                            entity.Layer == layer_name):
                            if self._scale_text_entity(entity, scale_factor):
                                scaled_count += 1
                                
                except Exception:
                    continue
            
            return {
                'count': scaled_count,
                'layer': layer_name,
                'scale_factor': scale_factor,
                'success': True
            }
            
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
    
    def scale_by_height_range(self, min_height: float, max_height: float, 
                             scale_factor: float) -> Dict[str, Any]:
        """
        Scale text entities within specified height range.
        
        Args:
            min_height: Minimum text height
            max_height: Maximum text height
            scale_factor: Scaling factor
            
        Returns:
            Dictionary with scaling results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        scaled_count = 0
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if self._is_text_entity(entity):
                            height = self._get_text_height(entity)
                            if height and min_height <= height <= max_height:
                                if self._scale_text_entity(entity, scale_factor):
                                    scaled_count += 1
                                    
                except Exception:
                    continue
            
            return {
                'count': scaled_count,
                'min_height': min_height,
                'max_height': max_height,
                'scale_factor': scale_factor,
                'success': True
            }
            
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
    
    def normalize_text_heights(self, target_height: float) -> Dict[str, Any]:
        """
        Normalize all text to a target height.
        
        Args:
            target_height: Target text height
            
        Returns:
            Dictionary with normalization results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        normalized_count = 0
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if self._is_text_entity(entity):
                            current_height = self._get_text_height(entity)
                            if current_height and current_height != target_height:
                                if self._set_text_height(entity, target_height):
                                    normalized_count += 1
                                    
                except Exception:
                    continue
            
            return {
                'count': normalized_count,
                'target_height': target_height,
                'success': True
            }
            
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
    
    def get_text_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about text entities in the drawing.
        
        Returns:
            Dictionary with text statistics
        """
        if not self.bridge.is_connected():
            return {'error': 'Not connected to AutoCAD'}
        
        stats = {
            'total_count': 0,
            'by_type': {},
            'by_layer': {},
            'by_style': {},
            'height_range': {'min': float('inf'), 'max': 0.0},
            'heights': []
        }
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if self._is_text_entity(entity):
                            stats['total_count'] += 1
                            
                            # Count by type
                            entity_type = entity.EntityName
                            stats['by_type'][entity_type] = stats['by_type'].get(entity_type, 0) + 1
                            
                            # Count by layer
                            layer = entity.Layer
                            stats['by_layer'][layer] = stats['by_layer'].get(layer, 0) + 1
                            
                            # Count by style
                            style = self._get_text_style(entity)
                            if style:
                                stats['by_style'][style] = stats['by_style'].get(style, 0) + 1
                            
                            # Height statistics
                            height = self._get_text_height(entity)
                            if height:
                                stats['heights'].append(height)
                                stats['height_range']['min'] = min(stats['height_range']['min'], height)
                                stats['height_range']['max'] = max(stats['height_range']['max'], height)
                                
                except Exception:
                    continue
            
            # Calculate additional statistics
            if stats['heights']:
                stats['height_range']['average'] = sum(stats['heights']) / len(stats['heights'])
                stats['height_range']['median'] = sorted(stats['heights'])[len(stats['heights']) // 2]
            else:
                stats['height_range'] = {'min': 0, 'max': 0, 'average': 0, 'median': 0}
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def _is_text_entity(self, entity) -> bool:
        """Check if entity is a text entity."""
        try:
            entity_type = entity.EntityName
            return entity_type in ["AcDbText", "AcDbMText", "AcDbAttributeDefinition", "AcDbAttribute"]
        except Exception:
            return False
    
    def _scale_text_entity(self, entity, scale_factor: float) -> bool:
        """Scale a single text entity."""
        try:
            current_height = self._get_text_height(entity)
            if current_height:
                new_height = current_height * scale_factor
                return self._set_text_height(entity, new_height)
        except Exception:
            pass
        
        return False
    
    def _get_text_height(self, entity) -> Optional[float]:
        """Get text height from entity."""
        try:
            if hasattr(entity, 'Height'):
                return entity.Height
        except Exception:
            pass
        
        return None
    
    def _set_text_height(self, entity, height: float) -> bool:
        """Set text height for entity."""
        try:
            if hasattr(entity, 'Height'):
                entity.Height = height
                return True
        except Exception:
            pass
        
        return False
    
    def _get_text_style(self, entity) -> Optional[str]:
        """Get text style from entity."""
        try:
            if hasattr(entity, 'StyleName'):
                return entity.StyleName
        except Exception:
            pass
        
        return None
    
    def scale_text_proportionally(self, reference_height: float, 
                                 target_height: float) -> Dict[str, Any]:
        """
        Scale all text proportionally based on reference height.
        
        Args:
            reference_height: Current reference height
            target_height: Target reference height
            
        Returns:
            Dictionary with scaling results
        """
        if reference_height <= 0:
            return {'count': 0, 'error': 'Invalid reference height', 'success': False}
        
        scale_factor = target_height / reference_height
        
        # Scale all text entities
        return self.scale_all_text(scale_factor)
    
    def scale_all_text(self, scale_factor: float) -> Dict[str, Any]:
        """
        Scale all text entities in the drawing.
        
        Args:
            scale_factor: Scaling factor
            
        Returns:
            Dictionary with scaling results
        """
        if not self.bridge.is_connected():
            return {'count': 0, 'error': 'Not connected to AutoCAD'}
        
        scaled_count = 0
        
        try:
            # Process both model space and paper space
            for space_name in ["ModelSpace", "PaperSpace"]:
                try:
                    if space_name == "ModelSpace":
                        space = self.bridge.doc.ModelSpace
                    else:
                        space = self.bridge.doc.PaperSpace
                    
                    for entity in space:
                        if self._is_text_entity(entity):
                            if self._scale_text_entity(entity, scale_factor):
                                scaled_count += 1
                                
                except Exception:
                    continue
            
            return {
                'count': scaled_count,
                'scale_factor': scale_factor,
                'success': True
            }
            
        except Exception as e:
            return {'count': 0, 'error': str(e), 'success': False}
