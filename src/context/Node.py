import orjson
from .BaseObject import BaseObject

TO_PEN_TYPE = {"o": None, "c": "curve", "l": "line", "q": "qcurve"}
FROM_PEN_TYPE = {v: k for k, v in TO_PEN_TYPE.items()}


class Node(BaseObject):
    """
    A node in a glyph outline path.

    Data is stored in self._data dict. Properties provide access to fields.
    """

    def __init__(self, x=0, y=0, type="c", _data=None, **kwargs):
        """Initialize Node with dict-backed storage."""
        if _data is not None:
            # from_dict path: use provided dict directly
            super().__init__(_data=_data)
        else:
            # Normal construction: build dict from parameters
            data = {"x": x, "y": y, "type": type}
            data.update(kwargs)
            super().__init__(_data=data)

    @property
    def x(self):
        """The x coordinate of the node."""
        return self._data.get("x", 0)

    @x.setter
    def x(self, value):
        self._data["x"] = value
        self.mark_dirty()

    @property
    def y(self):
        """The y coordinate of the node."""
        return self._data.get("y", 0)

    @y.setter
    def y(self, value):
        self._data["y"] = value
        self.mark_dirty()

    @property
    def type(self):
        """The node type (c/l/q/o with optional 's' suffix for smooth)."""
        return self._data.get("type", "c")

    @type.setter
    def type(self, value):
        self._data["type"] = value
        self.mark_dirty()

    def write(self, stream, _indent):
        # Check if there's any user data to write
        if not self.user_data:
            node_str = '[%i,%i,"%s"]' % (self.x, self.y, self.type)
            stream.write(node_str.encode())
        else:
            # Serialize user_data as JSON string with sorted keys
            # OPT_NON_STR_KEYS: Allow non-string dict keys
            userdata_str = orjson.dumps(
                self.user_data,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
            ).decode()
            node_str = '[%i,%i,"%s",%s]' % (
                self.x,
                self.y,
                self.type,
                userdata_str,
            )
            stream.write(node_str.encode())

    @property
    def is_smooth(self):
        return self.type.endswith("s")

    @property
    def pen_type(self):
        return TO_PEN_TYPE[self.type[0]]
