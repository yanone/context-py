from typing import Optional, Union

from .Layer import Layer
from .BaseObject import BaseObject, I18NDictionary
from .Guide import Guide

# Anything which can be varied in MVAR is a master-specific metric
CORE_METRICS = [
    "xHeight",
    "capHeight",
    "ascender",
    "descender",
    "italicAngle",
    "hheaAscender",
    "hheaDescender",
    "hheaLineGap",
    "winAscent",
    "winDescent",
    "typoAscender",
    "typoDescender",
    "typoLineGap",
    "subscriptXSize",
    "subscriptYSize",
    "subscriptXOffset",
    "subscriptYOffset",
    "superscriptXSize",
    "superscriptYSize",
    "superscriptXOffset",
    "superscriptYOffset",
    "strikeoutSize",
    "strikeoutPosition",
    "underlinePosition",
    "underlineThickness",
    "hheaCaretSlopeRise",
    "hheaCaretSlopeRun",
    "hheaCaretOffset",
]


class Master(BaseObject):
    """A font master."""

    CORE_METRICS = CORE_METRICS

    def __init__(
        self,
        name=None,
        id=None,
        location=None,
        sparse=False,
        guides=None,
        metrics=None,
        kerning=None,
        font=None,
        _data=None,
        **kwargs,
    ):
        """Initialize Master with dict-backed storage."""
        if _data is not None:
            # Convert name if it's a dict
            if "name" in _data and isinstance(_data["name"], dict):
                if not isinstance(_data["name"], I18NDictionary):
                    i18n = I18NDictionary()
                    i18n.update(_data["name"])
                    _data["name"] = i18n
            # Ensure guides exists (default to empty list)
            if "guides" not in _data:
                _data["guides"] = []
            # Convert guides
            elif _data["guides"] and isinstance(_data["guides"][0], dict):
                _data["guides"] = [Guide.from_dict(g) for g in _data["guides"]]
            super().__init__(_data=_data)
        else:
            # Convert name to I18NDictionary if needed
            if isinstance(name, str):
                name = I18NDictionary.with_default(name)
            elif isinstance(name, dict) and not isinstance(name, I18NDictionary):
                i18n = I18NDictionary()
                i18n.update(name)
                name = i18n

            # Convert guides to dicts
            if guides and not isinstance(guides[0] if guides else None, dict):
                guides = [g.to_dict() if hasattr(g, "to_dict") else g for g in guides]

            data = {
                "name": name,
                "id": id,
                "location": location,
                "sparse": sparse,
                "guides": guides or [],
                "metrics": metrics or {},
                "kerning": kerning or {},
                "font": font,
            }
            data.update(kwargs)
            super().__init__(_data=data)

        # Initialize guides cache
        object.__setattr__(self, "_guides_cache", None)

    @property
    def name(self):
        name = self._data.get("name")
        if isinstance(name, dict) and not isinstance(name, I18NDictionary):
            i18n = I18NDictionary()
            i18n.update(name)
            self._data["name"] = i18n
            name = i18n
        return name

    @name.setter
    def name(self, value):
        if isinstance(value, str):
            value = I18NDictionary.with_default(value)
        self._data["name"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def id(self):
        return self._data.get("id")

    @id.setter
    def id(self, value):
        self._data["id"] = value

    @property
    def location(self):
        return self._data.get("location")

    @location.setter
    def location(self, value):
        self._data["location"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def sparse(self):
        return self._data.get("sparse", False)

    @sparse.setter
    def sparse(self, value):
        self._data["sparse"] = value

    @property
    def guides(self):
        """Return TrackedList of Guide objects. _data stores dicts."""
        from .BaseObject import TrackedList

        # Return cached list if it exists
        if self._guides_cache is not None:
            return self._guides_cache

        guides_data = self._data.get("guides", [])

        # Convert dicts to Guide objects (no deepcopy needed for _data)
        guides_objects = [Guide.from_dict(g, _copy=False) for g in guides_data]
        for guide in guides_objects:
            guide._set_parent(self)
            # Enable tracking if parent has it enabled
            if self._tracking_enabled:
                object.__setattr__(guide, "_tracking_enabled", True)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "guides", Guide)
        tracked.extend(guides_objects, mark_dirty=False)
        object.__setattr__(self, "_guides_cache", tracked)
        return tracked

    @guides.setter
    def guides(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            # Convert Guide objects to dicts (serialize for to_dict())
            dict_guides = [g.to_dict() if hasattr(g, "to_dict") else g for g in value]
            self._data["guides"] = dict_guides
        else:
            self._data["guides"] = value
        # Invalidate cache
        object.__setattr__(self, "_guides_cache", None)
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def metrics(self):
        return self._data.get("metrics", {})

    @metrics.setter
    def metrics(self, value):
        self._data["metrics"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def kerning(self):
        """
        Return kerning with tuple keys for API access.
        _data stores string keys for JSON serialization.
        Creates a new dict each time to avoid modifying _data.
        """
        kerning_data = self._data.get("kerning", {})
        if not kerning_data:
            return {}
        
        # Convert string keys to tuples for user access (DON'T modify _data)
        kerning = {}
        for k, v in kerning_data.items():
            if isinstance(k, tuple):
                # Already a tuple (shouldn't happen, but be safe)
                kerning[k] = v
            else:
                # Convert from string format "a//b" to tuple ("a", "b")
                kerning[tuple(k.split("//"))] = v
        return kerning

    @kerning.setter
    def kerning(self, value):
        # Convert kerning tuple keys to string format for JSON serialization
        if value:
            kerning = {}
            for k, v in value.items():
                # Convert tuple ("a", "b") to string "a//b"
                if isinstance(k, tuple):
                    kerning["//".join(k)] = v
                else:
                    kerning[k] = v
            self._data["kerning"] = kerning
        else:
            self._data["kerning"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def font(self):
        """Get font via weak reference (back-reference)."""
        if hasattr(self, "_font_ref") and self._font_ref:
            return self._font_ref()
        return None

    @font.setter
    def font(self, value):
        """Set font using weak reference to avoid circular references."""
        import weakref

        font_ref = weakref.ref(value) if value else None
        object.__setattr__(self, "_font_ref", font_ref)

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean using cached TrackedList."""
        # Use cached TrackedList if available to avoid creating objects
        if self._guides_cache is not None:
            for guide in self._guides_cache:
                guide.mark_clean(context, recursive=False, build_cache=build_cache)
        elif build_cache:
            # Build cache by accessing the property
            for guide in self.guides:
                guide.mark_clean(context, recursive=False, build_cache=build_cache)
        # else: If cache doesn't exist and not building, skip
        #       (object doesn't exist in memory yet)

    def get_glyph_layer(self, glyphname: str) -> Optional[Layer]:
        g = self.font.glyphs[glyphname]
        for layer in g.layers:
            if layer._master == self.id:
                return layer

    @property
    def normalized_location(self) -> dict[str, float]:
        return {a.tag: a.normalize_value(self.location[a.tag]) for a in self.font.axes}

    @property
    def xHeight(self) -> Union[int, float]:
        return self.metrics.get("xHeight", 0)

    @property
    def capHeight(self) -> Union[int, float]:
        return self.metrics.get("capHeight", 0)

    @property
    def ascender(self) -> Union[int, float]:
        return self.metrics.get("ascender", 0)

    @property
    def descender(self) -> Union[int, float]:
        return self.metrics.get("descender", 0)

    @property
    def valid(self) -> bool:
        if not self.font:
            return False
        if self.location and list(self.location.keys()) != [
            n.tag for n in self.font.axes
        ]:
            return False
        return True

    @classmethod
    def from_dict(cls, data, _copy=True):
        """Create Master from dictionary, handling guides and kerning."""
        from .Guide import Guide

        # Make a copy to avoid modifying the input data (unless loading from disk)
        if _copy:
            data = data.copy()

        # Extract guides if present
        guides_data = data.pop("guides", [])

        # Kerning keys should already be in string format "a//b" for serialization
        # The kerning getter will convert them to tuples for API access
        
        # Handle name field - convert to I18NDictionary if needed
        if "name" in data and isinstance(data["name"], dict):
            name_dict = I18NDictionary()
            name_dict.update(data["name"])
            data["name"] = name_dict
        elif "name" in data and isinstance(data["name"], str):
            data["name"] = I18NDictionary.with_default(data["name"])

        # Create master with simple fields
        master = super(Master, cls).from_dict(data)

        # Restore guides (setter converts to dicts, parent set lazily)
        master.guides = [Guide.from_dict(g, _copy=False) for g in guides_data]

        return master
