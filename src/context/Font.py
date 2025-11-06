import functools
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from fontTools.feaLib.variableScalar import VariableScalar
    from fontTools.varLib.models import VariationModel
except ImportError:
    VariableScalar = None
    VariationModel = None

from .Axis import Axis, Tag
from .BaseObject import BaseObject, IncompatibleMastersError, Number
from .Features import Features
from .Glyph import GlyphList
from .Instance import Instance
from .Master import Master
from .Names import Names

log = logging.getLogger(__name__)


class Font(BaseObject):
    """Represents a font, with one or more masters."""

    def __init__(
        self,
        upm=1000,
        version=(1, 0),
        axes=None,
        instances=None,
        masters=None,
        glyphs=None,
        note=None,
        date=None,
        names=None,
        custom_opentype_values=None,
        filename=None,
        features=None,
        first_kern_groups=None,
        second_kern_groups=None,
        _data=None,
        **kwargs,
    ):
        """Initialize Font with dict-backed storage."""
        if _data is not None:
            # _data is passed in from from_dict() - use as-is
            # The cache properties will handle conversion as needed
            super().__init__(_data=_data)
        else:
            # Convert nested objects to dicts
            if axes and not isinstance(axes[0] if axes else None, dict):
                axes = [a._data if hasattr(a, "_data") else a for a in axes]
            if masters and not isinstance(masters[0] if masters else None, dict):
                masters = [m._data if hasattr(m, "_data") else m for m in masters]
            if instances and not isinstance(instances[0] if instances else None, dict):
                instances = [
                    i._data if hasattr(i, "_data") else i for i in instances
                ]

            data = {
                "upm": upm,
                "version": version,
                "axes": axes or [],
                "instances": instances or [],
                "masters": masters or [],
                "glyphs": glyphs or GlyphList(),
                "note": note,
                "date": date or datetime.now(),
                "names": names or Names(),
                "custom_opentype_values": custom_opentype_values or {},
                "filename": filename,
                "features": features or Features(),
                "first_kern_groups": first_kern_groups or {},
                "second_kern_groups": second_kern_groups or {},
            }
            data.update(kwargs)
            super().__init__(_data=data)

        # Set up parent reference for GlyphList dirty tracking
        self.glyphs._set_parent_font(self)
        # Set parent for names, features
        self.names._set_parent(self)
        self.features._set_parent(self)
        # Initialize callback lists
        object.__setattr__(
            self,
            "_callbacks",
            {"before_save": [], "after_save": [], "on_error": []},
        )
        # Initialize list property caches
        object.__setattr__(self, "_axes_cache", None)
        object.__setattr__(self, "_instances_cache", None)
        object.__setattr__(self, "_masters_cache", None)

    @property
    def upm(self):
        return self._data.get("upm", 1000)

    @upm.setter
    def upm(self, value):
        self._data["upm"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def version(self):
        ver = self._data.get("version", (1, 0))
        # Convert list back to tuple if needed
        if isinstance(ver, list):
            ver = tuple(ver)
            self._data["version"] = ver
        return ver

    @version.setter
    def version(self, value):
        self._data["version"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def axes(self):
        """Return TrackedList of Axis objects. _data stores dicts."""
        from .BaseObject import TrackedList

        # Return cached list if it exists
        if self._axes_cache is not None:
            # Check if cached objects need tracking enabled
            if self._tracking_enabled:
                for axis in self._axes_cache:
                    if not axis._tracking_enabled:
                        object.__setattr__(axis, "_tracking_enabled", True)
            return self._axes_cache

        axes_data = self._data.get("axes", [])

        # Convert dicts to Axis objects (no deepcopy needed for _data)
        axes_objects = [Axis.from_dict(a, _copy=False) for a in axes_data]
        for axis in axes_objects:
            # Enable tracking if parent has it enabled
            if self._tracking_enabled:
                object.__setattr__(axis, "_tracking_enabled", True)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "axes", Axis)
        tracked.extend(axes_objects, mark_dirty=False)
        object.__setattr__(self, "_axes_cache", tracked)
        return tracked

    @axes.setter
    def axes(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            dict_axes = [a._data if hasattr(a, "_data") else a for a in value]
            self._data["axes"] = dict_axes
        else:
            self._data["axes"] = value
        # Invalidate cache
        object.__setattr__(self, "_axes_cache", None)
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def instances(self):
        """Return TrackedList of Instance objects. _data stores dicts."""
        from .BaseObject import TrackedList

        # Return cached list if it exists
        if self._instances_cache is not None:
            # Check if cached objects need tracking enabled
            if self._tracking_enabled:
                for instance in self._instances_cache:
                    if not instance._tracking_enabled:
                        object.__setattr__(instance, "_tracking_enabled", True)
            return self._instances_cache

        instances_data = self._data.get("instances", [])

        # Convert dicts to Instance objects (no deepcopy needed for _data)
        instances_objects = [Instance.from_dict(i, _copy=False) for i in instances_data]
        for instance in instances_objects:
            # Enable tracking if parent has it enabled
            if self._tracking_enabled:
                object.__setattr__(instance, "_tracking_enabled", True)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "instances", Instance)
        tracked.extend(instances_objects, mark_dirty=False)
        object.__setattr__(self, "_instances_cache", tracked)
        return tracked

    @instances.setter
    def instances(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            dict_instances = [
                i._data if hasattr(i, "_data") else i for i in value
            ]
            self._data["instances"] = dict_instances
        else:
            self._data["instances"] = value
        # Invalidate cache
        object.__setattr__(self, "_instances_cache", None)
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def masters(self):
        """Return TrackedList of Master objects. _data stores dicts."""
        from .BaseObject import TrackedList

        # Return cached list if it exists
        if self._masters_cache is not None:
            # Check if cached objects need tracking enabled
            if self._tracking_enabled:
                for master in self._masters_cache:
                    if not master._tracking_enabled:
                        object.__setattr__(master, "_tracking_enabled", True)
                    # Ensure guides field exists (may be missing from loaded files)
                    if "guides" not in master._data:
                        master._data["guides"] = []
            return self._masters_cache

        masters_data = self._data.get("masters", [])

        # Convert dicts to Master objects (no deepcopy needed for _data)
        masters_objects = [Master.from_dict(m, _copy=False) for m in masters_data]

        # Set font reference on each master and enable tracking
        for master in masters_objects:
            master.font = self
            # Enable tracking if parent has it enabled
            if self._tracking_enabled:
                object.__setattr__(master, "_tracking_enabled", True)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "masters", Master)
        tracked.extend(masters_objects, mark_dirty=False)
        object.__setattr__(self, "_masters_cache", tracked)
        return tracked

    @masters.setter
    def masters(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            dict_masters = [m._data if hasattr(m, "_data") else m for m in value]
            self._data["masters"] = dict_masters
        else:
            self._data["masters"] = value
        # Invalidate cache
        object.__setattr__(self, "_masters_cache", None)
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def glyphs(self):
        glyphs = self._data.get("glyphs")
        if not glyphs:
            # No glyphs - create empty GlyphList
            glyphs = GlyphList()
            self._data["glyphs"] = glyphs
            glyphs._set_parent_font(self)
        elif isinstance(glyphs, list) and not isinstance(glyphs, GlyphList):
            # Have a plain list - convert to GlyphList
            glyph_list = GlyphList()
            glyph_list._set_parent_font(self)
            for g_data in glyphs:
                if isinstance(g_data, dict):
                    from .Glyph import Glyph

                    glyph = Glyph.from_dict(g_data)
                    glyph_list.append(glyph)
                else:
                    glyph_list.append(g_data)
            self._data["glyphs"] = glyph_list
            glyphs = glyph_list
        elif not glyphs._parent_font_ref or not glyphs._parent_font_ref():
            # GlyphList without parent - set it
            glyphs._set_parent_font(self)
        return glyphs

    @glyphs.setter
    def glyphs(self, value):
        self._data["glyphs"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def note(self):
        return self._data.get("note")

    @note.setter
    def note(self, value):
        self._data["note"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def date(self):
        return self._data.get("date", datetime.now())

    @date.setter
    def date(self, value):
        self._data["date"] = value

    @property
    def names(self):
        names_data = self._data.get("names")
        if isinstance(names_data, dict) and not isinstance(names_data, Names):
            names = Names.from_dict(names_data)
            names._set_parent(self)
            self._data["names"] = names
            return names
        return names_data or Names()

    @names.setter
    def names(self, value):
        self._data["names"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def custom_opentype_values(self):
        return self._data.get("custom_opentype_values", {})

    @custom_opentype_values.setter
    def custom_opentype_values(self, value):
        self._data["custom_opentype_values"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def filename(self):
        return self._data.get("filename")

    @filename.setter
    def filename(self, value):
        self._data["filename"] = value

    @property
    def features(self):
        features_data = self._data.get("features")
        if isinstance(features_data, dict) and not isinstance(features_data, Features):
            features = Features.from_dict(features_data)
            features._set_parent(self)
            self._data["features"] = features
            return features
        return features_data or Features()

    @features.setter
    def features(self, value):
        self._data["features"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def first_kern_groups(self):
        return self._data.get("first_kern_groups", {})

    @first_kern_groups.setter
    def first_kern_groups(self, value):
        self._data["first_kern_groups"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def second_kern_groups(self):
        return self._data.get("second_kern_groups", {})

    @second_kern_groups.setter
    def second_kern_groups(self, value):
        self._data["second_kern_groups"] = value
        if self._tracking_enabled:
            self.mark_dirty()

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

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean without creating objects."""
        # OPTIMIZATION: Don't create any objects during mark_clean!
        # All objects (glyphs, layers, shapes, etc.) will be created lazily
        # when first accessed. This makes initialization nearly instant.

        # Only mark already-instantiated objects
        for glyph_name, glyph_data in self.glyphs.items():
            if hasattr(glyph_data, "mark_clean"):
                # Already a Glyph object - mark it clean
                glyph_data.mark_clean(context, recursive=True, build_cache=build_cache)

        # Masters, axes, instances are stored as dicts - skip them
        # They'll be marked clean when converted to objects via properties

        # Clean names and features (these are always objects, not dicts)
        self.names.mark_clean(context, recursive=False, build_cache=build_cache)
        self.features.mark_clean(context, recursive=False, build_cache=build_cache)

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
                save_start = time.time()
                result = Context.save(self, convertor, **kwargs)
                save_duration = time.time() - save_start
                print(f"  ⏱️ File write time: {save_duration:.3f}s")
            finally:
                # Restore the original value
                context.BaseObject._SKIP_USER_DATA_TRACKING = old_skip_value

            # Update the stored filename after successful save
            self.filename = filename
            # Mark font clean after successful save
            # OPTIMIZATION: Only mark objects that were actually dirty,
            # rather than recursively traversing everything
            from context.BaseObject import DIRTY_FILE_SAVING

            mark_clean_start = time.time()

            # Mark font itself clean (non-recursive)
            self.mark_clean(DIRTY_FILE_SAVING, recursive=False)

            # Only mark glyphs clean if they were dirty
            # (Most glyphs are already clean after selective file writing)
            dirty_glyph_count = 0
            for glyph in self.glyphs:
                if glyph.is_dirty(DIRTY_FILE_SAVING):
                    glyph.mark_clean(DIRTY_FILE_SAVING, recursive=True)
                    dirty_glyph_count += 1

            # Mark other top-level objects clean if dirty
            for master in self.masters:
                if master.is_dirty(DIRTY_FILE_SAVING):
                    master.mark_clean(DIRTY_FILE_SAVING, recursive=True)

            for axis in self.axes:
                if axis.is_dirty(DIRTY_FILE_SAVING):
                    axis.mark_clean(DIRTY_FILE_SAVING, recursive=False)

            for instance in self.instances:
                if instance.is_dirty(DIRTY_FILE_SAVING):
                    instance.mark_clean(DIRTY_FILE_SAVING, recursive=False)

            if self.names.is_dirty(DIRTY_FILE_SAVING):
                self.names.mark_clean(DIRTY_FILE_SAVING, recursive=False)

            if self.features.is_dirty(DIRTY_FILE_SAVING):
                self.features.mark_clean(DIRTY_FILE_SAVING, recursive=False)

            mark_clean_duration = time.time() - mark_clean_start
            if dirty_glyph_count > 0:
                print(
                    f"  ⏱️ mark_clean() time: {mark_clean_duration:.3f}s ({dirty_glyph_count} glyphs)"
                )
            else:
                print(f"  ⏱️ mark_clean() time: {mark_clean_duration:.3f}s (all clean)")

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

    def write(self, stream, indent=0):
        """Override write to sync cached objects to _data before serialization."""
        # Sync masters: convert cached Master objects back to dicts
        if self._masters_cache is not None:
            self._data["masters"] = [m.to_dict() for m in self._masters_cache]

        # Sync instances: convert cached Instance objects back to dicts
        if self._instances_cache is not None:
            self._data["instances"] = [i.to_dict() for i in self._instances_cache]

        # Call parent write()
        super().write(stream, indent)

    def to_dict(self):
        """
        Convert the entire font to a dictionary representation.
        This creates a complete babelfont-compatible dictionary including
        all glyphs and their layers, suitable for serialization to JSON
        and passing to Rust/WASM.

        Returns:
            dict: A complete dictionary representation of the font
        """
        # Start with base object dictionary (top-level font properties)
        result = super().to_dict()

        # Add names dictionary
        result["names"] = self.names.to_dict()

        # Add features
        if self.features:
            result["features"] = self.features.to_dict()

        # Add glyphs with their layers
        glyphs_list = []
        for glyph in self.glyphs:
            glyph_dict = glyph.to_dict()
            # Add layers to each glyph
            if glyph.layers:
                glyph_dict["layers"] = [layer.to_dict() for layer in glyph.layers]
            glyphs_list.append(glyph_dict)

        result["glyphs"] = glyphs_list

        return result

    @classmethod
    def from_dict(cls, data, _copy=True):
        """
        Create a Font instance from a complete dictionary representation.
        This is the inverse of to_dict() and handles the full font structure
        including glyphs, layers, names, features, etc.

        Args:
            data: Complete dictionary with font data
            _copy: If True, copy data to prevent mutation. Set False when
                   loading from disk for performance.

        Returns:
            Font instance
        """
        from context import (
            Axis,
            Instance,
            Master,
            Glyph,
            Layer,
            Names,
            Features,
        )

        # Work on a copy to avoid mutating the input (unless loading from disk)
        if _copy:
            import copy

            data = copy.copy(data)  # Shallow copy is enough for top-level keys

        # Extract complex nested structures
        glyphs_data = data.pop("glyphs", [])
        names_data = data.pop("names", {})
        features_data = data.pop("features", None)
        axes_data = data.pop("axes", [])
        instances_data = data.pop("instances", [])
        masters_data = data.pop("masters", [])

        # Create font with simple fields
        font = super(Font, cls).from_dict(data)

        # Restore axes
        font.axes = [Axis.from_dict(axis_data) for axis_data in axes_data]
        for axis in font.axes:
            axis._set_parent(font)

        # Restore instances
        font.instances = [Instance.from_dict(inst_data) for inst_data in instances_data]
        for instance in font.instances:
            instance._set_parent(font)

        # Restore masters
        font.masters = [Master.from_dict(master_data) for master_data in masters_data]
        for master in font.masters:
            master.font = font
            master._set_parent(font)

        # Restore names
        font.names = Names.from_dict(names_data)
        font.names._set_parent(font)

        # Restore features
        if features_data:
            font.features = Features.from_dict(features_data)
            font.features._set_parent(font)

        # Restore glyphs with their layers
        for glyph_data in glyphs_data:
            layers_data = glyph_data.pop("layers", [])
            glyph = Glyph.from_dict(glyph_data)
            glyph._set_parent(font)

            # Restore layers
            for layer_data in layers_data:
                layer = Layer.from_dict(layer_data)
                layer._glyph = glyph
                layer._font = font
                layer._set_parent(glyph)
                glyph.layers.append(layer)

            font.glyphs.append(glyph)

        # Set up parent reference for GlyphList
        font.glyphs._set_parent_font(font)

        return font

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
