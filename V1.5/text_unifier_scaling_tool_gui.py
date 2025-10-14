# File: tools/text_unifier_scaling_tool_gui.py
# Python 3.9+ (Windows), AutoCAD installed, PySide6, pywin32, PyYAML
# pip install pywin32 PySide6 pyyaml
# NOTE: For COM stability, Python 3.10–3.12 tend to be less quirky than 3.13 today.

import sys
import os
import math
import traceback
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Set

# PySide6
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QLabel, QTextEdit, QGroupBox, QFormLayout, QLineEdit, QCheckBox,
    QMessageBox, QComboBox, QListWidget, QListWidgetItem, QSplitter, QPlainTextEdit,
    QDialog, QDialogButtonBox, QGridLayout
)

# YAML (PyYAML)
try:
    import yaml
except Exception:
    yaml = None

# AutoCAD COM
try:
    import pythoncom
    from win32com.client import gencache, Dispatch, GetActiveObject
except Exception:
    gencache = None
    Dispatch = GetActiveObject = None

# ---------------------------- Geometry helpers ----------------------------

@dataclass
class BBox:
    minx: float
    miny: float
    minz: float
    maxx: float
    maxy: float
    maxz: float

    def width(self) -> float:
        return self.maxx - self.minx

    def height(self) -> float:
        return self.maxy - self.miny

    def center(self) -> Tuple[float, float, float]:
        return (
            (self.minx + self.maxx) / 2.0,
            (self.miny + self.maxy) / 2.0,
            (self.minz + self.maxz) / 2.0,
        )

    def translate(self, dx: float, dy: float) -> "BBox":
        return BBox(self.minx + dx, self.miny + dy, self.minz, self.maxx + dx, self.maxy + dy, self.maxz)

    def intersects_2d(self, other: "BBox", padding: float = 0.0) -> bool:
        return not (
            self.maxx + padding < other.minx or
            self.minx - padding > other.maxx or
            self.maxy + padding < other.miny or
            self.miny - padding > other.maxy
        )

def deg_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d

def rotate_point_about(p: Tuple[float,float], c: Tuple[float,float], ang_rad: float) -> Tuple[float,float]:
    x,y = p
    cx,cy = c
    dx,dy = x-cx, y-cy
    ca,sa = math.cos(ang_rad), math.sin(ang_rad)
    rx = dx*ca - dy*sa
    ry = dx*sa + dy*ca
    return (cx+rx, cy+ry)

# ---------------------------- AutoCAD bridge ----------------------------

