from .BaseObject import BaseObject, Color, Position


class Guide(BaseObject):
    """A guide line in a glyph or master."""

    # Map Python field names to their serialized names in files
    _field_aliases = {"position": "pos"}

    def __init__(self, position=None, name=None, color=None, _data=None, **kwargs):
        """Initialize Guide with dict-backed storage."""
        if _data is not None:
            super().__init__(_data=_data)
        else:
            # Convert Position/Color to dict if needed
            if isinstance(position, Position):
                position = {
                    "x": position.x,
                    "y": position.y,
                    "angle": position.angle,
                }
            elif isinstance(position, (list, tuple)):
                angle = position[2] if len(position) > 2 else 0
                position = {"x": position[0], "y": position[1], "angle": angle}

            if isinstance(color, Color):
                color = {
                    "r": color.r,
                    "g": color.g,
                    "b": color.b,
                    "a": color.a,
                }
            elif isinstance(color, (list, tuple)) and color:
                a = color[3] if len(color) > 3 else 0
                color = {"r": color[0], "g": color[1], "b": color[2], "a": a}

            data = {"position": position, "name": name, "color": color}
            data.update(kwargs)
            super().__init__(_data=data)

    @property
    def position(self):
        pos = self._data.get("position")
        if pos:
            if isinstance(pos, dict):
                return Position(**pos)
            elif isinstance(pos, (list, tuple)):
                # From JSON: [x, y, angle]
                angle = pos[2] if len(pos) > 2 else 0
                return Position(pos[0], pos[1], angle)
        return pos

    @position.setter
    def position(self, value):
        if isinstance(value, Position):
            value = {"x": value.x, "y": value.y, "angle": value.angle}
        elif isinstance(value, (list, tuple)):
            angle = value[2] if len(value) > 2 else 0
            value = {"x": value[0], "y": value[1], "angle": angle}
        self._data["position"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def name(self):
        return self._data.get("name")

    @name.setter
    def name(self, value):
        self._data["name"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def color(self):
        col = self._data.get("color")
        if col:
            if isinstance(col, dict):
                return Color(**col)
            elif isinstance(col, (list, tuple)):
                # From JSON: [r, g, b, a]
                a = col[3] if len(col) > 3 else 0
                return Color(col[0], col[1], col[2], a)
        return col

    @color.setter
    def color(self, value):
        if isinstance(value, Color):
            value = {"r": value.r, "g": value.g, "b": value.b, "a": value.a}
        elif isinstance(value, (list, tuple)) and value:
            a = value[3] if len(value) > 3 else 0
            value = {"r": value[0], "g": value[1], "b": value[2], "a": a}
        self._data["color"] = value
        if self._tracking_enabled:
            self.mark_dirty()
