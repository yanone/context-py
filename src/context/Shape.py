import math
from typing import Optional, TYPE_CHECKING

try:
    from fontTools.misc.transform import Transform
except ImportError:
    Transform = None

from .BaseObject import BaseObject
from .Node import Node

if TYPE_CHECKING:
    from .Layer import Layer


class Shape(BaseObject):
    """A shape in a glyph layer - either a path or component reference."""

    # Define validation rules for each field
    _field_types = {
        "ref": {
            "data_type": str,
        },
        "closed": {
            "data_type": bool,
        },
        "direction": {
            "data_type": int,
            "allowed_values": [-1, 1],
        },
    }

    def __init__(
        self,
        ref=None,
        transform=None,
        nodes=None,
        closed=True,
        direction=1,
        _data=None,
        **kwargs,
    ):
        """Initialize Shape with dict-backed storage."""
        if _data is not None:
            super().__init__(_data=_data)
        else:
            # Convert nodes to list of dicts if needed
            if nodes and not isinstance(nodes[0] if nodes else None, dict):
                nodes = [n.to_dict() if hasattr(n, "to_dict") else n for n in nodes]

            data = {
                "ref": ref,
                "transform": transform,
                "nodes": nodes,
                "closed": closed,
                "direction": direction,
                "_layer": None,
            }
            data.update(kwargs)
            super().__init__(_data=data)

        # Initialize nodes cache
        object.__setattr__(self, "_nodes_cache", None)

    @property
    def ref(self):
        return self._data.get("ref")

    @ref.setter
    def ref(self, value):
        self._set_field("ref", value)

    @property
    def transform(self):
        return self._data.get("transform")

    @transform.setter
    def transform(self, value):
        self._data["transform"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def nodes(self):
        """Return TrackedList of Node objects. _data stores dicts."""
        from .BaseObject import TrackedList

        nodes_data = self._data.get("nodes")
        if not nodes_data:
            return None

        # Return cached list if it exists
        if self._nodes_cache is not None:
            return self._nodes_cache

        # Convert dicts to Node objects
        nodes_objects = [Node.from_dict(n) for n in nodes_data]
        for node in nodes_objects:
            node._set_parent(self)

        # Create TrackedList and cache it
        tracked = TrackedList(self, "nodes", Node)
        tracked.extend(nodes_objects, mark_dirty=False)
        object.__setattr__(self, "_nodes_cache", tracked)
        return tracked

    @nodes.setter
    def nodes(self, value):
        """Store as dicts in _data and invalidate cache."""
        if value:
            # Convert Node objects to dicts
            dict_nodes = [n.to_dict() if hasattr(n, "to_dict") else n for n in value]
            self._data["nodes"] = dict_nodes
        else:
            self._data["nodes"] = value
        # Invalidate cache
        object.__setattr__(self, "_nodes_cache", None)
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def closed(self):
        return self._data.get("closed", True)

    @closed.setter
    def closed(self, value):
        self._set_field("closed", value)

    @property
    def direction(self):
        return self._data.get("direction", 1)

    @direction.setter
    def direction(self, value):
        self._set_field("direction", value)

    @property
    def _layer(self):
        return self._data.get("_layer")

    @_layer.setter
    def _layer(self, value):
        self._data["_layer"] = value

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean."""
        if self.nodes:
            for node in self.nodes:
                node.mark_clean(context, recursive=True, build_cache=build_cache)

    def write(self, stream, indent=0):
        """Override write to ensure nodes are Node objects."""
        # Access nodes property to trigger conversion if needed
        if self._data.get("nodes"):
            # This will convert dicts/lists to Node objects
            _ = self.nodes
        # Now call parent write() which will use Node.write()
        super().write(stream, indent)

    @property
    def _write_one_line(self):
        return self.is_component

    @property
    def is_path(self):
        return not bool(self.ref)

    @property
    def is_component(self):
        return bool(self.ref)

    @property
    def component_layer(self) -> Optional["Layer"]:
        if not self.is_component:
            return None
        return self._layer.master.get_glyph_layer(self.ref)

    @property
    def position(self):
        assert self.is_component
        if not self.transform:
            return (0, 0)
        return tuple(self.transform[4:])

    @property
    def angle(self):
        assert self.is_component
        if not self.transform:
            return 0
        return math.atan2(self.transform[1], self.transform[0]) * 180 / math.pi

    @property
    def scale(self):
        assert self.is_component
        if not self.transform:
            return (1, 1)
        scaleX = math.sqrt(self.transform[0] ** 2 + self.transform[2] ** 2)
        scaleY = math.sqrt(self.transform[1] ** 2 + self.transform[3] ** 2)
        return (scaleX, scaleY)
