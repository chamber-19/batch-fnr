"""
Geometry utilities for AutoCAD Text Tools.

This module provides geometric calculations and data structures used throughout
the application, particularly for text clustering and spatial operations.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class BBox:
    """
    3D Bounding box representation.
    
    Provides methods for geometric operations on bounding boxes including
    intersection, union, translation, and spatial relationships.
    """
    minx: float
    miny: float
    minz: float
    maxx: float
    maxy: float
    maxz: float
    
    def width(self) -> float:
        """Get width (X dimension)."""
        return self.maxx - self.minx
    
    def height(self) -> float:
        """Get height (Y dimension)."""
        return self.maxy - self.miny
    
    def depth(self) -> float:
        """Get depth (Z dimension)."""
        return self.maxz - self.minz
    
    def center(self) -> Tuple[float, float, float]:
        """Get center point."""
        return (
            (self.minx + self.maxx) / 2,
            (self.miny + self.maxy) / 2,
            (self.minz + self.maxz) / 2
        )
    
    def center_2d(self) -> Tuple[float, float]:
        """Get 2D center point (X, Y only)."""
        return (
            (self.minx + self.maxx) / 2,
            (self.miny + self.maxy) / 2
        )
    
    def area(self) -> float:
        """Get 2D area (width * height)."""
        return self.width() * self.height()
    
    def volume(self) -> float:
        """Get 3D volume."""
        return self.width() * self.height() * self.depth()
    
    def translate(self, dx: float, dy: float, dz: float = 0) -> 'BBox':
        """Translate bounding box by given offsets."""
        return BBox(
            self.minx + dx, self.miny + dy, self.minz + dz,
            self.maxx + dx, self.maxy + dy, self.maxz + dz
        )
    
    def expand(self, margin: float) -> 'BBox':
        """Expand bounding box by margin in all directions."""
        return BBox(
            self.minx - margin, self.miny - margin, self.minz - margin,
            self.maxx + margin, self.maxy + margin, self.maxz + margin
        )
    
    def expand_2d(self, margin: float) -> 'BBox':
        """Expand bounding box by margin in X and Y directions only."""
        return BBox(
            self.minx - margin, self.miny - margin, self.minz,
            self.maxx + margin, self.maxy + margin, self.maxz
        )
    
    def intersects_2d(self, other: 'BBox') -> bool:
        """Check if this bbox intersects with another in 2D (X, Y only)."""
        return not (
            self.maxx < other.minx or
            self.minx > other.maxx or
            self.maxy < other.miny or
            self.miny > other.maxy
        )
    
    def intersects_3d(self, other: 'BBox') -> bool:
        """Check if this bbox intersects with another in 3D."""
        return (
            self.intersects_2d(other) and
            not (self.maxz < other.minz or self.minz > other.maxz)
        )
    
    def contains_point_2d(self, x: float, y: float) -> bool:
        """Check if point is inside this bbox in 2D."""
        return (
            self.minx <= x <= self.maxx and
            self.miny <= y <= self.maxy
        )
    
    def contains_point_3d(self, x: float, y: float, z: float) -> bool:
        """Check if point is inside this bbox in 3D."""
        return (
            self.contains_point_2d(x, y) and
            self.minz <= z <= self.maxz
        )
    
    def contains_bbox_2d(self, other: 'BBox') -> bool:
        """Check if this bbox completely contains another in 2D."""
        return (
            self.minx <= other.minx and
            self.miny <= other.miny and
            self.maxx >= other.maxx and
            self.maxy >= other.maxy
        )
    
    def union(self, other: 'BBox') -> 'BBox':
        """Get union (combined) bounding box."""
        return BBox(
            min(self.minx, other.minx),
            min(self.miny, other.miny),
            min(self.minz, other.minz),
            max(self.maxx, other.maxx),
            max(self.maxy, other.maxy),
            max(self.maxz, other.maxz)
        )
    
    def intersection(self, other: 'BBox') -> Optional['BBox']:
        """Get intersection bounding box, None if no intersection."""
        if not self.intersects_3d(other):
            return None
        
        return BBox(
            max(self.minx, other.minx),
            max(self.miny, other.miny),
            max(self.minz, other.minz),
            min(self.maxx, other.maxx),
            min(self.maxy, other.maxy),
            min(self.maxz, other.maxz)
        )
    
    def distance_to_point_2d(self, x: float, y: float) -> float:
        """Get minimum distance from bbox to point in 2D."""
        if self.contains_point_2d(x, y):
            return 0.0
        
        dx = max(0, max(self.minx - x, x - self.maxx))
        dy = max(0, max(self.miny - y, y - self.maxy))
        return math.sqrt(dx * dx + dy * dy)
    
    def distance_to_bbox_2d(self, other: 'BBox') -> float:
        """Get minimum distance between two bboxes in 2D."""
        if self.intersects_2d(other):
            return 0.0
        
        dx = max(0, max(self.minx - other.maxx, other.minx - self.maxx))
        dy = max(0, max(self.miny - other.maxy, other.miny - self.maxy))
        return math.sqrt(dx * dx + dy * dy)
    
    def gap_to_bbox_x(self, other: 'BBox') -> float:
        """Get horizontal gap between bboxes (negative if overlapping)."""
        if self.maxx < other.minx:
            return other.minx - self.maxx
        elif other.maxx < self.minx:
            return self.minx - other.maxx
        else:
            # Overlapping
            return -min(self.maxx - other.minx, other.maxx - self.minx)
    
    def gap_to_bbox_y(self, other: 'BBox') -> float:
        """Get vertical gap between bboxes (negative if overlapping)."""
        if self.maxy < other.miny:
            return other.miny - self.maxy
        elif other.maxy < self.miny:
            return self.miny - other.maxy
        else:
            # Overlapping
            return -min(self.maxy - other.miny, other.maxy - self.miny)
    
    @classmethod
    def from_points(cls, points: List[Tuple[float, float, float]]) -> 'BBox':
        """Create bounding box from list of 3D points."""
        if not points:
            return cls(0, 0, 0, 0, 0, 0)
        
        xs, ys, zs = zip(*points)
        return cls(
            min(xs), min(ys), min(zs),
            max(xs), max(ys), max(zs)
        )
    
    @classmethod
    def from_points_2d(cls, points: List[Tuple[float, float]]) -> 'BBox':
        """Create bounding box from list of 2D points (Z=0)."""
        if not points:
            return cls(0, 0, 0, 0, 0, 0)
        
        xs, ys = zip(*points)
        return cls(
            min(xs), min(ys), 0,
            max(xs), max(ys), 0
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"BBox({self.minx:.3f}, {self.miny:.3f}, {self.minz:.3f}, {self.maxx:.3f}, {self.maxy:.3f}, {self.maxz:.3f})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()


def normalize_angle(angle_deg: float) -> float:
    """Normalize angle to [0, 360) degrees."""
    while angle_deg < 0:
        angle_deg += 360
    while angle_deg >= 360:
        angle_deg -= 360
    return angle_deg


def angle_difference(angle1_deg: float, angle2_deg: float) -> float:
    """Get the smallest difference between two angles in degrees."""
    diff = abs(normalize_angle(angle1_deg) - normalize_angle(angle2_deg))
    return min(diff, 360 - diff)


def point_distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate 2D distance between two points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def point_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculate 3D distance between two points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def line_length_2d(start: Tuple[float, float], end: Tuple[float, float]) -> float:
    """Calculate 2D line length."""
    return point_distance_2d(start, end)


def line_angle_2d(start: Tuple[float, float], end: Tuple[float, float]) -> float:
    """Calculate angle of line in degrees (0-360)."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return normalize_angle(angle_deg)


