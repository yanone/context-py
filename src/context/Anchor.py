from .BaseObject import BaseObject


class Anchor(BaseObject):
    """An anchor point in a glyph."""

    # Define validation rules for each field
    _field_types = {
        "name": {
            "data_type": str,
        },
        "x": {
            "data_type": int,
        },
        "y": {
            "data_type": int,
        },
    }

    def __init__(self, name=None, x=0, y=0, _data=None, **kwargs):
        """Initialize Anchor with dict-backed storage."""
        if _data is not None:
            super().__init__(_data=_data)
        else:
            data = {"name": name, "x": x, "y": y}
            data.update(kwargs)
            super().__init__(_data=data)

    @property
    def name(self):
        return self._data.get("name")

    @name.setter
    def name(self, value):
        self._set_field("name", value)

    @property
    def x(self):
        return self._data.get("x", 0)

    @x.setter
    def x(self, value):
        self._set_field("x", value)

    @property
    def y(self):
        return self._data.get("y", 0)

    @y.setter
    def y(self, value):
        self._set_field("y", value)
