"""
Text Group class for Text Unifier Plugin.

Represents a group of similar text items that can be unified together.
Provides methods for group management, text unification, and preview generation.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from core.geometry import BBox
from .text_item import TextItem


@dataclass
class TextGroup:
    """
    Represents a group of similar text items for unification.
    
    Contains multiple TextItem objects that are similar enough to be
    unified into a single text entity or aligned together.
    """
    
    # Group properties
    group_id: int
    text_items: List[TextItem] = field(default_factory=list)
    
    # Unification properties
    unified_text: str = ""
    target_position: Optional[Tuple[float, float]] = None
    target_rotation: float = 0.0
    
    # UI properties
    selected: bool = True
    
    # Preview properties
    preview_objects: List[Any] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.text_items:
            self._calculate_unified_properties()
    
    def add_text_item(self, text_item: TextItem):
        """
        Add a text item to this group.
        
        Args:
            text_item: TextItem to add
        """
        text_item.group_id = self.group_id
        self.text_items.append(text_item)
        self._calculate_unified_properties()
    
    def remove_text_item(self, text_item: TextItem):
        """
        Remove a text item from this group.
        
        Args:
            text_item: TextItem to remove
        """
        if text_item in self.text_items:
            text_item.group_id = None
            self.text_items.remove(text_item)
            self._calculate_unified_properties()
    
    def _calculate_unified_properties(self):
        """Calculate unified properties from all text items."""
        if not self.text_items:
            return
        
        # Calculate unified text (use most common or longest)
        text_counts = {}
        for item in self.text_items:
            text = item.text.strip()
            text_counts[text] = text_counts.get(text, 0) + 1
        
        if text_counts:
            # Use most common text, or longest if tie
            max_count = max(text_counts.values())
            candidates = [text for text, count in text_counts.items() if count == max_count]
            self.unified_text = max(candidates, key=len)
        
        # Calculate target position (centroid)
        total_x = sum(item.center_x for item in self.text_items)
        total_y = sum(item.center_y for item in self.text_items)
        count = len(self.text_items)
        
        self.target_position = (total_x / count, total_y / count)
        
        # Calculate target rotation (average)
        # Handle circular nature of angles
        sin_sum = sum(math.sin(math.radians(item.rotation_deg)) for item in self.text_items)
        cos_sum = sum(math.cos(math.radians(item.rotation_deg)) for item in self.text_items)
        
        avg_angle_rad = math.atan2(sin_sum / count, cos_sum / count)
        self.target_rotation = math.degrees(avg_angle_rad) % 360.0
    
    @property
    def count(self) -> int:
        """Get number of text items in group."""
        return len(self.text_items)
    
    @property
    def is_empty(self) -> bool:
        """Check if group is empty."""
        return len(self.text_items) == 0
    
    @property
    def bounding_box(self) -> Optional[BBox]:
        """Get bounding box encompassing all text items."""
        if not self.text_items:
            return None
        
        min_x = min(item.bbox.minx for item in self.text_items)
        min_y = min(item.bbox.miny for item in self.text_items)
        min_z = min(item.bbox.minz for item in self.text_items)
        max_x = max(item.bbox.maxx for item in self.text_items)
        max_y = max(item.bbox.maxy for item in self.text_items)
        max_z = max(item.bbox.maxz for item in self.text_items)
        
        return BBox(min_x, min_y, min_z, max_x, max_y, max_z)
    
    @property
    def center_point(self) -> Optional[Tuple[float, float]]:
        """Get center point of the group."""
        return self.target_position
    
    @property
    def layers(self) -> List[str]:
        """Get unique layers used by text items in group."""
        return list(set(item.layer for item in self.text_items))
    
    @property
    def text_styles(self) -> List[str]:
        """Get unique text styles used by text items in group."""
        return list(set(item.text_style for item in self.text_items))
    
    @property
    def entity_types(self) -> List[str]:
        """Get unique entity types in group."""
        return list(set(item.entity_type for item in self.text_items))
    
    def get_display_text(self, max_length: int = 50) -> str:
        """
        Get display text for UI.
        
        Args:
            max_length: Maximum length of display text
            
        Returns:
            Formatted display text
        """
        if not self.unified_text:
            return f"({self.count} items)"
        
        text = self.unified_text
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return f"{text} ({self.count} items)"
    
    def get_representative_item(self) -> Optional[TextItem]:
        """
        Get a representative text item from the group.
        
        Returns:
            TextItem that best represents the group
        """
        if not self.text_items:
            return None
        
        # Find item closest to target position
        if self.target_position:
            target_x, target_y = self.target_position
            
            min_distance = float('inf')
            best_item = self.text_items[0]
            
            for item in self.text_items:
                distance = ((item.center_x - target_x) ** 2 + 
                           (item.center_y - target_y) ** 2) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    best_item = item
            
            return best_item
        
        return self.text_items[0]
    
    def calculate_spread(self) -> Dict[str, float]:
        """
        Calculate spread statistics for the group.
        
        Returns:
            Dictionary with spread statistics
        """
        if len(self.text_items) < 2:
            return {'x_spread': 0.0, 'y_spread': 0.0, 'max_distance': 0.0}
        
        x_coords = [item.center_x for item in self.text_items]
        y_coords = [item.center_y for item in self.text_items]
        
        x_spread = max(x_coords) - min(x_coords)
        y_spread = max(y_coords) - min(y_coords)
        
        # Calculate maximum distance between any two items
        max_distance = 0.0
        for i, item1 in enumerate(self.text_items):
            for item2 in self.text_items[i+1:]:
                distance = item1.distance_to(item2)
                max_distance = max(max_distance, distance)
        
        return {
            'x_spread': x_spread,
            'y_spread': y_spread,
            'max_distance': max_distance
        }
    
    def is_column_like(self, x_tolerance: float = 0.5) -> bool:
        """
        Check if group forms a column (vertically aligned).
        
        Args:
            x_tolerance: X-coordinate tolerance
            
        Returns:
            True if group is column-like
        """
        if len(self.text_items) < 2:
            return False
        
        x_coords = [item.center_x for item in self.text_items]
        x_spread = max(x_coords) - min(x_coords)
        
        return x_spread <= x_tolerance
    
    def is_row_like(self, y_tolerance: float = 0.5) -> bool:
        """
        Check if group forms a row (horizontally aligned).
        
        Args:
            y_tolerance: Y-coordinate tolerance
            
        Returns:
            True if group is row-like
        """
        if len(self.text_items) < 2:
            return False
        
        y_coords = [item.center_y for item in self.text_items]
        y_spread = max(y_coords) - min(y_coords)
        
        return y_spread <= y_tolerance
    
    def sort_items_by_position(self, sort_by: str = "auto"):
        """
        Sort text items by position.
        
        Args:
            sort_by: Sort method ("auto", "x", "y", "distance")
        """
        if sort_by == "auto":
            # Auto-detect based on group shape
            if self.is_column_like():
                sort_by = "y"
            elif self.is_row_like():
                sort_by = "x"
            else:
                sort_by = "distance"
        
        if sort_by == "x":
            self.text_items.sort(key=lambda item: item.center_x)
        elif sort_by == "y":
            self.text_items.sort(key=lambda item: item.center_y, reverse=True)  # Top to bottom
        elif sort_by == "distance" and self.target_position:
            target_x, target_y = self.target_position
            self.text_items.sort(key=lambda item: 
                ((item.center_x - target_x) ** 2 + (item.center_y - target_y) ** 2) ** 0.5)
    
    def merge_with(self, other_group: 'TextGroup'):
        """
        Merge another group into this one.
        
        Args:
            other_group: TextGroup to merge
        """
        for item in other_group.text_items:
            self.add_text_item(item)
        
        # Clear the other group
        other_group.text_items.clear()
        other_group.preview_objects.clear()
    
    def split_at_index(self, index: int) -> Optional['TextGroup']:
        """
        Split group at specified index.
        
        Args:
            index: Index to split at
            
        Returns:
            New TextGroup with items from index onwards, or None if invalid
        """
        if index <= 0 or index >= len(self.text_items):
            return None
        
        # Create new group
        new_group = TextGroup(group_id=self.group_id + 1000)  # Temporary ID
        
        # Move items to new group
        items_to_move = self.text_items[index:]
        self.text_items = self.text_items[:index]
        
        for item in items_to_move:
            new_group.add_text_item(item)
        
        # Recalculate properties
        self._calculate_unified_properties()
        
        return new_group
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert group to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'group_id': self.group_id,
            'unified_text': self.unified_text,
            'target_position': self.target_position,
            'target_rotation': self.target_rotation,
            'selected': self.selected,
            'text_items': [item.to_dict() for item in self.text_items],
            'count': self.count,
            'spread': self.calculate_spread()
        }
    
    def __str__(self) -> str:
        """String representation of TextGroup."""
        return f"TextGroup({self.group_id}: '{self.unified_text}', {self.count} items)"
    
    def __repr__(self) -> str:
        """Detailed string representation of TextGroup."""
        return (f"TextGroup(id={self.group_id}, text='{self.unified_text}', "
                f"count={self.count}, selected={self.selected})")
    
    def __len__(self) -> int:
        """Get number of text items in group."""
        return len(self.text_items)
    
    def __iter__(self):
        """Iterate over text items."""
        return iter(self.text_items)
    
    def __getitem__(self, index):
        """Get text item by index."""
        return self.text_items[index]