class AcadBridge:
    def __init__(self, logger, dry_run: bool = False):
        self.logger = logger
        self.dry_run = dry_run
        self.acad = None
        self.doc = None
        self.preview_handles: List[str] = []
        self.preview_map: Dict[int, List[str]] = {}
        self._progid_used: Optional[str] = None

    def log(self, msg: str):
        self.logger(msg)

    def _ensure_dispatch(self, progid: str):
        try:
            return gencache.EnsureDispatch(progid)
        except Exception:
            return Dispatch(progid)

    def _try_getactive(self, progid: str):
        try:
            return GetActiveObject(progid)
        except Exception:
            return None

    def _validate_app(self, app) -> bool:
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
        if gencache is None or Dispatch is None:
            raise RuntimeError("pywin32 not installed. Install with: pip install pywin32")

        # IMPORTANT: This runs inside the worker thread.
        pythoncom.CoInitialize()

        progids = [
            "AutoCAD.Application",
            "AutoCAD.Application.28",
            "AutoCAD.Application.27",
            "AutoCAD.Application.26",
            "AutoCAD.Application.25",
            "AutoCAD.Application.24",
            "AutoCAD.Application.23",
            "AutoCAD.Application.22",
            "AutoCAD.Application.21",
            "AutoCAD.Application.20",
        ]

        app = None
        used = None

        for pid in progids:
            a = self._try_getactive(pid)
            if a and self._validate_app(a):
                app = a
                used = pid
                break

        if app is None:
            for pid in progids:
                try:
                    a = self._ensure_dispatch(pid)
                    try:
                        a.Visible = True
                    except Exception:
                        pass
                    if self._validate_app(a):
                        app = a
                        used = pid
                        break
                except Exception:
                    continue

        if app is None:
            raise RuntimeError(
                "Could not obtain AutoCAD COM Application. "
                "Ensure full AutoCAD (not LT/Core Console) is installed and bitness matches Python."
            )

        self.acad = app
        self._progid_used = used
        self.log(f"Connected to AutoCAD ({used}).")
        try:
            self.acad.Visible = True
        except Exception:
            pass
        return self.acad

    def open_dwg(self, path: str):
        if not self.acad:
            self.connect()
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            raise RuntimeError(f"DWG not found at path: {path}")
        try:
            docs = self.acad.Documents
            self.doc = docs.Open(path)
            self.log(f"Opened DWG: {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to open DWG via {self._progid_used or 'AutoCAD.Application'}: {e}")
        return self.doc

    def active_doc(self):
        if not self.acad:
            self.connect()
        try:
            self.doc = self.acad.ActiveDocument
        except Exception:
            self.doc = None
        return self.doc

    # ---------- Layers / Preview ----------

    def ensure_layer(self, name: str, color_index: Optional[int] = None, plottable: Optional[bool] = None):
        lyr = None
        for l in self.acad.ActiveDocument.Layers:
            if l.Name.lower() == name.lower():
                lyr = l
                break
        if lyr is None:
            lyr = self.acad.ActiveDocument.Layers.Add(name)
        if color_index is not None:
            try:
                lyr.Color = color_index
            except Exception:
                pass
        if plottable is not None:
            try:
                lyr.Plottable = plottable
            except Exception:
                pass
        return lyr

    def ensure_preview_layer(self):
        return self.ensure_layer("CC_PREVIEW", color_index=7, plottable=False)

    def _track(self, ent) -> None:
        try:
            self.preview_handles.append(str(ent.Handle))
        except Exception:
            pass

    def add_preview_rect(self, space_name: str, bbox: BBox, color_index: int) -> Optional[Any]:
        space = self.acad.ActiveDocument.ModelSpace if space_name == "ModelSpace" else self.acad.ActiveDocument.PaperSpace
        pts = [bbox.minx, bbox.miny, bbox.maxx, bbox.miny, bbox.maxx, bbox.maxy, bbox.minx, bbox.maxy]
        try:
            pl = space.AddLightWeightPolyline(pts)
            pl.Closed = True
            pl.Layer = "CC_PREVIEW"
            pl.Color = color_index
            try:
                pl.ConstantWidth = 0.0
            except Exception:
                pass
            self._track(pl)
            return pl
        except Exception:
            return None

    def add_preview_line(self, space_name: str, p1: Tuple[float,float], p2: Tuple[float,float], color_index: int = 2):
        space = self.acad.ActiveDocument.ModelSpace if space_name == "ModelSpace" else self.acad.ActiveDocument.PaperSpace
        try:
            ln = space.AddLine((p1[0], p1[1], 0), (p2[0], p2[1], 0))
            ln.Layer = "CC_PREVIEW"
            ln.Color = color_index
            self._track(ln)
            return ln
        except Exception:
            return None

    def add_preview_label(self, space_name: str, pt: Tuple[float,float,float], text: str, height: float = 0.1):
        space = self.acad.ActiveDocument.ModelSpace if space_name == "ModelSpace" else self.acad.ActiveDocument.PaperSpace
        try:
            tx = space.AddText(text, (pt[0], pt[1], pt[2]), height)
            tx.Layer = "CC_PREVIEW"
            tx.Color = 4
            self._track(tx)
            return tx
        except Exception:
            return None

    def clear_preview(self):
        if not self.preview_handles:
            return
        handles = set(self.preview_handles)
        self.preview_handles.clear()
        self.preview_map.clear()
        for space in (self.acad.ActiveDocument.ModelSpace, self.acad.ActiveDocument.PaperSpace):
            try:
                ents = list(space)
            except Exception:
                continue
            for e in ents:
                try:
                    h = str(e.Handle)
                    if h in handles:
                        e.Delete()
                except Exception:
                    continue
        self.log("Cleared preview graphics.")

    # ---------- Text style ----------

    def ensure_text_style(self, style_name: str = "R3P") -> None:
        st = None
        for s in self.acad.ActiveDocument.TextStyles:
            if s.Name.lower() == style_name.lower():
                st = s
                break
        if st is None:
            st = self.acad.ActiveDocument.TextStyles.Add(style_name)
            self.log(f"Created TextStyle '{style_name}'.")
        try:
            st.FontFile = style_name
            self.log(f"Set TextStyle '{style_name}' font to '{style_name}'.")
        except Exception:
            self.log("Warning: Could not assign font file. Ensure 'R3P' is installed.")
        try:
            st.Height = 0.0
        except Exception:
            pass

    # ---------- Entities / Viewports ----------

    def each_space_entities(self):
        doc = self.acad.ActiveDocument
        return [("ModelSpace", doc.ModelSpace), ("PaperSpace", doc.PaperSpace)]

    def get_viewports(self) -> List[Any]:
        vps = []
        for ent in self.acad.ActiveDocument.PaperSpace:
            try:
                if ent.ObjectName.lower().endswith("pviewport"):
                    vps.append(ent)
            except Exception:
                continue
        return vps

    def get_entity_bbox(self, ent) -> Optional[BBox]:
        try:
            mn, mx = ent.GetBoundingBox()
            return BBox(mn[0], mn[1], mn[2], mx[0], mx[1], mx[2])
        except Exception:
            return None

    def delete_entity(self, ent):
        try:
            if not self.dry_run:
                ent.Delete()
        except Exception:
            pass

    def set_mtext_mask(self, mtext, enable: bool, offset_factor: float = 1.5):
        for props in (("BackgroundFill", "UseBackgroundColor", "BackgroundScaleFactor"),
                      ("BackgroundMask", None, "MaskScaleFactor")):
            try:
                setattr(mtext, props[0], enable)
                if enable:
                    if props[1]:
                        setattr(mtext, props[1], True)
                    setattr(mtext, props[2], offset_factor)
                return
            except Exception:
                continue
        self.log("Warning: Could not set background mask on MText.")

    def nudge_clear(self, mtext, m_bbox: BBox, obstacles: List[BBox], max_steps: int = 6, step: float = 0.5) -> bool:
        directions = [(step, 0), (-step, 0), (0, step), (0, -step), (step, step), (-step, step)]
        for k in range(1, max_steps + 1):
            for dx, dy in directions:
                nx, ny = dx * k, dy * k
                try:
                    if not self.dry_run:
                        mtext.Move((0, 0, 0), (nx, ny, 0))
                    test_bbox = self.get_entity_bbox(mtext)
                    if test_bbox is None:
                        continue
                    if not any(test_bbox.intersects_2d(ob, 0.0) for ob in obstacles):
                        return True
                    if not self.dry_run:
                        mtext.Move((0, 0, 0), (-nx, -ny, 0))
                except Exception:
                    continue
        return False

    def compute_nudge_target(self, bbox: BBox, obstacles: List[BBox], base_step: float, max_steps: int) -> Optional[Tuple[float,float]]:
        directions = [(base_step, 0), (-base_step, 0), (0, base_step), (0, -base_step), (base_step, base_step), (-base_step, base_step)]
        for k in range(1, max_steps + 1):
            for dx, dy in directions:
                nx, ny = dx * k, dy * k
                tb = bbox.translate(nx, ny)
                if not any(tb.intersects_2d(ob, 0.0) for ob in obstacles):
                    return (nx, ny)
        return None

    def model_point_in_viewport(self, pt: Tuple[float,float,float], vp) -> bool:
        try:
            if not vp.Display:
                return False
            vc = vp.ViewCenter
            vh = float(vp.ViewHeight)
            vw = vh * (float(vp.Width) / float(vp.Height))
            twist = float(vp.TwistAngle)  # radians
            px, py = rotate_point_about((pt[0], pt[1]), (vc[0], vc[1]), -twist)
            in_x = (vc[0] - vw/2.0) <= px <= (vc[0] + vw/2.0)
            in_y = (vc[1] - vh/2.0) <= py <= (vc[1] + vh/2.0)
            return bool(in_x and in_y)
        except Exception:
            return False

