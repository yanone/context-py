import os

from .BaseObject import BaseObject
from .Layer import Layer

try:
    from fontTools.misc.filenames import userNameToFileName
except ImportError:
    userNameToFileName = None


class Glyph(BaseObject):
    """A glyph in a font."""

    _write_one_line = True

    def __init__(
        self,
        name=None,
        production_name=None,
        category="base",
        codepoints=None,
        layers=None,
        exported=True,
        direction="LTR",
        _data=None,
        **kwargs,
    ):
        """Initialize Glyph with dict-backed storage."""
        if _data is not None:
            # Convert layers
            if "layers" in _data and _data["layers"]:
                if isinstance(_data["layers"][0], dict):
                    _data["layers"] = [Layer.from_dict(l) for l in _data["layers"]]
            super().__init__(_data=_data)
        else:
            # Convert layers to dicts
            if layers and not isinstance(layers[0] if layers else None, dict):
                layers = [l._data if hasattr(l, "_data") else l for l in layers]

            data = {
                "name": name,
                "production_name": production_name,
                "category": category,
                "codepoints": codepoints or [],
                "layers": layers or [],
                "exported": exported,
                "direction": direction,
            }
            data.update(kwargs)
            super().__init__(_data=data)

        # Initialize layers cache
        object.__setattr__(self, "_layers_cache", None)

    @property
    def name(self):
        return self._data.get("name")

    @name.setter
    def name(self, value):
        self._data["name"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="name")

    @property
    def production_name(self):
        return self._data.get("production_name")

    @production_name.setter
    def production_name(self, value):
        self._data["production_name"] = value

    @property
    def category(self):
        return self._data.get("category", "base")

    @category.setter
    def category(self, value):
        self._data["category"] = value

    @property
    def codepoints(self):
        return self._data.get("codepoints", [])

    @codepoints.setter
    def codepoints(self, value):
        self._data["codepoints"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="production_name")

    @property
    def layers(self):
        """Return TrackedList of Layer objects. _data stores dicts."""
        from .BaseObject import TrackedList

        # Return cached list if it exists
        if self._layers_cache is not None:
            # Check if cached objects need tracking enabled
            if self._tracking_enabled:
                for layer in self._layers_cache:
                    if not layer._tracking_enabled:
                        object.__setattr__(layer, "_tracking_enabled", True)
            return self._layers_cache

        layers_data = self._data.get("layers", [])

        # Convert dicts to Layer objects (no deepcopy needed for _data)
        layers_objects = [Layer.from_dict(lyr, _copy=False) for lyr in layers_data]
        for layer in layers_objects:
            layer._set_parent(self)
            # Enable tracking if parent has it enabled
            if self._tracking_enabled:
                object.__setattr__(layer, "_tracking_enabled", True)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "layers", Layer)
        tracked.extend(layers_objects, mark_dirty=False)
        object.__setattr__(self, "_layers_cache", tracked)
        return tracked

    @layers.setter
    def layers(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            dict_layers = [
                layer._data if hasattr(layer, "_data") else layer
                for layer in value
            ]
            self._data["layers"] = dict_layers
        else:
            self._data["layers"] = value
        # Invalidate cache
        object.__setattr__(self, "_layers_cache", None)
        if self._tracking_enabled:
            self.mark_dirty(field_name="layers")

    @property
    def exported(self):
        return self._data.get("exported", True)

    @exported.setter
    def exported(self, value):
        self._data["exported"] = value

    @property
    def direction(self):
        return self._data.get("direction", "LTR")

    @direction.setter
    def direction(self, value):
        self._data["direction"] = value

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean without creating objects."""
        # Don't create Layer objects during mark_clean!
        # Use cached TrackedList if available, otherwise skip

        # If layers are cached, mark them clean
        if self._layers_cache is not None:
            for layer in self._layers_cache:
                layer.mark_clean(context, recursive=True, build_cache=build_cache)
        # Otherwise skip - layers will be marked clean when first accessed

    @property
    def babelfont_filename(self):
        return os.path.join("glyphs", (userNameToFileName(self.name) + ".nfsglyph"))


class GlyphList(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_font_ref = None

    def _set_parent_font(self, font):
        """Set the parent font for dirty tracking using weak reference."""
        import weakref

        self._parent_font_ref = weakref.ref(font) if font else None

    def __getitem__(self, key):
        """Get glyph by name, converting dict to Glyph object if needed."""
        value = super().__getitem__(key)
        if isinstance(value, dict):
            # Convert dict to Glyph object
            glyph = Glyph.from_dict(value, _copy=False)
            # Set parent font
            if self._parent_font_ref:
                font = self._parent_font_ref()
                if font:
                    glyph._set_parent(font)
                    # Enable tracking if parent has it enabled
                    if font._tracking_enabled:
                        object.__setattr__(glyph, "_tracking_enabled", True)
            # Store the converted object back
            super().__setitem__(key, glyph)
            return glyph
        elif isinstance(value, Glyph):
            # Already a Glyph object - check if tracking needs to be enabled
            if self._parent_font_ref:
                font = self._parent_font_ref()
                if font and font._tracking_enabled and not value._tracking_enabled:
                    object.__setattr__(value, "_tracking_enabled", True)
        return value

    def append(self, thing):
        # Set parent and enable tracking on new glyph
        if self._parent_font_ref:
            font = self._parent_font_ref()
            if font:
                thing._set_parent(font)
                # Enable tracking if font has it enabled
                if hasattr(font, "_tracking_enabled") and font._tracking_enabled:
                    if hasattr(thing, "_tracking_enabled"):
                        object.__setattr__(thing, "_tracking_enabled", True)
                        # Initialize dirty flags if not already set
                        if thing._dirty_flags is None:
                            object.__setattr__(thing, "_dirty_flags", {})
                        if thing._dirty_fields is None:
                            object.__setattr__(thing, "_dirty_fields", {})

        self[thing.name] = thing

        # Mark font dirty when glyph is added
        if self._parent_font_ref:
            from .BaseObject import DIRTY_FILE_SAVING, DIRTY_CANVAS_RENDER

            font = self._parent_font_ref()
            if font:
                font.mark_dirty(DIRTY_FILE_SAVING, field_name="glyphs")
                font.mark_dirty(DIRTY_CANVAS_RENDER, field_name="glyphs")

    def write(self, stream, indent):
        stream.write(b"[")
        for ix, item in enumerate(self):
            stream.write(b"\n")
            stream.write(b"  " * (indent + 2))
            item.write(stream, indent + 1)
            if ix < len(self) - 1:
                stream.write(b", ")
            else:
                stream.write(b"\n")
        stream.write(b"]")

    def __iter__(self) -> "GlyphList":
        self._n = 0
        self._values = list(self.values())
        return self

    def __next__(self) -> Glyph:
        if self._n < len(self._values):
            result = self._values[self._n]
            self._n += 1
            return result
        else:
            raise StopIteration
