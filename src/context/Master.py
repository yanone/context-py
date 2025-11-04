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
            # Convert guides
            if "guides" in _data and _data["guides"]:
                if isinstance(_data["guides"][0], dict):
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
        guides_data = self._data.get("guides", [])
        # Convert dicts to Guide objects on first access
        if guides_data and isinstance(guides_data[0], dict):
            guides = [Guide.from_dict(g) for g in guides_data]
            for guide in guides:
                guide._set_parent(self)
            self._data["guides"] = guides
        return self._data.get("guides", [])

    @guides.setter
    def guides(self, value):
        if value and not isinstance(value[0] if value else None, dict):
            value = [g.to_dict() if hasattr(g, "to_dict") else g for g in value]
        self._data["guides"] = value
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
        return self._data.get("kerning", {})

    @kerning.setter
    def kerning(self, value):
        self._data["kerning"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def font(self):
        return self._data.get("font")

    @font.setter
    def font(self, value):
        self._data["font"] = value

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean."""
        for guide in self.guides:
            guide.mark_clean(context, recursive=False, build_cache=build_cache)

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
    def from_dict(cls, data):
        """Create Master from dictionary, handling guides and kerning."""
        from .Guide import Guide

        # Extract guides if present
        guides_data = data.pop("guides", [])

        # Handle kerning keys (convert from "a//b" to ("a", "b"))
        if "kerning" in data:
            data["kerning"] = {
                tuple(k.split("//")): v for k, v in data["kerning"].items()
            }

        # Handle name field - convert to I18NDictionary if needed
        if "name" in data and isinstance(data["name"], dict):
            name_dict = I18NDictionary()
            name_dict.update(data["name"])
            data["name"] = name_dict
        elif "name" in data and isinstance(data["name"], str):
            data["name"] = I18NDictionary.with_default(data["name"])

        # Create master with simple fields
        master = super(Master, cls).from_dict(data)

        # Restore guides
        master.guides = [Guide.from_dict(g) for g in guides_data]
        for guide in master.guides:
            guide._set_parent(master)

        return master