# ---------------------------- Text analyzer ----------------------------

@dataclass
class TextItem:
    ent: Any
    bbox: BBox
    rotation_deg: float
    height: float
    inspt: Tuple[float, float, float]
    space: str
    layer: str
    text: str

@dataclass
class GroupPreview:
    idx: int
    space: str
    bbox: BBox
    collide: bool
    sample: str
    height_hint: float

class TextUnifier:
    def __init__(self, bridge: AcadBridge,
                 desired_plot_height_in: float = 0.125,
                 style_name: str = "R3P",
                 angle_tol_deg: float = 2.0,
                 gap_factor: float = 1.5,
                 nudge_factor: float = 0.2,
                 max_nudge_steps: int = 8,
                 detect_columns: bool = True,
                 column_gap_factor: float = 2.0,
                 auto_wrap_cols: int = 0):
        self.b = bridge
        self.desired_plot_height_in = desired_plot_height_in
        self.style_name = style_name
        self.angle_tol_deg = angle_tol_deg
        self.gap_factor = gap_factor
        self.nudge_factor = nudge_factor
        self.max_nudge_steps = max_nudge_steps
        self.detect_columns = detect_columns
        self.column_gap_factor = column_gap_factor
        self.auto_wrap_cols = auto_wrap_cols

        self._last_group_previews: List[GroupPreview] = []
        self._last_clusters: List[List["TextItem"]] = []
        self._included_groups: Set[int] = set()
        self._group_overrides: Dict[int, str] = {}
        self._group_lines: Dict[int, List[str]] = {}

    def set_included_groups(self, group_ids: Set[int]):
        self._included_groups = set(group_ids)

    def set_group_override(self, gid: int, content: str):
        self._group_overrides[gid] = content

    # ------ Collect & cluster ------

    def _collect_text_candidates(self) -> List[TextItem]:
        items: List[TextItem] = []
        for space_name, space in self.b.each_space_entities():
            for ent in space:
                try:
                    on = ent.ObjectName.lower()
                except Exception:
                    continue
                if on.endswith("mtext"):
                    continue
                if on.endswith("text") or on.endswith("attributedefinition") or on.endswith("attributereference"):
                    bbox = self.b.get_entity_bbox(ent)
                    if not bbox:
                        continue
                    try:
                        rot = math.degrees(getattr(ent, "Rotation", 0.0))
                    except Exception:
                        rot = 0.0
                    try:
                        h = float(getattr(ent, "Height", 0.0)) or 0.0
                    except Exception:
                        h = 0.0
                    try:
                        inspt = tuple(getattr(ent, "InsertionPoint", (bbox.minx, bbox.miny, bbox.minz)))
                    except Exception:
                        inspt = (bbox.minx, bbox.miny, bbox.minz)
                    try:
                        layer = ent.Layer
                    except Exception:
                        layer = "0"
                    try:
                        txt = str(ent.TextString).strip()
                    except Exception:
                        txt = ""
                    items.append(TextItem(ent=ent, bbox=bbox, rotation_deg=rot, height=h, inspt=inspt, space=space_name, layer=layer, text=txt))
        self.b.log(f"Found {len(items)} non-MText text entities.")
        return items

    def _cluster_lines(self, items: List[TextItem]) -> List[List[TextItem]]:
        clusters: List[List[TextItem]] = []
        used = set()
        sorted_items = sorted(enumerate(items), key=lambda t: (-t[1].bbox.maxy, t[1].bbox.minx))
        for idx, it in sorted_items:
            if idx in used:
                continue
            group = [it]
            used.add(idx)
            for jdx, jt in sorted_items:
                if jdx in used or it.space != jt.space:
                    continue
                if deg_diff(it.rotation_deg, jt.rotation_deg) > self.angle_tol_deg:
                    continue
                same_left = abs(it.bbox.minx - jt.bbox.minx) <= max(0.1, 0.2 * max(it.bbox.width(), jt.bbox.width()))
                overlap_x = not (it.bbox.maxx < jt.bbox.minx or jt.bbox.maxx < it.bbox.minx)
                ic = (jt.bbox.miny + jt.bbox.maxy)/2.0
                oc = (it.bbox.miny + it.bbox.maxy)/2.0
                vertical_gap = abs(ic - oc)
                avg_h = max(1e-6, (it.bbox.height() + jt.bbox.height()) / 2.0)
                close_y = vertical_gap <= self.gap_factor * avg_h
                if (same_left or overlap_x) and close_y:
                    group.append(jt)
                    used.add(jdx)
            group = sorted(group, key=lambda t: (-t.bbox.maxy, t.bbox.minx))
            clusters.append([g for g in group])

        if self.detect_columns:
            clusters = self._split_columns_in_clusters(clusters)

        self.b.log(f"Clustered into {len(clusters)} groups. (angle_tol={self.angle_tol_deg}°, gap_factor={self.gap_factor}, columns={'on' if self.detect_columns else 'off'})")
        return clusters

    def _split_columns_in_clusters(self, clusters: List[List[TextItem]]) -> List[List[TextItem]]:
        out: List[List[TextItem]] = []
        for group in clusters:
            out.extend(self._split_columns_recursive(group))
        return out

    def _split_columns_recursive(self, group: List[TextItem]) -> List[List[TextItem]]:
        if len(group) < 2:
            return [group]
        xs = sorted([g.bbox.minx for g in group])
        gaps = [(xs[i+1]-xs[i], i) for i in range(len(xs)-1)]
        max_gap, idx = max(gaps, key=lambda x: x[0]) if gaps else (0.0, 0)
        avg_h = sum(g.bbox.height() for g in group) / max(1, len(group))
        threshold = self.column_gap_factor * max(0.01, avg_h)
        if max_gap > threshold:
            cutoff = (xs[idx] + xs[idx+1]) / 2.0
            left = [g for g in group if g.bbox.minx <= cutoff]
            right = [g for g in group if g.bbox.minx > cutoff]
            return self._split_columns_recursive(left) + self._split_columns_recursive(right)
        return [group]

    # ------ Scale & alignment ------

    def _viewport_scale_for_point(self, pt: Tuple[float, float, float], space: str) -> float:
        if space.lower() == "paperspace":
            return 1.0
        vps = self.b.get_viewports()
        chosen = None
        for vp in vps:
            try:
                if self.b.model_point_in_viewport(pt, vp):
                    chosen = vp
                    break
            except Exception:
                continue
        if chosen is None:
            best = None
            for vp in vps:
                try:
                    if not vp.Display:
                        continue
                    cs = float(vp.CustomScale)
                except Exception:
                    continue
                if best is None or cs > best:
                    best = cs
            return best if best else 1.0
        try:
            return float(chosen.CustomScale)
        except Exception:
            return 1.0

    def _desired_height_for(self, item: TextItem) -> float:
        cs = self._viewport_scale_for_point(item.inspt, item.space)
        return self.desired_plot_height_in * cs

    def _alignment_for_group(self, group: List[TextItem]) -> int:
        lefts = [g.bbox.minx for g in group]
        rights = [g.bbox.maxx for g in group]
        l_var = (max(lefts) - min(lefts)) if len(lefts) > 1 else 0
        r_var = (max(rights) - min(rights)) if len(rights) > 1 else 0
        if l_var < r_var * 0.6:
            return 4  # MidLeft
        if r_var < l_var * 0.6:
            return 6  # MidRight
        return 5  # MidCenter

    def _collect_obstacles(self, space_name: str) -> List[BBox]:
        obs: List[BBox] = []
        space = self.b.acad.ActiveDocument.ModelSpace if space_name == "ModelSpace" else self.b.acad.ActiveDocument.PaperSpace
        for ent in space:
            try:
                on = ent.ObjectName.lower()
            except Exception:
                continue
            if on.endswith("text") or on.endswith("mtext") or "attribute" in on or (hasattr(ent, "Layer") and ent.Layer == "CC_PREVIEW"):
                continue
            bb = self.b.get_entity_bbox(ent)
            if bb:
                obs.append(bb)
        return obs

    def _group_bbox(self, group: List[TextItem]) -> BBox:
        gminx = min(t.bbox.minx for t in group)
        gminy = min(t.bbox.miny for t in group)
        gminz = min(t.bbox.minz for t in group)
        gmaxx = max(t.bbox.maxx for t in group)
        gmaxy = max(t.bbox.maxy for t in group)
        gmaxz = max(t.bbox.maxz for t in group)
        return BBox(gminx, gminy, gminz, gmaxx, gmaxy, gmaxz)

    # ------ Text building ------

    def _wrap_text(self, text: str, cols: int) -> str:
        if cols <= 0:
            return text
        out = []
        for line in text.splitlines():
            line = line.strip()
            while len(line) > cols:
                cut = line.rfind(" ", 0, cols + 1)
                if cut <= 0:
                    cut = cols
                out.append(line[:cut])
                line = line[cut:].lstrip()
            out.append(line)
        return "\n".join(out)

    def _merged_text_default(self, group: List[TextItem]) -> str:
        lines = [t.text for t in group if t.text]
        base = r"\P".join(lines)
        if self.auto_wrap_cols and self.auto_wrap_cols > 0:
            parts = [self._wrap_text(p, self.auto_wrap_cols) for p in base.split(r"\P")]
            return r"\P".join(parts)
        return base

    # ------ Preview / Resolution / Convert (unchanged functional behavior) ------

    def preview(self):
        self.b.ensure_text_style(self.style_name)
        self.b.ensure_preview_layer()
        items = self._collect_text_candidates()
        if not items:
            self.b.log("No non-MText text found.")
            self._last_group_previews = []
            self._last_clusters = []
            self._group_lines.clear()
            return

        clusters = self._cluster_lines(items)
        self._last_clusters = clusters
        self._last_group_previews = []
        self._included_groups = set()
        self._group_lines.clear()

        gid = 1
        for group in clusters:
            gbbox = self._group_bbox(group)
            space = group[0].space
            obstacles = self._collect_obstacles(space)
            collide = any(gbbox.intersects_2d(o) for o in obstacles)
            color = 1 if collide else 3
            self.b.add_preview_rect(space, gbbox, color)
            label_y = gbbox.maxy + max(0.1, gbbox.height() * 0.1)
            sample = next((g.text for g in group if g.text), "")
            text_label = f"[G{gid}] {len(group)} ln – {'COLLIDE' if collide else 'OK'} – {sample[:40]}"
            self.b.add_preview_label(space, (gbbox.minx, label_y, gbbox.minz), text_label, height=0.1)
            height_hint = self._desired_height_for(group[0])
            self._last_group_previews.append(GroupPreview(idx=gid, space=space, bbox=gbbox, collide=collide, sample=sample, height_hint=height_hint))
            self._group_lines[gid] = [t.text for t in group if t.text]
            gid += 1

        self.b.log(f"Preview ready. {len(clusters)} groups total.")

    def preview_resolution(self, strategy: str):
        if not self._last_group_previews:
            self.b.log("Run Preview Groups first.")
            return
        for handles in self.b.preview_map.values():
            for h in handles:
                for space in (self.b.acad.ActiveDocument.ModelSpace, self.b.acad.ActiveDocument.PaperSpace):
                    try:
                        for e in list(space):
                            try:
                                if str(e.Handle) == h:
                                    e.Delete()
                            except Exception:
                                continue
                    except Exception:
                        continue
        self.b.preview_map.clear()

        included = self._included_groups or {gp.idx for gp in self._last_group_previews}
        for gp in self._last_group_previews:
            if gp.idx not in included:
                continue
            if not gp.collide and strategy.lower() != "move":
                continue
            obstacles = self._collect_obstacles(gp.space)
            proposed = None
            if strategy.lower() in ("nudge", "move"):
                step = max(0.05, gp.height_hint * self.nudge_factor)
                proposed = self.b.compute_nudge_target(gp.bbox, obstacles, base_step=step, max_steps=self.max_nudge_steps)
            handles: List[str] = []
            if proposed:
                dx, dy = proposed
                nb = gp.bbox.translate(dx, dy)
                ent = self.b.add_preview_rect(gp.space, nb, color_index=2)
                if ent:
                    handles.append(str(ent.Handle))
                self.b.add_preview_line(gp.space, (gp.bbox.center()[0], gp.bbox.center()[1]), (nb.center()[0], nb.center()[1]), color_index=2)
            elif strategy.lower() == "mask":
                self.b.add_preview_label(gp.space, (gp.bbox.maxx, gp.bbox.maxy, gp.bbox.minz), "[Mask]", height=0.1)
            else:
                self.b.add_preview_label(gp.space, (gp.bbox.maxx, gp.bbox.maxy, gp.bbox.minz), "[No free spot]", height=0.1)
            self.b.preview_map[gp.idx] = handles

        self.b.log(f"Resolution preview ({strategy}) complete for included groups.")

    def convert(self, strategy: str):
        self.b.ensure_text_style(self.style_name)
        items = self._collect_text_candidates()
        if not items:
            self.b.log("No non-MText text found.")
            return
        clusters = self._cluster_lines(items)
        included = self._included_groups or set(range(1, len(clusters)+1))

        total_converted = 0
        gid = 1
        for group in clusters:
            if gid not in included:
                gid += 1
                continue

            if gid in self._group_overrides:
                content = self._group_overrides[gid]
            else:
                content = self._merged_text_default(group)
            if not content:
                gid += 1
                continue

            gbbox = self._group_bbox(group)
            inspt = gbbox.center()
            rot = group[0].rotation_deg
            height = self._desired_height_for(group[0])
            attach = self._alignment_for_group(group)
            layer = group[0].layer
            space_name = group[0].space
            space = self.b.acad.ActiveDocument.ModelSpace if space_name == "ModelSpace" else self.b.acad.ActiveDocument.PaperSpace

            try:
                if not self.dry_run:
                    mtx = space.AddMText(inspt, gbbox.width() * 1.2 + 1.0, content)
                    mtx.AttachmentPoint = attach
                    try:
                        mtx.Rotation = math.radians(rot)
                    except Exception:
                        try:
                            mtx.Rotation = rot
                        except Exception:
                            pass
                    mtx.Layer = layer
                    mtx.TextStyle = self.style_name
                    mtx.Height = height
                else:
                    mtx = None

                for t in group:
                    self.b.delete_entity(t.ent)

                if mtx is not None:
                    obstacles = self._collect_obstacles(space_name)
                    mbb = self.b.get_entity_bbox(mtx)
                    if mbb and any(mbb.intersects_2d(o) for o in obstacles):
                        st = strategy.lower()
                        if st == "nudge":
                            nudged = self.b.nudge_clear(mtx, mbb, obstacles, max_steps=self.max_nudge_steps, step=max(0.05, height * self.nudge_factor))
                            if not nudged:
                                self.b.set_mtext_mask(mtx, True, 1.5)
                        elif st == "mask":
                            self.b.set_mtext_mask(mtx, True, 1.5)
                        elif st == "move":
                            target = self.b.compute_nudge_target(mbb, obstacles, base_step=max(0.05, height * self.nudge_factor), max_steps=self.max_nudge_steps)
                            if target:
                                dx, dy = target
                                mtx.Move((0,0,0), (dx, dy, 0))
                            else:
                                self.b.set_mtext_mask(mtx, True, 1.5)
                total_converted += 1
                self.b.log(f"Converted group #{gid} with {len(group)} lines -> MText.")
            except Exception as e:
                self.b.log(f"Error creating MText for group #{gid}: {e}")
            gid += 1

        self.b.log(f"Done. Created {total_converted} MText objects.")

    # ------ Scaling Tool ------

    def scale_tool(self, factor: float, scale_text_height_only: bool = False):
        if factor <= 0:
            raise ValueError("Scale factor must be > 0.")
        base = self.b.acad.ActiveDocument.Utility.GetPoint(None, "Pick base point for scaling:\n")
        ss_name = "__CC_SS__"
        for s in list(self.b.acad.ActiveDocument.SelectionSets):
            if s.Name == ss_name:
                s.Delete()
        ss = self.b.acad.ActiveDocument.SelectionSets.Add(ss_name)
        self.b.acad.ActiveDocument.Utility.Prompt("Select objects to scale:\n")
        ss.SelectOnScreen()

        count = 0
        for i in range(ss.Count):
            ent = ss.Item(i)
            try:
                if scale_text_height_only and ent.ObjectName.lower().endswith("mtext"):
                    h = float(getattr(ent, "Height", 0.0)) or 0.0
                    if h > 0:
                        setattr(ent, "Height", h * factor)
                else:
                    ent.ScaleEntity(base, factor)
                count += 1
            except Exception:
                continue
        self.b.log(f"Scaled {count} entities by factor {factor}.")

