from typing import Optional, Tuple
from .BaseObject import BaseObject, I18NDictionary, Number
import uuid

try:
    from fontTools.varLib.models import normalizeValue, piecewiseLinearMap
except ImportError:
    normalizeValue = None
    piecewiseLinearMap = None


Tag = str


class Axis(BaseObject):
    """Represents an axis in a multiple master or variable font."""

    _write_one_line = True

    def __init__(
        self,
        name=None,
        tag=None,
        id=None,
        min=None,
        max=None,
        default=None,
        map=None,
        hidden=False,
        _data=None,
        **kwargs,
    ):
        """Initialize Axis with dict-backed storage."""
        if _data is not None:
            # Convert name if it's a dict
            if "name" in _data and isinstance(_data["name"], dict):
                if not isinstance(_data["name"], I18NDictionary):
                    i18n = I18NDictionary()
                    i18n.update(_data["name"])
                    _data["name"] = i18n
            super().__init__(_data=_data)
        else:
            # Convert name to I18NDictionary if needed
            if isinstance(name, str):
                name = I18NDictionary.with_default(name)
            elif isinstance(name, dict) and not isinstance(name, I18NDictionary):
                i18n = I18NDictionary()
                i18n.update(name)
                name = i18n

            data = {
                "name": name,
                "tag": tag,
                "id": id or str(uuid.uuid1()),
                "min": min,
                "max": max,
                "default": default,
                "map": map,
                "hidden": hidden,
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
            self.mark_dirty(field_name="name")

    @property
    def tag(self):
        return self._data.get("tag")

    @tag.setter
    def tag(self, value):
        self._data["tag"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="tag")

    @property
    def id(self):
        return self._data.get("id")

    @id.setter
    def id(self, value):
        self._data["id"] = value

    @property
    def min(self):
        return self._data.get("min")

    @min.setter
    def min(self, value):
        self._data["min"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="id")

    @property
    def max(self):
        return self._data.get("max")

    @max.setter
    def max(self, value):
        self._data["max"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="max")

    @property
    def default(self):
        return self._data.get("default")

    @default.setter
    def default(self, value):
        self._data["default"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="default")

    @property
    def map(self):
        return self._data.get("map")

    @map.setter
    def map(self, value):
        self._data["map"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="map")

    @property
    def hidden(self):
        return self._data.get("hidden", False)

    @hidden.setter
    def hidden(self, value):
        self._data["hidden"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="hidden")

    def normalize_value(self, value: Number) -> float:
        """Return a normalized co-ordinate (-1.0 to 1.0) for the given value.
        The value provided is expected to be in userspace coordinates."""
        return normalizeValue(
            self.userspace_to_designspace(value),
            (
                self.userspace_to_designspace(self.min),
                self.userspace_to_designspace(self.default),
                self.userspace_to_designspace(self.max),
            ),
        )

    def denormalize_value(self, value: float) -> Number:
        """Return a userspace coordinate for the given normalized value."""
        if value == 0:
            return self.default
        elif value > 0:
            return self.default + (self.max - self.default) * value
        else:
            return self.default + (self.default - self.min) * value

    # Compatibility with designspaceLib. Our names are smaller for serialization.
    @property
    def maximum(self):
        return self.max

    @property
    def minimum(self):
        return self.min

    # Compatibility with fontTools.varLib
    @property
    def maxValue(self):
        return self.max

    @property
    def minValue(self):
        return self.min

    @property
    def axisTag(self):
        return self.tag

    @property
    def defaultValue(self):
        return self.default

    @property
    def inverted_map(self) -> Optional[Tuple[float, float]]:
        """Return the axis map as a list of tuples, where the first value is the
        designspace coordinate and the second value is the userspace coordinate."""
        if not self.map:
            return None
        return [(v, k) for k, v in self.map]

    # Stolen from fontTools.designspaceLib
    def map_forward(self, v: Number) -> Number:
        """Map a location on this axis from userspace to designspace."""
        if not self.map:
            return v
        return piecewiseLinearMap(v, dict(self.map))

    def map_backward(self, v: Number) -> Number:
        """Map a location on this axis from designspace to userspace."""
        if not self.map:
            return v
        return piecewiseLinearMap(v, {v: k for k, v in self.map})

    @classmethod
    def from_dict(cls, data, _copy=True, _validate=True):
        """Create Axis from dictionary, handling name field."""
        # Handle name field - convert to I18NDictionary if needed
        if "name" in data and isinstance(data["name"], dict):
            name_dict = I18NDictionary()
            name_dict.update(data["name"])
            data["name"] = name_dict
        elif "name" in data and isinstance(data["name"], str):
            data["name"] = I18NDictionary.with_default(data["name"])

        # Create axis with fields
        return super(Axis, cls).from_dict(data, _copy=_copy, _validate=_validate)

    # These are just better names
    def userspace_to_designspace(self, v: Number) -> Number:
        """Map a location on this axis from userspace to designspace."""
        return self.map_forward(v)

    def designspace_to_userspace(self, v: Number) -> Number:
        """Map a location on this axis from designspace to userspace."""
        return self.map_backward(v)
