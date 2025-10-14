"""
Text Unifier Core Engine.

Provides the core functionality for text collection, clustering, grouping,
and unification operations in AutoCAD drawings.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from core.autocad_bridge import AutoCADBridge
from core.geometry import BBox
from .text_item import TextItem
from .text_group import TextGroup


class TextUnifierCore:
    """
    Core engine for text unification operations.
    
    Handles text collection, clustering, grouping, and unification
    with various strategies and algorithms.
    """
    
    def __init__(self, autocad_bridge: AutoCADBridge):
        self.bridge = autocad_bridge
        self.preview_group_id = 9999  # Special group ID for preview objects
        
    def collect_and_group_text(self, settings: Dict[str, Any]) -> List[TextGroup]:
        """
        Collect text from AutoCAD and group similar items.
        
        Args:
            settings: Unification settings
            
        Returns:
            List of TextGroup objects
        """
        # Collect text items
        text_items = self._collect_text_items()
        
        if not text_items:
            return []
        
        # Filter and prepare items
        filtered_items = self._filter_text_items(text_items, settings)
        
        # Detect columns
        self._detect_columns(filtered_items, settings)
        
        # Group similar items
        groups = self._group_similar_items(filtered_items, settings)
        
        return groups
    
    def _collect_text_items(self) -> List[TextItem]:
        """Collect text items from AutoCAD."""
        if not self.bridge.is_connected():
            return []
        
        text_items = []
        
        # Use the bridge's collect_text_entities method
        bridge_items = self.bridge.collect_text_entities()
        
        for bridge_item in bridge_items:
            # Convert bridge TextItem to plugin TextItem
            text_item = TextItem(
                ent=bridge_item.ent,
                text=bridge_item.text,
                bbox=bridge_item.bbox,
                rotation_deg=bridge_item.rotation_deg,
                layer=bridge_item.layer,
                space=bridge_item.space,
                entity_type=bridge_item.entity_type
            )
            
            # Get additional properties from entity
            try:
                if hasattr(bridge_item.ent, 'Height'):
                    text_item.height = bridge_item.ent.Height
                if hasattr(bridge_item.ent, 'ScaleFactor'):
                    text_item.width_factor = bridge_item.ent.ScaleFactor
                if hasattr(bridge_item.ent, 'ObliqueAngle'):
                    text_item.oblique_angle = math.degrees(bridge_item.ent.ObliqueAngle)
                if hasattr(bridge_item.ent, 'StyleName'):
                    text_item.text_style = bridge_item.ent.StyleName
                if hasattr(bridge_item.ent, 'Color'):
                    text_item.color = bridge_item.ent.Color
            except Exception:
                pass  # Use defaults if properties can't be read
            
            text_items.append(text_item)
        
        return text_items
    
    def _filter_text_items(self, text_items: List[TextItem], 
                          settings: Dict[str, Any]) -> List[TextItem]:
        """Filter text items based on settings."""
        filtered = []
        
        for item in text_items:
            # Skip empty text
            if item.is_empty:
                continue
            
            # Skip very small text (likely dimension text)
            if item.height > 0 and item.height < 0.05:
                continue
            
            # Add other filtering criteria as needed
            filtered.append(item)
        
        return filtered
    
    def _detect_columns(self, text_items: List[TextItem], settings: Dict[str, Any]):
        """Detect and assign column IDs to text items."""
        distance_tolerance = settings.get('distance_tolerance', 0.5)
        
        # Sort by X coordinate
        sorted_items = sorted(text_items, key=lambda item: item.center_x)
        
        column_id = 0
        current_column_x = None
        
        for item in sorted_items:
            if (current_column_x is None or 
                abs(item.center_x - current_column_x) > distance_tolerance):
                # Start new column
                column_id += 1
                current_column_x = item.center_x
            
            item.column_id = column_id
    
    def _group_similar_items(self, text_items: List[TextItem], 
                           settings: Dict[str, Any]) -> List[TextGroup]:
        """Group similar text items together."""
        distance_tolerance = settings.get('distance_tolerance', 0.5)
        angle_tolerance = settings.get('angle_tolerance', 5.0)
        
        groups = []
        group_id = 1
        
        # Create groups based on proximity and similarity
        ungrouped_items = text_items.copy()
        
        while ungrouped_items:
            # Start new group with first ungrouped item
            seed_item = ungrouped_items.pop(0)
            group = TextGroup(group_id=group_id)
            group.add_text_item(seed_item)
            
            # Find similar items to add to this group
            items_to_remove = []
            
            for item in ungrouped_items:
                if self._should_group_together(seed_item, item, distance_tolerance, angle_tolerance):
                    group.add_text_item(item)
                    items_to_remove.append(item)
            
            # Remove grouped items from ungrouped list
            for item in items_to_remove:
                ungrouped_items.remove(item)
            
            # Only keep groups with multiple items
            if group.count > 1:
                groups.append(group)
                group_id += 1
        
        return groups
    
    def _should_group_together(self, item1: TextItem, item2: TextItem,
                             distance_tolerance: float, angle_tolerance: float) -> bool:
        """Check if two items should be grouped together."""
        # Check distance
        distance = item1.distance_to(item2)
        if distance > distance_tolerance:
            return False
        
        # Check angle similarity
        angle_diff = item1.angle_difference(item2)
        if angle_diff > angle_tolerance:
            return False
        
        # Check if text is similar (optional - could be made configurable)
        # For now, group items regardless of text content
        
        return True
    
    def create_preview(self, groups: List[TextGroup], settings: Dict[str, Any]):
        """Create preview objects for selected groups."""
        self.clear_preview()
        
        strategy = settings.get('strategy', 'nudge')
        
        for group in groups:
            if not group.selected:
                continue
            
            try:
                if strategy == 'nudge':
                    self._create_nudge_preview(group, settings)
                elif strategy == 'mask':
                    self._create_mask_preview(group, settings)
                elif strategy == 'move':
                    self._create_move_preview(group, settings)
            except Exception as e:
                print(f"Error creating preview for group {group.group_id}: {e}")
    
    def _create_nudge_preview(self, group: TextGroup, settings: Dict[str, Any]):
        """Create preview for nudge strategy."""
        if not group.target_position:
            return
        
        target_x, target_y = group.target_position
        
        # Create preview lines showing movement
        for item in group.text_items:
            if abs(item.center_x - target_x) > 0.01 or abs(item.center_y - target_y) > 0.01:
                # Create line from current position to target
                try:
                    start_point = [item.center_x, item.center_y, 0]
                    end_point = [target_x, target_y, 0]
                    
                    if self.bridge.doc and self.bridge.doc.ModelSpace:
                        line = self.bridge.doc.ModelSpace.AddLine(start_point, end_point)
                        line.Color = 3  # Green
                        group.preview_objects.append(line)
                except Exception:
                    pass
    
    def _create_mask_preview(self, group: TextGroup, settings: Dict[str, Any]):
        """Create preview for mask strategy."""
        # Show which items will be hidden
        for i, item in enumerate(group.text_items):
            if i == 0:  # Keep first item visible
                continue
            
            try:
                # Create rectangle around text to be masked
                bbox = item.bbox
                points = [
                    [bbox.minx, bbox.miny, 0],
                    [bbox.maxx, bbox.miny, 0],
                    [bbox.maxx, bbox.maxy, 0],
                    [bbox.minx, bbox.maxy, 0],
                    [bbox.minx, bbox.miny, 0]  # Close the rectangle
                ]
                
                if self.bridge.doc and self.bridge.doc.ModelSpace:
                    polyline = self.bridge.doc.ModelSpace.AddPolyline(points)
                    polyline.Color = 1  # Red
                    group.preview_objects.append(polyline)
            except Exception:
                pass
    
    def _create_move_preview(self, group: TextGroup, settings: Dict[str, Any]):
        """Create preview for move strategy."""
        if not group.target_position:
            return
        
        target_x, target_y = group.target_position
        text_style = settings.get('text_style', 'Standard')
        plot_height = settings.get('plot_height', 0.125)
        
        try:
            # Create preview MText at target position
            if self.bridge.doc and self.bridge.doc.ModelSpace:
                # Calculate text width for MText
                text_width = max(len(group.unified_text) * plot_height * 0.6, 1.0)
                
                mtext = self.bridge.doc.ModelSpace.AddMText(
                    [target_x, target_y, 0],
                    text_width,
                    group.unified_text
                )
                mtext.Height = plot_height
                mtext.Color = 2  # Yellow
                
                if text_style:
                    try:
                        mtext.StyleName = text_style
                    except Exception:
                        pass
                
                group.preview_objects.append(mtext)
        except Exception:
            pass
    
    def clear_preview(self):
        """Clear all preview objects."""
        try:
            if self.bridge.doc:
                # Find and delete preview objects
                for space_name in ["ModelSpace", "PaperSpace"]:
                    try:
                        if space_name == "ModelSpace":
                            space = self.bridge.doc.ModelSpace
                        else:
                            space = self.bridge.doc.PaperSpace
                        
                        # Collect objects to delete (can't delete while iterating)
                        objects_to_delete = []
                        
                        for entity in space:
                            try:
                                # Check if this is a preview object (by color or other marker)
                                if (hasattr(entity, 'Color') and 
                                    entity.Color in [1, 2, 3]):  # Red, Yellow, Green
                                    objects_to_delete.append(entity)
                            except Exception:
                                continue
                        
                        # Delete preview objects
                        for obj in objects_to_delete:
                            try:
                                obj.Delete()
                            except Exception:
                                pass
                                
                    except Exception:
                        continue
        except Exception:
            pass
    
    def resolve_groups(self, groups: List[TextGroup], 
                      settings: Dict[str, Any]) -> Dict[str, int]:
        """Resolve (apply unification to) selected groups."""
        strategy = settings.get('strategy', 'nudge')
        resolved_count = 0
        
        for group in groups:
            if not group.selected:
                continue
            
            try:
                if strategy == 'nudge':
                    if self._apply_nudge_strategy(group, settings):
                        resolved_count += 1
                elif strategy == 'mask':
                    if self._apply_mask_strategy(group, settings):
                        resolved_count += 1
                elif strategy == 'move':
                    if self._apply_move_strategy(group, settings):
                        resolved_count += 1
            except Exception as e:
                print(f"Error resolving group {group.group_id}: {e}")
        
        return {'resolved': resolved_count}
    
    def _apply_nudge_strategy(self, group: TextGroup, settings: Dict[str, Any]) -> bool:
        """Apply nudge strategy to group."""
        if not group.target_position:
            return False
        
        target_x, target_y = group.target_position
        changed = False
        
        for item in group.text_items:
            try:
                # Move text to target position
                if hasattr(item.ent, 'InsertionPoint'):
                    current_point = item.ent.InsertionPoint
                    new_point = [target_x, target_y, current_point[2]]
                    item.ent.InsertionPoint = new_point
                    changed = True
            except Exception:
                continue
        
        return changed
    
    def _apply_mask_strategy(self, group: TextGroup, settings: Dict[str, Any]) -> bool:
        """Apply mask strategy to group."""
        # Hide all but the first item
        changed = False
        
        for i, item in enumerate(group.text_items):
            if i == 0:  # Keep first item
                continue
            
            try:
                # Move to non-plotting layer or make invisible
                item.ent.Visible = False
                changed = True
            except Exception:
                continue
        
        return changed
    
    def _apply_move_strategy(self, group: TextGroup, settings: Dict[str, Any]) -> bool:
        """Apply move strategy to group."""
        if not group.target_position:
            return False
        
        target_x, target_y = group.target_position
        text_style = settings.get('text_style', 'Standard')
        plot_height = settings.get('plot_height', 0.125)
        
        try:
            # Create new MText
            if self.bridge.doc and self.bridge.doc.ModelSpace:
                text_width = max(len(group.unified_text) * plot_height * 0.6, 1.0)
                
                mtext = self.bridge.doc.ModelSpace.AddMText(
                    [target_x, target_y, 0],
                    text_width,
                    group.unified_text
                )
                mtext.Height = plot_height
                
                if text_style:
                    try:
                        mtext.StyleName = text_style
                    except Exception:
                        pass
                
                # Delete original text items
                for item in group.text_items:
                    try:
                        item.ent.Delete()
                    except Exception:
                        continue
                
                return True
        except Exception:
            pass
        
        return False
    
    def convert_groups(self, groups: List[TextGroup], 
                      settings: Dict[str, Any]) -> Dict[str, int]:
        """Convert groups to final format."""
        # For now, this is the same as resolve
        return self.resolve_groups(groups, settings)