# ---------------------------- Worker Threads ----------------------------

class Worker(QThread):
    finished = Signal()
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            tb = traceback.format_exc()
            self.failed.emit(f"{e}\n{tb}")

# ---------------------------- Edit Text Dialog ----------------------------

class EditGroupTextDialog(QDialog):
    def __init__(self, parent, groups: List[GroupPreview], get_default_text, overrides: Dict[int, str], auto_wrap_cols: int):
        super().__init__(parent)
        self.setWindowTitle("Edit Group Text")
        self.resize(720, 520)
        self.groups = groups
        self.get_default_text = get_default_text
        self.overrides = overrides
        self.auto_wrap_cols = auto_wrap_cols

        layout = QGridLayout(self)
        self.cmb = QComboBox()
        for gp in groups:
            self.cmb.addItem(f"G{gp.idx} – {gp.sample[:48]}", gp.idx)
        self.txt = QPlainTextEdit()
        self.txt.setPlaceholderText("Edit the final MText content here. Use \\P for line breaks.")
        self.lbl_hint = QLabel("Tip: Use \\P for paragraph breaks. Auto-wrap applies on convert if enabled.")

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        btns.accepted.connect(self.save_current)
        btns.rejected.connect(self.reject)

        layout.addWidget(QLabel("Group:"), 0, 0)
        layout.addWidget(self.cmb, 0, 1, 1, 3)
        layout.addWidget(self.txt, 1, 0, 1, 4)
        layout.addWidget(self.lbl_hint, 2, 0, 1, 4)
        layout.addWidget(btns, 3, 0, 1, 4)

        self.cmb.currentIndexChanged.connect(self.load_current)
        self.load_current()

    def current_gid(self) -> int:
        return int(self.cmb.currentData())

    def load_current(self):
        gid = self.current_gid()
        if gid in self.overrides:
            content = self.overrides[gid]
        else:
            content = self.get_default_text(gid)
        self.txt.setPlainText(content)

    def save_current(self):
        gid = self.current_gid()
        self.overrides[gid] = self.txt.toPlainText().strip()
        QMessageBox.information(self, "Saved", f"Saved edited text for group G{gid}.")