def rotate_point_2d(point: Tuple[float, float], center: Tuple[float, float], angle_deg: float) -> Tuple[float, float]:
    """Rotate a 2D point around a center by given angle in degrees."""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Translate to origin
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    
    # Rotate
    new_x = dx * cos_a - dy * sin_a
    new_y = dx * sin_a + dy * cos_a
    
    # Translate back
    return (new_x + center[0], new_y + center[1])


def is_point_on_line_2d(point: Tuple[float, float], line_start: Tuple[float, float], 
                       line_end: Tuple[float, float], tolerance: float = 1e-6) -> bool:
    """Check if a point lies on a line segment within tolerance."""
    # Check if point is within bounding box of line
    min_x, max_x = min(line_start[0], line_end[0]), max(line_start[0], line_end[0])
    min_y, max_y = min(line_start[1], line_end[1]), max(line_start[1], line_end[1])
    
    if not (min_x - tolerance <= point[0] <= max_x + tolerance and
            min_y - tolerance <= point[1] <= max_y + tolerance):
        return False
    
    # Calculate cross product to check collinearity
    cross_product = ((point[1] - line_start[1]) * (line_end[0] - line_start[0]) - 
                    (point[0] - line_start[0]) * (line_end[1] - line_start[1]))
    
    return abs(cross_product) <= tolerance


def polygon_area_2d(points: List[Tuple[float, float]]) -> float:
    """Calculate area of a 2D polygon using shoelace formula."""
    if len(points) < 3:
        return 0.0
    
    area = 0.0
    n = len(points)
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0


def point_in_polygon_2d(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """Check if point is inside polygon using ray casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside
