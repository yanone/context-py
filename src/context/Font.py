import functools
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.varLib.models import VariationModel

from .Axis import Axis, Tag
from .BaseObject import BaseObject, IncompatibleMastersError, Number
from .Features import Features
from .Glyph import GlyphList
from .Instance import Instance
from .Master import Master
from .Names import Names

log = logging.getLogger(__name__)


@dataclass
class _FontFields:
    upm: int = field(default=1000, metadata={"description": "The font's units per em."})
    version: Tuple[int, int] = field(
        default=(1, 0),
        metadata={
            "description": "Font version number as a tuple of integers (major, minor).",
            "json_type": "[int,int]",
        },
    )
    axes: List[Axis] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of axes, in the case of variable/multiple master font. May be empty.",
        },
    )
    instances: List[Instance] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of named/static instances.",
        },
    )
    masters: List[Master] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of the font's masters.",
        },
    )
    glyphs: GlyphList = field(
        default_factory=GlyphList,
        metadata={
            "skip_serialize": True,
            "separate_items": True,
            "json_type": "[dict]",
            "json_location": "glyphs.json",
            "description": """A list of all glyphs supported in the font.

The `GlyphList` structure in the Python object is a dictionary with array-like
properties (or you might think of it as an array with dictionary-like properties)
containing [`Glyph`](Glyph.md) objects. The `GlyphList` may be iterated
directly, and may be appended to, but may also be used to index a `Glyph` by
its name. This is generally what you want:

```Python

for g in font.glyphs:
    assert isinstance(g, Glyph)

font.glyphs.append(newglyph)

glyph_ampersand = font.glyphs["ampersand"]
```
            """,
        },
    )
    note: str = field(
        default=None,
        metadata={"description": "Any user-defined textual note about this font."},
    )
    date: datetime = field(
        default_factory=datetime.now,
        metadata={
            "description": """The font's date. When writing to Context-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.""",
            "json_type": "str",
        },
    )
    names: Names = field(default_factory=Names, metadata={"skip_serialize": True})
    custom_opentype_values: Dict[Tuple[str, str], Any] = field(
        default_factory=dict,
        metadata={
            "description": "Any values to be placed in OpenType tables on export to override defaults; these must be font-wide. Metrics which may vary by master should be placed in the `metrics` field of a Master."
        },
    )
    filename: Optional[str] = field(
        default=None,
        metadata={
            "python_only": True,
            "description": """The file path from which this font was loaded
or to which it should be saved. This is automatically set when loading
a font and used as the default path when saving.""",
        },
    )
    features: Features = field(
        default_factory=Features,
        metadata={
            "description": "A representation of the font's OpenType features",
        },
    )
    first_kern_groups: Dict[str, List[str]] = field(
        default_factory=dict,
        metadata={
            "description": "A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group."
        },
    )
    second_kern_groups: Dict[str, List[str]] = field(
        default_factory=dict,
        metadata={
            "description": "A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group."
        },
    )


@dataclass
class Font(_FontFields, BaseObject):
    """Represents a font, with one or more masters."""

    def __post_init__(self):
        super().__post_init__()
        # Set up parent reference for GlyphList dirty tracking
        # (must be done even if glyphs is empty, so appends work later)
        self.glyphs._set_parent_font(self)
        # Set parent for names, features
        self.names._set_parent(self)
        self.features._set_parent(self)
        # Initialize callback lists
        object.__setattr__(
            self, "_callbacks", {"before_save": [], "after_save": [], "on_error": []}
        )

    def initialize_dirty_tracking(self):
        """
        Enable dirty tracking for this font and all its children.
        Call this after loading a font to activate change tracking.

        Sets the font as clean for FILE_SAVING (matches disk state)
        and dirty for CANVAS_RENDER (needs initial render).

        OPTIMIZATION: Uses lazy initialization - child objects get their
        tracking flags initialized on-demand when first accessed/modified.
        This avoids traversing all 877k+ objects upfront.
        """
        from context.BaseObject import (
            BaseObject,
            DIRTY_CANVAS_RENDER,
            DIRTY_FILE_SAVING,
        )

        # Enable __setattr__ on BaseObject class (one-time operation)
        # This adds dirty tracking to ALL BaseObject instances
        BaseObject._enable_tracking_setattr()

        def enable_tracking_lazy(obj):
            """
            Initialize tracking on an object without recursing to children.
            Children will be initialized lazily when accessed.
            """
            if not hasattr(obj, "_tracking_enabled"):
                return

            # Enable tracking for this object
            object.__setattr__(obj, "_tracking_enabled", True)

            # Initialize dirty flags as empty dicts (not None)
            # This is the signal that tracking is active
            if obj._dirty_flags is None:
                object.__setattr__(obj, "_dirty_flags", {})
            if obj._dirty_fields is None:
                object.__setattr__(obj, "_dirty_fields", {})

            # LAZY: Don't convert user_data, create snapshots, or recurse!
            # Everything happens on-demand:
            # - user_data → TrackedDict: on first access (tracked_getattribute)
            # - snapshots: on first access (tracked_getattribute)
            # - child tracking: when parent marks them clean/dirty

        # Initialize tracking on Font object only (not children!)
        enable_tracking_lazy(self)
        print(f"  📍 Font tracking enabled: {self._tracking_enabled}")

        # Mark font AND children clean for FILE_SAVING
        # This recursively initializes tracking flags as needed
        # (mark_clean will call enable_tracking_lazy for each child
        # via _mark_children_clean)
        self.mark_clean(DIRTY_FILE_SAVING, recursive=True)
        print("  📍 Font marked clean for FILE_SAVING")

        # Mark font dirty for canvas render (needs initial render)
        self.mark_dirty(DIRTY_CANVAS_RENDER, propagate=False)
        print("  📍 Font marked dirty for CANVAS_RENDER")

    def _mark_children_clean(self, context):
        """Recursively mark children clean."""
        for glyph in self.glyphs:
            glyph.mark_clean(context, recursive=True)
        for master in self.masters:
            master.mark_clean(context, recursive=True)
        for axis in self.axes:
            axis.mark_clean(context, recursive=False)
        for instance in self.instances:
            instance.mark_clean(context, recursive=False)
        # Clean names and features
        self.names.mark_clean(context, recursive=False)
        self.features.mark_clean(context, recursive=False)

    def __repr__(self):
        return "<Font '%s' (%i masters)>" % (
            self.names.familyName.get_default(),
            len(self.masters),
        )

    def register_callback(self, event: str, callback):
        """Register a callback function to be called during operations.

        Args:
            event: Event name (e.g., 'before_save', 'after_save', 'on_error')
            callback: A callable that will be invoked at the specified event.
                     Signature depends on the event type.
        """
        if event not in self._callbacks:
            raise ValueError(
                f"Invalid event: {event}. Must be one of: "
                f"{', '.join(self._callbacks.keys())}"
            )
        self._callbacks[event].append(callback)

    def unregister_callback(self, event: str, callback):
        """Remove a previously registered callback.

        Args:
            event: The event type the callback was registered for
            callback: The callback function to remove
        """
        if event in self._callbacks:
            try:
                self._callbacks[event].remove(callback)
            except ValueError:
                pass  # Callback not in list, ignore

    def clear_callbacks(self, event: str = None):
        """Clear all callbacks for a specific event or all events.

        Args:
            event: Optional event type to clear. If None, clears all.
        """
        if event is None:
            for callbacks in self._callbacks.values():
                callbacks.clear()
        elif event in self._callbacks:
            self._callbacks[event].clear()

    def save(self, filename: str = None, **kwargs):
        """Save the font to a Context format file. Any additional keyword
        arguments are passed to the save method of the Context converter.

        Args:
            filename: Path to save the font. If not provided, uses the font's
                     stored filename (from where it was loaded).
        """
        import time
        from context.convertors.nfsf import Context
        from context.convertors import Convert

        # Use stored filename if no filename provided
        if filename is None:
            if self.filename is None:
                raise ValueError("No filename provided and font has no stored filename")
            filename = self.filename

        # Call before_save callbacks
        for callback in self._callbacks.get("before_save", []):
            try:
                callback(self, filename)
            except Exception as e:
                log.error(f"Error in before_save callback: {e}")

        # Perform the save operation
        start_time = time.time()
        try:
            # Disable user_data tracking during serialization for performance
            import context.BaseObject

            old_skip_value = context.BaseObject._SKIP_USER_DATA_TRACKING
            context.BaseObject._SKIP_USER_DATA_TRACKING = True

            try:
                convertor = Convert(filename)
                result = Context.save(self, convertor, **kwargs)
            finally:
                # Restore the original value
                context.BaseObject._SKIP_USER_DATA_TRACKING = old_skip_value

            # Update the stored filename after successful save
            self.filename = filename

            duration = time.time() - start_time

            # Call after_save callbacks
            for callback in self._callbacks.get("after_save", []):
                try:
                    callback(self, filename, duration)
                except Exception as e:
                    log.error(f"Error in after_save callback: {e}")

            return result

        except Exception as error:
            # Call on_error callbacks
            for callback in self._callbacks.get("on_error", []):
                try:
                    callback(self, filename, error)
                except Exception as e:
                    log.error(f"Error in on_error callback: {e}")
            # Re-raise the original error
            raise

    def master(self, mid: str) -> Optional[Master]:
        """Locates a master by its ID. Returns `None` if not found."""
        return self._master_map[mid]

    def map_forward(self, location: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from userspace to designspace."""
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_forward(location2[a.tag])
        return location2

    def map_backward(self, location: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from designspace to userspace."""
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_backward(location2[a.tag])
        return location2

    def userspace_to_designspace(self, v: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from userspace to designspace."""
        return self.map_forward(v)

    def designspace_to_userspace(self, v: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from designspace to userspace."""
        return self.map_backward(v)

    @functools.cached_property
    def default_master(self) -> Master:
        """Return the default master. If there is only one master, return it.
        If there are multiple masters, return the one with the default location.
        If there is no default location, raise an error."""
        default_loc = {a.tag: a.userspace_to_designspace(a.default) for a in self.axes}
        for m in self.masters:
            if m.location == default_loc:
                return m
        if len(self.masters) == 1:
            return self.masters[0]
        raise ValueError("Could not determine default master")

    @functools.cached_property
    def _master_map(self):
        return {m.id: m for m in self.masters}

    @functools.cached_property
    def unicode_map(self) -> Dict[int, str]:
        """Return a dictionary mapping Unicode codepoints to glyph names."""
        unicodes = {}
        for g in self.glyphs:
            for u in g.codepoints:
                if u is not None:
                    unicodes[u] = g.name
        return unicodes

    def variation_model(self) -> VariationModel:
        """Return a `fontTools.varLib.models.VariationModel` object representing
        the font's axes and masters. This is used for generating variable fonts."""
        return VariationModel(
            [m.normalized_location for m in self.masters],
            axisOrder=[a.tag for a in self.axes],
        )

    @functools.cached_property
    def _all_kerning(self):
        all_keys = [set(m.kerning.keys()) for m in self.masters]
        kerndict = {}
        for left, right in list(set().union(*all_keys)):
            kern = VariableScalar()
            kern.axes = self.axes
            for m in self.masters:
                thiskern = m.kerning.get((left, right), 0)
                if (left, right) not in m.kerning:
                    log.debug(
                        "Master %s did not define a kern pair for (%s, %s), using 0",
                        m.name.get_default(),
                        left,
                        right,
                    )
                kern.add_value(m.location, thiskern)
            kerndict[(left, right)] = kern
        return kerndict

    @functools.cached_property
    def _all_anchors(self):
        _all_anchors_dict = {}
        for g in sorted(self.glyphs.keys()):
            default_layer = self.default_master.get_glyph_layer(g)
            has_mark = None
            for a in default_layer.anchors_dict.keys():
                if a[0] == "_":
                    if has_mark:
                        log.warning(
                            "Glyph %s tried to be in two mark classes (%s, %s). The first one will win.",
                            g,
                            has_mark,
                            a,
                        )
                        continue
                    has_mark = a
                if a not in _all_anchors_dict:
                    _all_anchors_dict[a] = {}
                _all_anchors_dict[a][g] = self.get_variable_anchor(g, a)
        return _all_anchors_dict

    def get_variable_anchor(
        self, glyph, anchorname
    ) -> Tuple[VariableScalar, VariableScalar]:
        """Return a tuple of `VariableScalar` objects representing the x and y
        coordinates of the anchor on the given glyph. The `VariableScalar` objects
        are indexed by master location. If the anchor is not found on some master,
        raise an `IncompatibleMastersError`."""
        x_vs = VariableScalar()
        x_vs.axes = self.axes
        y_vs = VariableScalar()
        y_vs.axes = self.axes
        for m in self.masters:
            layer = m.get_glyph_layer(glyph)
            if anchorname not in layer.anchors_dict:
                raise IncompatibleMastersError(
                    f"Anchor {anchorname} not found on glyph {glyph} in master {m}"
                )
            anchor = m.get_glyph_layer(glyph).anchors_dict[anchorname]
            x_vs.add_value(self.map_forward(m.location), anchor.x)
            y_vs.add_value(self.map_forward(m.location), anchor.y)
        return (x_vs, y_vs)

    def exported_glyphs(self) -> List[str]:
        """Return a list of glyph names that are marked for export."""
        return [g.name for g in self.glyphs if g.exported]
