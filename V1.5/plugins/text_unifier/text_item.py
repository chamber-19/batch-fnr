"""
Text Item class for Text Unifier Plugin.

Represents a single text entity from AutoCAD with all its properties
and geometric information needed for clustering and unification.
"""

from dataclasses import dataclass
from typing import Any, Optional
from core.geometry import BBox


@dataclass
class TextItem:
    """
    Represents a text entity from AutoCAD.
    
    Contains all the information needed for text clustering,
    unification, and manipulation operations.
    """
    
    # Entity reference
    ent: Any  # AutoCAD entity object
    
    # Text content
    text: str
    
    # Geometric properties
    bbox: BBox
    rotation_deg: float = 0.0
    
    # AutoCAD properties
    layer: str = "0"
    space: str = "ModelSpace"  # "ModelSpace" or "PaperSpace"
    entity_type: str = "AcDbText"  # AcDbText, AcDbMText, etc.
    
    # Text formatting properties
    height: float = 0.0
    width_factor: float = 1.0
    oblique_angle: float = 0.0
    text_style: str = "Standard"
    
    # Additional properties
    color: int = 256  # ByLayer
    linetype: str = "ByLayer"
    lineweight: int = -1  # ByLayer
    
    # Clustering properties
    group_id: Optional[int] = None
    column_id: Optional[int] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Normalize rotation to 0-360 range
        self.rotation_deg = self.rotation_deg % 360.0
        
        # Clean up text
        self.text = self.text.strip() if self.text else ""
    
    @property
    def center_x(self) -> float:
        """Get X coordinate of text center."""
        return self.bbox.center_x
    
    @property
    def center_y(self) -> float:
        """Get Y coordinate of text center."""
        return self.bbox.center_y
    
    @property
    def center_point(self) -> tuple[float, float]:
        """Get center point as (x, y) tuple."""
        return (self.center_x, self.center_y)
    
    @property
    def width(self) -> float:
        """Get text width."""
        return self.bbox.width
    
    @property
    def height_bbox(self) -> float:
        """Get text height from bounding box."""
        return self.bbox.height
    
    @property
    def is_empty(self) -> bool:
        """Check if text is empty or whitespace only."""
        return not self.text or self.text.isspace()
    
    @property
    def is_horizontal(self) -> bool:
        """Check if text is approximately horizontal."""
        return abs(self.rotation_deg) < 5.0 or abs(self.rotation_deg - 360.0) < 5.0
    
    @property
    def is_vertical(self) -> bool:
        """Check if text is approximately vertical."""
        return abs(self.rotation_deg - 90.0) < 5.0 or abs(self.rotation_deg - 270.0) < 5.0
    
    def distance_to(self, other: 'TextItem') -> float:
        """
        Calculate distance to another text item.
        
        Args:
            other: Another TextItem
            
        Returns:
            Distance between text centers
        """
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return (dx * dx + dy * dy) ** 0.5
    
    def angle_difference(self, other: 'TextItem') -> float:
        """
        Calculate angle difference with another text item.
        
        Args:
            other: Another TextItem
            
        Returns:
            Absolute angle difference in degrees (0-180)
        """
        diff = abs(self.rotation_deg - other.rotation_deg)
        return min(diff, 360.0 - diff)
    
    def is_similar_to(self, other: 'TextItem', 
                     distance_tolerance: float = 0.5,
                     angle_tolerance: float = 5.0,
                     text_similarity: bool = True) -> bool:
        """
        Check if this text item is similar to another.
        
        Args:
            other: Another TextItem
            distance_tolerance: Maximum distance for similarity
            angle_tolerance: Maximum angle difference for similarity
            text_similarity: Whether to check text content similarity
            
        Returns:
            True if items are similar
        """
        # Check distance
        if self.distance_to(other) > distance_tolerance:
            return False
        
        # Check angle
        if self.angle_difference(other) > angle_tolerance:
            return False
        
        # Check text similarity if requested
        if text_similarity:
            # Simple text similarity - could be enhanced with fuzzy matching
            if self.text.lower().strip() != other.text.lower().strip():
                return False
        
        return True
    
    def overlaps_with(self, other: 'TextItem', tolerance: float = 0.1) -> bool:
        """
        Check if this text item overlaps with another.
        
        Args:
            other: Another TextItem
            tolerance: Overlap tolerance
            
        Returns:
            True if bounding boxes overlap
        """
        return self.bbox.intersects(other.bbox, tolerance)
    
    def is_in_same_column(self, other: 'TextItem', 
                         x_tolerance: float = 0.5) -> bool:
        """
        Check if this text item is in the same column as another.
        
        Args:
            other: Another TextItem
            x_tolerance: X-coordinate tolerance for column detection
            
        Returns:
            True if items are in the same column
        """
        return abs(self.center_x - other.center_x) <= x_tolerance
    
    def is_in_same_row(self, other: 'TextItem',
                      y_tolerance: float = 0.5) -> bool:
        """
        Check if this text item is in the same row as another.
        
        Args:
            other: Another TextItem
            y_tolerance: Y-coordinate tolerance for row detection
            
        Returns:
            True if items are in the same row
        """
        return abs(self.center_y - other.center_y) <= y_tolerance
    
    def get_insertion_point(self) -> tuple[float, float, float]:
        """
        Get the insertion point for this text item.
        
        Returns:
            (x, y, z) coordinates of insertion point
        """
        # For most text, insertion point is at the bottom-left
        return (self.bbox.minx, self.bbox.miny, self.bbox.minz)
    
    def copy_properties_from(self, other: 'TextItem'):
        """
        Copy formatting properties from another text item.
        
        Args:
            other: Source TextItem to copy properties from
        """
        self.height = other.height
        self.width_factor = other.width_factor
        self.oblique_angle = other.oblique_angle
        self.text_style = other.text_style
        self.color = other.color
        self.linetype = other.linetype
        self.lineweight = other.lineweight
        self.layer = other.layer
    
    def to_dict(self) -> dict:
        """
        Convert TextItem to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'text': self.text,
            'bbox': {
                'minx': self.bbox.minx,
                'miny': self.bbox.miny,
                'minz': self.bbox.minz,
                'maxx': self.bbox.maxx,
                'maxy': self.bbox.maxy,
                'maxz': self.bbox.maxz
            },
            'rotation_deg': self.rotation_deg,
            'layer': self.layer,
            'space': self.space,
            'entity_type': self.entity_type,
            'height': self.height,
            'width_factor': self.width_factor,
            'oblique_angle': self.oblique_angle,
            'text_style': self.text_style,
            'color': self.color,
            'linetype': self.linetype,
            'lineweight': self.lineweight,
            'group_id': self.group_id,
            'column_id': self.column_id
        }
    
    def __str__(self) -> str:
        """String representation of TextItem."""
        return f"TextItem('{self.text}' at {self.center_point}, {self.entity_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of TextItem."""
        return (f"TextItem(text='{self.text}', center=({self.center_x:.2f}, {self.center_y:.2f}), "
                f"rotation={self.rotation_deg:.1f}°, layer='{self.layer}', type='{self.entity_type}')")
    
    def __eq__(self, other) -> bool:
        """Check equality with another TextItem."""
        if not isinstance(other, TextItem):
            return False
        
        return (self.text == other.text and
                self.bbox == other.bbox and
                abs(self.rotation_deg - other.rotation_deg) < 0.1 and
                self.layer == other.layer and
                self.entity_type == other.entity_type)
    
    def __hash__(self) -> int:
        """Hash function for TextItem."""
        return hash((self.text, self.center_x, self.center_y, self.rotation_deg, self.layer))