# ---------------------------- GUI ----------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Copilot – AutoCAD Text Unifier")
        self.resize(1400, 860)

        self.bridge: Optional[AcadBridge] = None
        self.unifier: Optional[TextUnifier] = None

        splitter = QSplitter()
        # Left
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Groups (check to include)"))
        self.list_groups = QListWidget()
        left_layout.addWidget(self.list_groups, 1)
        self.btn_edit_text = QPushButton("Edit Group Text…")
        left_layout.addWidget(self.btn_edit_text)

        # Right
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("Open DWG…")
        self.btn_preview = QPushButton("Preview Groups")
        self.btn_prev_res = QPushButton("Preview Resolution")
        self.btn_convert = QPushButton("Apply Conversion")
        self.btn_clear_preview = QPushButton("Clear Preview")
        self.btn_scale = QPushButton("Scaling Tool")
        for b in (self.btn_open, self.btn_preview, self.btn_prev_res, self.btn_convert, self.btn_clear_preview, self.btn_scale):
            btn_row.addWidget(b)
        right_layout.addLayout(btn_row)

        self.grp = QGroupBox("Settings")
        form = QFormLayout(self.grp)
        self.txt_style = QLineEdit("R3P")
        self.txt_plot_h = QLineEdit("0.125")
        self.txt_angle_tol = QLineEdit("2.0")
        self.txt_gap_factor = QLineEdit("1.5")
        self.chk_columns = QCheckBox("Detect columns (keep separate)")
        self.chk_columns.setChecked(True)
        self.txt_col_gap = QLineEdit("2.0")
        self.txt_nudge_factor = QLineEdit("0.2")
        self.txt_max_nudge = QLineEdit("8")
        self.cmb_strategy = QComboBox()
        self.cmb_strategy.addItems(["Nudge", "Mask", "Move"])
        self.txt_autowrap = QLineEdit("0")
        self.chk_dry = QCheckBox("Dry run (no changes)")
        self.btn_settings = QPushButton("Apply Settings")

        form.addRow(QLabel("Text Style:"), self.txt_style)
        form.addRow(QLabel("Plotted Text Height (inches):"), self.txt_plot_h)
        form.addRow(QLabel("Angle Tolerance (°):"), self.txt_angle_tol)
        form.addRow(QLabel("Line Gap Factor:"), self.txt_gap_factor)
        form.addRow(self.chk_columns)
        form.addRow(QLabel("Column Gap Factor:"), self.txt_col_gap)
        form.addRow(QLabel("Nudge Step Factor:"), self.txt_nudge_factor)
        form.addRow(QLabel("Max Nudge Steps:"), self.txt_max_nudge)
        form.addRow(QLabel("Collision Strategy:"), self.cmb_strategy)
        form.addRow(QLabel("Auto-wrap columns (0=off):"), self.txt_autowrap)
        form.addRow(self.chk_dry)
        form.addRow(self.btn_settings)
        right_layout.addWidget(self.grp)

        # YAML Configurator
        self.grp_yaml = QGroupBox("YAML Configurator")
        yaml_layout = QVBoxLayout(self.grp_yaml)
        self.yaml_editor = QPlainTextEdit()
        yaml_btns = QHBoxLayout()
        self.btn_yaml_from = QPushButton("From Current")
        self.btn_yaml_apply = QPushButton("Apply YAML")
        self.btn_yaml_load = QPushButton("Load YAML…")
        self.btn_yaml_save = QPushButton("Save YAML…")
        for b in (self.btn_yaml_from, self.btn_yaml_apply, self.btn_yaml_load, self.btn_yaml_save):
            yaml_btns.addWidget(b)
        yaml_layout.addWidget(self.yaml_editor, 1)
        yaml_layout.addLayout(yaml_btns)
        right_layout.addWidget(self.grp_yaml, 2)

        self.grp_scale = QGroupBox("Scaling Tool")
        form_s = QFormLayout(self.grp_scale)
        self.txt_scale_factor = QLineEdit("1.0")
        self.chk_scale_text_only = QCheckBox("Scale text heights only")
        self.btn_scale_exec = QPushButton("Run Scaling")
        form_s.addRow(QLabel("Scale Factor:"), self.txt_scale_factor)
        form_s.addRow(self.chk_scale_text_only)
        form_s.addRow(self.btn_scale_exec)
        right_layout.addWidget(self.grp_scale)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right_layout.addWidget(QLabel("Log"))
        right_layout.addWidget(self.log, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # Wire events
        self.btn_open.clicked.connect(self.on_open)
        self.btn_preview.clicked.connect(self.on_preview)
        self.btn_prev_res.clicked.connect(self.on_preview_resolution)
        self.btn_convert.clicked.connect(self.on_convert)
        self.btn_clear_preview.clicked.connect(self.on_clear_preview)
        self.btn_scale.clicked.connect(lambda: self.log_append("Use the Scaling Tool pane, then click 'Run Scaling'."))
        self.btn_settings.clicked.connect(self.on_apply_settings)
        self.btn_scale_exec.clicked.connect(self.on_run_scaling)
        self.list_groups.itemChanged.connect(self.on_group_check_changed)
        self.btn_edit_text.clicked.connect(self.on_edit_group_text)

        self.btn_yaml_from.clicked.connect(self.on_yaml_from_current)
        self.btn_yaml_apply.clicked.connect(self.on_yaml_apply)
        self.btn_yaml_load.clicked.connect(self.on_yaml_load)
        self.btn_yaml_save.clicked.connect(self.on_yaml_save)

        self.init_bridge()

    # ----- Helpers -----

    def log_append(self, msg: str):
        self.log.append(msg)
        try:
            self.log.moveCursor(QTextCursor.End)
        except Exception:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
        self.log.ensureCursorVisible()

    def init_bridge(self):
        # IMPORTANT: Do NOT connect here. Keep COM creation inside worker thread only.
        try:
            self.bridge = AcadBridge(self.log_append, dry_run=False)
            self.unifier = TextUnifier(self.bridge)
            self.log_append("Ready.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.log_append(str(e))

    def _populate_group_list(self):
        self.list_groups.blockSignals(True)
        self.list_groups.clear()
        if not self.unifier or not self.unifier._last_group_previews:
            self.list_groups.blockSignals(False)
            return
        for gp in self.unifier._last_group_previews:
            item = QListWidgetItem(f"G{gp.idx}: {gp.sample[:50] or '(no text)'}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, gp.idx)
            self.list_groups.addItem(item)
        self.list_groups.blockSignals(False)
        self._update_included_from_ui()

    def _update_included_from_ui(self):
        ids: Set[int] = set()
        for i in range(self.list_groups.count()):
            it = self.list_groups.item(i)
            if it.checkState() == Qt.Checked:
                ids.add(int(it.data(Qt.UserRole)))
        if self.unifier:
            self.unifier.set_included_groups(ids)
        self.log_append(f"Included groups: {sorted(ids)}")

    # ----- YAML support -----

    def _settings_to_dict(self) -> Dict[str, Any]:
        included = sorted(self.unifier._included_groups) if self.unifier else []
        return {
            "style": self.txt_style.text().strip(),
            "plotted_height_in": float(self.txt_plot_h.text().strip() or "0.125"),
            "angle_tolerance_deg": float(self.txt_angle_tol.text().strip() or "2.0"),
            "gap_factor": float(self.txt_gap_factor.text().strip() or "1.5"),
            "detect_columns": self.chk_columns.isChecked(),
            "column_gap_factor": float(self.txt_col_gap.text().strip() or "2.0"),
            "nudge_step_factor": float(self.txt_nudge_factor.text().strip() or "0.2"),
            "max_nudge_steps": int(self.txt_max_nudge.text().strip() or "8"),
            "collision_strategy": self.cmb_strategy.currentText(),
            "auto_wrap_cols": int(self.txt_autowrap.text().strip() or "0"),
            "dry_run": bool(self.bridge.dry_run),
            "included_groups": included,
            "group_overrides": dict(self.unifier._group_overrides) if self.unifier else {},
        }

    def _dict_to_settings(self, d: Dict[str, Any]):
        try:
            self.txt_style.setText(str(d.get("style", "R3P")))
            self.txt_plot_h.setText(str(d.get("plotted_height_in", 0.125)))
            self.txt_angle_tol.setText(str(d.get("angle_tolerance_deg", 2.0)))
            self.txt_gap_factor.setText(str(d.get("gap_factor", 1.5)))
            self.chk_columns.setChecked(bool(d.get("detect_columns", True)))
            self.txt_col_gap.setText(str(d.get("column_gap_factor", 2.0)))
            self.txt_nudge_factor.setText(str(d.get("nudge_step_factor", 0.2)))
            self.txt_max_nudge.setText(str(d.get("max_nudge_steps", 8)))
            self.cmb_strategy.setCurrentText(str(d.get("collision_strategy", "Nudge")))
            self.txt_autowrap.setText(str(d.get("auto_wrap_cols", 0)))
            self.chk_dry.setChecked(bool(d.get("dry_run", False)))

            self.on_apply_settings()
            if self.unifier:
                inc = set(int(x) for x in d.get("included_groups", []))
                self.unifier.set_included_groups(inc)
                if isinstance(d.get("group_overrides", {}), dict):
                    self.unifier._group_overrides = {int(k): str(v) for k, v in d["group_overrides"].items()}
            self.log_append("Applied settings from YAML.")
        except Exception as e:
            QMessageBox.warning(self, "YAML Apply Error", str(e))

    @Slot()
    def on_yaml_from_current(self):
        if yaml is None:
            QMessageBox.warning(self, "Missing dependency", "PyYAML not installed. pip install pyyaml")
            return
        data = self._settings_to_dict()
        try:
            self.yaml_editor.setPlainText(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
            self.log_append("Dumped current settings to YAML editor.")
        except Exception as e:
            QMessageBox.warning(self, "YAML Error", str(e))

    @Slot()
    def on_yaml_apply(self):
        if yaml is None:
            QMessageBox.warning(self, "Missing dependency", "PyYAML not installed. pip install pyyaml")
            return
        try:
            d = yaml.safe_load(self.yaml_editor.toPlainText()) or {}
            if not isinstance(d, dict):
                raise ValueError("YAML root must be a mapping.")
            self._dict_to_settings(d)
        except Exception as e:
            QMessageBox.warning(self, "YAML Parse Error", str(e))

    @Slot()
    def on_yaml_load(self):
        if yaml is None:
            QMessageBox.warning(self, "Missing dependency", "PyYAML not installed. pip install pyyaml")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load YAML", "", "YAML Files (*.yml *.yaml)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            self.yaml_editor.setPlainText(txt)
            self.on_yaml_apply()
            self.log_append(f"Loaded YAML from: {path}")
        except Exception as e:
            QMessageBox.warning(self, "YAML Load Error", str(e))

    @Slot()
    def on_yaml_save(self):
        if yaml is None:
            QMessageBox.warning(self, "Missing dependency", "PyYAML not installed. pip install pyyaml")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save YAML", "text_unifier_settings.yaml", "YAML Files (*.yml *.yaml)")
        if not path:
            return
        try:
            d = self._settings_to_dict()
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(d, f, sort_keys=False, allow_unicode=True)
            self.log_append(f"Saved YAML to: {path}")
        except Exception as e:
            QMessageBox.warning(self, "YAML Save Error", str(e))

    # ----- Events -----

    @Slot()
    def on_group_check_changed(self, _item: QListWidgetItem):
        self._update_included_from_ui()

    @Slot()
    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open DWG", "", "AutoCAD Drawing (*.dwg)")
        if not path:
            return
        def work():
            # COM created and used in this worker
            self.bridge.open_dwg(path)
        self._run_in_worker(work)

    @Slot()
    def on_apply_settings(self):
        try:
            style = self.txt_style.text().strip() or "R3P"
            h_in = float(self.txt_plot_h.text().strip())
            angle = float(self.txt_angle_tol.text().strip())
            gap = float(self.txt_gap_factor.text().strip())
            nud = float(self.txt_nudge_factor.text().strip())
            maxn = int(self.txt_max_nudge.text().strip())
            detect_cols = self.chk_columns.isChecked()
            col_gap = float(self.txt_col_gap.text().strip())
            auto_wrap = int(self.txt_autowrap.text().strip())
            self.bridge.dry_run = self.chk_dry.isChecked()

            self.unifier.desired_plot_height_in = h_in
            self.unifier.style_name = style
            self.unifier.angle_tol_deg = angle
            self.unifier.gap_factor = gap
            self.unifier.nudge_factor = nud
            self.unifier.max_nudge_steps = maxn
            self.unifier.detect_columns = detect_cols
            self.unifier.column_gap_factor = col_gap
            self.unifier.auto_wrap_cols = auto_wrap

            self.log_append(
                f"Applied settings. Style='{style}', PlotH={h_in} in, angle_tol={angle}°, "
                f"gap={gap}, columns={detect_cols}, col_gap_factor={col_gap}, "
                f"wrap_cols={auto_wrap}, nudge_factor={nud}, max_steps={maxn}, DryRun={self.bridge.dry_run}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Invalid settings", str(e))

    @Slot()
    def on_preview(self):
        def work():
            doc = self.bridge.active_doc()
            if not doc:
                raise RuntimeError("No active document.")
            self.bridge.ensure_preview_layer()
            self.unifier.preview()
        def after(_err=None):
            self._populate_group_list()
        self._run_in_worker(work, after)

    @Slot()
    def on_preview_resolution(self):
        strategy = self.cmb_strategy.currentText()
        def work():
            doc = self.bridge.active_doc()
            if not doc:
                raise RuntimeError("No active document.")
            self._update_included_from_ui()
            self.unifier.preview_resolution(strategy)
        self._run_in_worker(work)

    @Slot()
    def on_clear_preview(self):
        def work():
            doc = self.bridge.active_doc()
            if not doc:
                raise RuntimeError("No active document.")
            self.bridge.clear_preview()
        self._run_in_worker(work)

    @Slot()
    def on_convert(self):
        strategy = self.cmb_strategy.currentText()
        def work():
            doc = self.bridge.active_doc()
            if not doc:
                raise RuntimeError("No active document.")
            self._update_included_from_ui()
            self.bridge.clear_preview()
            self.unifier.convert(strategy)
        self._run_in_worker(work)

    @Slot()
    def on_run_scaling(self):
        try:
            factor = float(self.txt_scale_factor.text().strip())
            text_only = self.chk_scale_text_only.isChecked()
        except Exception:
            QMessageBox.warning(self, "Invalid input", "Scale factor must be a number.")
            return
        def work():
            doc = self.bridge.active_doc()
            if not doc:
                raise RuntimeError("No active document.")
            self.unifier.scale_tool(factor, text_only)
        self._run_in_worker(work)

    @Slot()
    def on_edit_group_text(self):
        if not self.unifier or not self.unifier._last_group_previews:
            QMessageBox.information(self, "Info", "Run Preview Groups first.")
            return

        def get_default_text(gid: int) -> str:
            for gp, grp in zip(self.unifier._last_group_previews, self.unifier._last_clusters):
                if gp.idx == gid:
                    return self.unifier._merged_text_default(grp)
            lines = self.unifier._group_lines.get(gid, [])
            base = r"\P".join(lines)
            if self.unifier.auto_wrap_cols > 0:
                parts = [self.unifier._wrap_text(p, self.unifier.auto_wrap_cols) for p in base.split(r"\P")]
                return r"\P".join(parts)
            return base

        dlg = EditGroupTextDialog(self, self.unifier._last_group_previews, get_default_text, self.unifier._group_overrides, self.unifier.auto_wrap_cols)
        dlg.exec()

    # ----- Worker helper -----

    def _run_in_worker(self, fn, after=None):
        self.setEnabled(False)
        worker = Worker(fn)
        worker.finished.connect(lambda: self._on_worker_done(None, after))
        worker.failed.connect(lambda err: self._on_worker_done(err, after))
        worker.start()
        self._worker = worker

    @Slot(object)
    def _on_worker_done(self, err, after=None):
        self.setEnabled(True)
        if err:
            self.log_append(f"Error: {err}")
        if after:
            after(err)

# ---------------------------- Entry Point ----------------------------

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
