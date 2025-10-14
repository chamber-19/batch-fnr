"""
Enhanced AutoCAD COM Bridge.

This module provides a unified interface to AutoCAD COM API, combining functionality
from both the find/replace tool and text unifier tool with improved error handling,
caching, and threading support.
"""

import logging
import os
import time
import math
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass

try:
    import pythoncom
    import win32com.client as win32
    from win32com.client import gencache, Dispatch, GetActiveObject
    import pywintypes
except ImportError:
    pythoncom = None
    win32 = None
    gencache = None
    Dispatch = GetActiveObject = None
    pywintypes = None

from .geometry import BBox

logger = logging.getLogger(__name__)


@dataclass
class TextItem:
    """Represents a text entity in AutoCAD."""
    ent: Any  # AutoCAD entity object
    text: str
    bbox: BBox
    rotation_deg: float
    layer: str
    space: str  # "ModelSpace" or "PaperSpace"
    entity_type: str  # "AcDbText", "AcDbMText", etc.


class AutoCADBridge:
    """
    Enhanced AutoCAD COM interface with unified functionality.
    
    Combines features from both tools:
    - Robust connection handling with multiple AutoCAD versions
    - Text entity processing and manipulation
    - Block reference handling with nested scanning
    - Title block and stamp management
    - Geometry operations and text clustering
    - Caching for improved performance
    """
    
    def __init__(self, logger_func: Optional[Callable[[str], None]] = None, dry_run: bool = False):
        self.logger_func = logger_func or (lambda msg: logger.info(msg))
        self.dry_run = dry_run
        
        # AutoCAD objects
        self.acad: Optional[Any] = None
        self.doc: Optional[Any] = None
        self._progid_used: Optional[str] = None
        
        # Caching
        self.blockdef_cache: Dict[str, Optional[Any]] = {}
        self.layer_cache: Dict[str, Any] = {}
        self.text_style_cache: Dict[str, Any] = {}
        
        # Preview tracking
        self.preview_handles: List[str] = []
        self.preview_map: Dict[int, List[str]] = {}
        
        # Connection state
        self._last_connection_check = 0
        self._connection_check_interval = 5.0  # seconds
    
    def log(self, message: str):
        """Log a message using the provided logger function."""
        self.logger_func(message)
    
    def _ensure_dispatch(self, progid: str):
        """Ensure COM dispatch with fallback."""
        try:
            return gencache.EnsureDispatch(progid)
        except Exception:
            return Dispatch(progid)
    
    def _try_getactive(self, progid: str):
        """Try to get active AutoCAD instance."""
        try:
            return GetActiveObject(progid)
        except Exception:
            return None
    
    def _validate_app(self, app) -> bool:
        """Validate that the AutoCAD application object is functional."""
        try:
            docs = getattr(app, "Documents", None)
            if docs is None:
                return False
            _ = docs.Count
            _ = docs.Open
            return True
        except Exception:
            return False
    
    def connect(self):
        """Connect to AutoCAD with robust version detection."""
        if not pythoncom or not win32:
            raise RuntimeError("pywin32 not installed. Install with: pip install pywin32")
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        # Try multiple AutoCAD versions
        progids = [
            "AutoCAD.Application",
            "AutoCAD.Application.28",  # AutoCAD 2024
            "AutoCAD.Application.27",  # AutoCAD 2023
            "AutoCAD.Application.26",  # AutoCAD 2022
            "AutoCAD.Application.25",  # AutoCAD 2021
            "AutoCAD.Application.24",  # AutoCAD 2020
            "AutoCAD.Application.23",  # AutoCAD 2019
            "AutoCAD.Application.22",  # AutoCAD 2018
            "AutoCAD.Application.21",  # AutoCAD 2017
            "AutoCAD.Application.20",  # AutoCAD 2016
        ]
        
        app = None
        used_progid = None
        
        # First try to get existing active instance
        for progid in progids:
            app = self._try_getactive(progid)
            if app and self._validate_app(app):
                used_progid = progid
                self.log(f"Connected to existing AutoCAD instance: {progid}")
                break
        
        # If no active instance, try to create new one
        if not app:
            for progid in progids:
                try:
                    app = self._ensure_dispatch(progid)
                    if app and self._validate_app(app):
                        used_progid = progid
                        self.log(f"Created new AutoCAD instance: {progid}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to create {progid}: {e}")
                    continue
        
        if not app:
            raise RuntimeError("Could not connect to AutoCAD. Please ensure AutoCAD is installed and running.")
        
        self.acad = app
        self._progid_used = used_progid
        
        # Make AutoCAD visible
        try:
            self.acad.Visible = True
        except Exception as e:
            logger.warning(f"Could not make AutoCAD visible: {e}")
        
        # Get active document
        try:
            self.doc = self.acad.ActiveDocument
            if self.doc:
                self.log(f"Active document: {self.doc.Name}")
        except Exception as e:
            logger.warning(f"No active document: {e}")
            self.doc = None
    
    def disconnect(self):
        """Disconnect from AutoCAD."""
        self.clear_preview()
        self.acad = None
        self.doc = None
        self._progid_used = None
        self.blockdef_cache.clear()
        self.layer_cache.clear()
        self.text_style_cache.clear()
        self.log("Disconnected from AutoCAD")
    
    def is_connected(self) -> bool:
        """Check if connected to AutoCAD."""
        current_time = time.time()
        
        # Throttle connection checks
        if current_time - self._last_connection_check < self._connection_check_interval:
            return self.acad is not None
        
        self._last_connection_check = current_time
        
        if not self.acad:
            return False
        
        try:
            # Try to access a simple property
            _ = self.acad.Name
            return True
        except Exception:
            self.acad = None
            self.doc = None
            return False
    
    def ensure_connection(self):
        """Ensure AutoCAD connection, reconnect if necessary."""
        if not self.is_connected():
            self.connect()
    
    def open_dwg(self, path: str):
        """Open a DWG file."""
        self.ensure_connection()
        
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            raise RuntimeError(f"DWG not found at path: {path}")
        
        try:
            docs = self.acad.Documents
            self.doc = docs.Open(path)
            self.log(f"Opened DWG: {path}")
            return self.doc
        except Exception as e:
            raise RuntimeError(f"Failed to open DWG: {e}")
    
    def active_doc(self):
        """Get the active document."""
        self.ensure_connection()
        
        try:
            self.doc = self.acad.ActiveDocument
            return self.doc
        except Exception:
            self.doc = None
            return None
    
    def save_doc(self):
        """Save the current document."""
        if not self.doc:
            raise RuntimeError("No active document")
        
        if not self.dry_run:
            self.doc.Save()
            time.sleep(1)
            pythoncom.PumpWaitingMessages()
            self.log("Document saved")
    
    def close_doc(self):
        """Close the current document."""
        if self.doc:
            self.doc.Close()
            time.sleep(1)
            pythoncom.PumpWaitingMessages()
            self.doc = None
            self.log("Document closed")
    
    def _is_e_fail(self, err: Exception) -> bool:
        """Check if error is E_FAIL (common benign COM error)."""
        if not pywintypes:
            return False
        return (isinstance(err, pywintypes.com_error) and 
                getattr(err, "hresult", None) == -2147467259)
    
    def _is_xref_block_name(self, name: str) -> bool:
        """Check if block name indicates an xref."""
        if not name:
            return False
        name_upper = str(name).upper()
        return ('|' in name_upper) or name_upper.startswith('*X')
    
    def get_block_definition(self, block_name: str):
        """Get block definition with caching."""
        if not self.doc:
            return None
        
        key = block_name or ""
        if key in self.blockdef_cache:
            return self.blockdef_cache[key]
        
        if self._is_xref_block_name(key):
            self.blockdef_cache[key] = None
            return None
        
        try:
            block_def = self.doc.Blocks.Item(block_name)
            
            # Check if block is xref-derived
            for flag in ("IsXRef", "IsXRefDependent", "IsFromExternalReference"):
                try:
                    if bool(getattr(block_def, flag)):
                        self.blockdef_cache[key] = None
                        return None
                except Exception:
                    pass
            
            self.blockdef_cache[key] = block_def
            return block_def
            
        except Exception:
            self.blockdef_cache[key] = None
            return None
    
    def ensure_layer(self, layer_name: str):
        """Ensure layer exists, create if necessary."""
        if not self.doc:
            return None
        
        if layer_name in self.layer_cache:
            return self.layer_cache[layer_name]
        
        try:
            layer = self.doc.Layers.Item(layer_name)
            self.layer_cache[layer_name] = layer
            return layer
        except Exception:
            # Layer doesn't exist, create it
            try:
                if not self.dry_run:
                    layer = self.doc.Layers.Add(layer_name)
                    self.layer_cache[layer_name] = layer
                    self.log(f"Created layer: {layer_name}")
                    return layer
            except Exception as e:
                logger.error(f"Failed to create layer {layer_name}: {e}")
                return None
    
    def ensure_text_style(self, style_name: str):
        """Ensure text style exists."""
        if not self.doc:
            return None
        
        if style_name in self.text_style_cache:
            return self.text_style_cache[style_name]
        
        try:
            style = self.doc.TextStyles.Item(style_name)
            self.text_style_cache[style_name] = style
            return style
        except Exception:
            # Style doesn't exist, create basic one
            try:
                if not self.dry_run:
                    style = self.doc.TextStyles.Add(style_name)
                    self.text_style_cache[style_name] = style
                    self.log(f"Created text style: {style_name}")
                    return style
            except Exception as e:
                logger.error(f"Failed to create text style {style_name}: {e}")
                return None
    
    def ensure_preview_layer(self):
        """Ensure preview layer exists for temporary objects."""
        return self.ensure_layer("PREVIEW_TEMP")
    
    def clear_preview(self):
        """Clear all preview objects."""
        if not self.doc or not self.preview_handles:
            return
        
        cleared_count = 0
        for handle in self.preview_handles:
            try:
                if not self.dry_run:
                    obj = self.doc.HandleToObject(handle)
                    obj.Delete()
                    cleared_count += 1
            except Exception:
                pass  # Object may already be deleted
        
        self.preview_handles.clear()
        self.preview_map.clear()
        
        if cleared_count > 0:
            self.log(f"Cleared {cleared_count} preview objects")
    
    def delete_entity(self, entity):
        """Delete an entity."""
        if not self.dry_run:
            try:
                entity.Delete()
            except Exception as e:
                logger.warning(f"Failed to delete entity: {e}")
    
    def pump_messages(self):
        """Pump COM messages to prevent AutoCAD from becoming unresponsive."""
        if pythoncom:
            pythoncom.PumpWaitingMessages()
    
    def get_entity_text(self, entity) -> Optional[str]:
        """Extract text from various entity types."""
        try:
            entity_type = entity.EntityName
            
            if entity_type == "AcDbText":
                return entity.TextString
            elif entity_type == "AcDbMText":
                try:
                    return entity.Text
                except Exception:
                    return getattr(entity, "Contents", "")
            elif entity_type.startswith("AcDbDimension"):
                return getattr(entity, "TextOverride", "") or ""
            elif entity_type == "AcDbMLeader" and hasattr(entity, "MTextContent"):
                return entity.MTextContent
            
        except Exception as e:
            if not self._is_e_fail(e):
                logger.debug(f"Failed to get text from entity: {e}")
        
        return None
    
    def set_entity_text(self, entity, text: str):
        """Set text for various entity types."""
        if self.dry_run:
            return
        
        try:
            entity_type = entity.EntityName
            
            if entity_type == "AcDbText":
                entity.TextString = text
            elif entity_type == "AcDbMText":
                try:
                    entity.Text = text
                except Exception:
                    entity.Contents = text
            elif entity_type == "AcDbMLeader" and hasattr(entity, "MTextContent"):
                entity.MTextContent = text
            elif entity_type.startswith("AcDbDimension"):
                entity.TextOverride = text
                
        except Exception as e:
            logger.warning(f"Failed to set entity text: {e}")
    
    def get_entity_bbox(self, entity) -> Optional[BBox]:
        """Get bounding box of an entity."""
        try:
            bounds = entity.GetBoundingBox()
            if len(bounds) >= 2:
                min_pt, max_pt = bounds[0], bounds[1]
                return BBox(
                    minx=min_pt[0], miny=min_pt[1], minz=min_pt[2] if len(min_pt) > 2 else 0,
                    maxx=max_pt[0], maxy=max_pt[1], maxz=max_pt[2] if len(max_pt) > 2 else 0
                )
        except Exception as e:
            if not self._is_e_fail(e):
                logger.debug(f"Failed to get entity bbox: {e}")

        return None

    def collect_text_entities(self, spaces: Optional[List[str]] = None) -> List[TextItem]:
        """
        Collect all text entities from specified spaces.

        Args:
            spaces: List of space names ("ModelSpace", "PaperSpace") or None for both

        Returns:
            List of TextItem objects
        """
        if not self.doc:
            return []

        if spaces is None:
            spaces = ["ModelSpace", "PaperSpace"]

        text_items = []

        for space_name in spaces:
            try:
                if space_name == "ModelSpace":
                    space = self.doc.ModelSpace
                elif space_name == "PaperSpace":
                    space = self.doc.PaperSpace
                else:
                    continue

                for entity in space:
                    text_item = self._entity_to_text_item(entity, space_name)
                    if text_item:
                        text_items.append(text_item)

                    # Also check block references for nested text
                    if hasattr(entity, 'EntityName') and entity.EntityName == "AcDbBlockReference":
                        nested_items = self._collect_text_from_block_ref(entity, space_name)
                        text_items.extend(nested_items)

            except Exception as e:
                logger.error(f"Error collecting text from {space_name}: {e}")

        return text_items

    def _entity_to_text_item(self, entity, space_name: str) -> Optional[TextItem]:
        """Convert an entity to a TextItem if it contains text."""
        try:
            entity_type = entity.EntityName
            text = self.get_entity_text(entity)

            if not text:
                return None

            bbox = self.get_entity_bbox(entity)
            if not bbox:
                return None

            # Get rotation
            rotation_deg = 0.0
            try:
                if hasattr(entity, 'Rotation'):
                    rotation_deg = math.degrees(entity.Rotation)
            except Exception:
                pass

            # Get layer
            layer = "0"
            try:
                layer = entity.Layer
            except Exception:
                pass

            return TextItem(
                ent=entity,
                text=text,
                bbox=bbox,
                rotation_deg=rotation_deg,
                layer=layer,
                space=space_name,
                entity_type=entity_type
            )

        except Exception as e:
            if not self._is_e_fail(e):
                logger.debug(f"Failed to convert entity to TextItem: {e}")
            return None

    def _collect_text_from_block_ref(self, block_ref, space_name: str, depth: int = 0, max_depth: int = 3) -> List[TextItem]:
        """Collect text entities from within a block reference."""
        if depth >= max_depth:
            return []

        text_items = []

        try:
            if getattr(block_ref, "IsXRef", False):
                return text_items

            block_name = getattr(block_ref, "EffectiveName", None) or getattr(block_ref, "Name", None)
            if not block_name or self._is_xref_block_name(block_name):
                return text_items

            block_def = self.get_block_definition(block_name)
            if not block_def:
                return text_items

            for entity in block_def:
                try:
                    text_item = self._entity_to_text_item(entity, space_name)
                    if text_item:
                        text_items.append(text_item)

                    # Recursively check nested blocks
                    if hasattr(entity, 'EntityName') and entity.EntityName == "AcDbBlockReference":
                        nested_items = self._collect_text_from_block_ref(entity, space_name, depth + 1, max_depth)
                        text_items.extend(nested_items)

                except Exception as e:
                    if not self._is_e_fail(e):
                        logger.debug(f"Error processing nested entity: {e}")
                    continue

        except Exception as e:
            if not self._is_e_fail(e):
                logger.debug(f"Error collecting text from block reference: {e}")

        return text_items

    def process_block_attributes(self, block_ref, processor_func) -> bool:
        """
        Process attributes of a block reference.

        Args:
            block_ref: Block reference entity
            processor_func: Function to process each attribute (attr, tag, value) -> new_value or None

        Returns:
            True if any attributes were modified
        """
        if not hasattr(block_ref, 'HasAttributes') or not block_ref.HasAttributes:
            return False

        changed = False

        try:
            for attr in block_ref.GetAttributes():
                tag = getattr(attr, "TagString", "").upper().strip()
                original_value = attr.TextString

                new_value = processor_func(attr, tag, original_value)

                if new_value is not None and new_value != original_value:
                    if not self.dry_run:
                        attr.TextString = new_value
                    changed = True

        except Exception as e:
            logger.error(f"Error processing block attributes: {e}")

        return changed

    def apply_stamp_layers(self, issue_type: str) -> bool:
        """
        Apply stamp by freezing/thawing issue layers.

        Args:
            issue_type: Type of issue (APPROVAL, PRELIM, CONSTRUCTION, etc.)

        Returns:
            True if any layers were modified
        """
        if not self.doc:
            return False

        layer_map = {
            "APPROVAL": "ISSUE-APPROVAL",
            "AS-BUILT": "ISSUE-AS-BUILT",
            "BID": "ISSUE-BID",
            "CONSTRUCTION": "ISSUE-CONSTRUCTION",
            "PRELIM": "ISSUE-PRELIM",
            "REFERENCE": "ISSUE-REFERENCE",
        }

        target_layer = layer_map.get(issue_type.upper())
        if not target_layer:
            return False

        # Find all ISSUE-* layers
        issue_layers = []
        try:
            for layer in self.doc.Layers:
                layer_name = layer.Name
                if layer_name.upper().startswith("ISSUE-"):
                    issue_layers.append(layer_name)
        except Exception as e:
            logger.error(f"Failed to enumerate layers: {e}")
            return False

        if not issue_layers:
            self.log("No ISSUE-* layers found")
            return False

        changed = False

        # Freeze all issue layers except target
        for layer_name in issue_layers:
            try:
                layer = self.doc.Layers.Item(layer_name)
                should_freeze = (layer_name.upper() != target_layer.upper())

                if bool(layer.Freeze) != should_freeze:
                    if not self.dry_run:
                        layer.Freeze = should_freeze

                    action = "Froze" if should_freeze else "Thawed"
                    self.log(f"Stamp: {action} layer {layer_name}")
                    changed = True

            except Exception as e:
                logger.error(f"Failed to update layer {layer_name}: {e}")

        # Ensure target layer is on
        try:
            target_layer_obj = self.doc.Layers.Item(target_layer)
            if not target_layer_obj.LayerOn and not self.dry_run:
                target_layer_obj.LayerOn = True
        except Exception:
            pass

        return changed
