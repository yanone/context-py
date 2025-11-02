from dataclasses import dataclass, field
import orjson
from .BaseObject import BaseObject

TO_PEN_TYPE = {"o": None, "c": "curve", "l": "line", "q": "qcurve"}
FROM_PEN_TYPE = {v: k for k, v in TO_PEN_TYPE.items()}


@dataclass
class _NodeFields:
    x: int = field(default=0, metadata={"description": "The x coordinate of the node."})
    y: int = field(default=0, metadata={"description": "The y coordinate of the node."})
    type: str = field(
        default="c",
        metadata={
            "description": """The node type. Valid values are:
- 'c' or 'cs': curve point (smooth)
- 'l' or 'ls': line point (smooth)
- 'q' or 'qs': quadratic curve point (smooth)
- 'o' or 'os': off-curve point (smooth)"""
        },
    )


@dataclass
class Node(BaseObject, _NodeFields):
    def write(self, stream, _indent):
        # Check if there's any format-specific data to write
        if not self._formatspecific:
            node_str = '[%i,%i,"%s"]' % (self.x, self.y, self.type)
            stream.write(node_str.encode())
        else:
            # Serialize _formatspecific as JSON string
            userdata_str = orjson.dumps(self._formatspecific).decode()
            node_str = '[%i,%i,"%s",%s]' % (self.x, self.y, self.type, userdata_str)
            stream.write(node_str.encode())

    @property
    def is_smooth(self):
        return self.type.endswith("s")

    @property
    def pen_type(self):
        return TO_PEN_TYPE[self.type[0]]
