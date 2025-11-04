import uuid
import weakref
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Optional

try:
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.ufoLib.pointPen import (
        AbstractPointPen,
        PointToSegmentPen,
        SegmentToPointPen,
    )
except ImportError:
    BoundsPen = None
    DecomposingRecordingPen = None
    AbstractPointPen = object
    PointToSegmentPen = None
    SegmentToPointPen = None

from .Anchor import Anchor
from .BaseObject import BaseObject, Color
from .Guide import Guide
from .Node import Node, FROM_PEN_TYPE
from .Shape import Shape

if TYPE_CHECKING:
    from .Font import Font
    from .Glyph import Glyph


class Layer(BaseObject):
    """A layer in a glyph with shapes, anchors, and guides."""

    def __init__(
        self,
        width=0,
        height=0,
        vertWidth=None,
        name=None,
        _master=None,
        id=None,
        guides=None,
        shapes=None,
        anchors=None,
        color=None,
        layerIndex=0,
        background=None,
        isBackground=False,
        location=None,
        _data=None,
        **kwargs,
    ):
        """Initialize Layer with dict-backed storage."""
        if _data is not None:
            super().__init__(_data=_data)
        else:
            # Convert nested objects to dicts
            if shapes and not isinstance(shapes[0] if shapes else None, dict):
                shapes = [s.to_dict() if hasattr(s, "to_dict") else s for s in shapes]
            if anchors and not isinstance(anchors[0] if anchors else None, dict):
                anchors = [a.to_dict() if hasattr(a, "to_dict") else a for a in anchors]
            if guides and not isinstance(guides[0] if guides else None, dict):
                guides = [g.to_dict() if hasattr(g, "to_dict") else g for g in guides]

            data = {
                "width": width,
                "height": height,
                "vertWidth": vertWidth,
                "name": name,
                "_master": _master,
                "id": id or str(uuid.uuid1()),
                "guides": guides or [],
                "shapes": shapes or [],
                "anchors": anchors or [],
                "color": color,
                "layerIndex": layerIndex,
                "background": background,
                "isBackground": isBackground,
                "location": location,
            }
            data.update(kwargs)
            super().__init__(_data=data)

        # Initialize weak reference holders
        if not hasattr(self, "_font_ref"):
            object.__setattr__(self, "_font_ref", None)
        if not hasattr(self, "_glyph_ref"):
            object.__setattr__(self, "_glyph_ref", None)

    @property
    def width(self):
        return self._data.get("width", 0)

    @width.setter
    def width(self, value):
        old_value = self._data.get("width", 0)
        if old_value != value:
            self._data["width"] = value
            if self._tracking_enabled:
                self.mark_dirty()
        else:
            self._data["width"] = value

    @property
    def height(self):
        return self._data.get("height", 0)

    @height.setter
    def height(self, value):
        self._data["height"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def vertWidth(self):
        return self._data.get("vertWidth")

    @vertWidth.setter
    def vertWidth(self, value):
        self._data["vertWidth"] = value
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
    def _master(self):
        return self._data.get("_master")

    @_master.setter
    def _master(self, value):
        self._data["_master"] = value

    @property
    def id(self):
        return self._data.get("id")

    @id.setter
    def id(self, value):
        self._data["id"] = value

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
    def shapes(self):
        shapes_data = self._data.get("shapes", [])
        # Convert dicts to Shape objects on first access
        if shapes_data and isinstance(shapes_data[0], dict):
            shapes = [Shape.from_dict(s) for s in shapes_data]
            for shape in shapes:
                shape._set_parent(self)
            self._data["shapes"] = shapes
        return self._data.get("shapes", [])

    @shapes.setter
    def shapes(self, value):
        # Store Shape objects directly (don't convert to dicts)
        # This ensures Shape.write() method is used during serialization
        if value:
            # Convert dicts to Shape objects if needed
            if not isinstance(value[0], Shape):
                value = [Shape.from_dict(s) for s in value]
            # Set parent for all shapes
            for shape in value:
                if hasattr(shape, '_set_parent'):
                    shape._set_parent(self)
        self._data["shapes"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def anchors(self):
        anchors_data = self._data.get("anchors", [])
        # Convert dicts to Anchor objects on first access
        if anchors_data and isinstance(anchors_data[0], dict):
            anchors = [Anchor.from_dict(a) for a in anchors_data]
            for anchor in anchors:
                anchor._set_parent(self)
            self._data["anchors"] = anchors
        return self._data.get("anchors", [])

    @anchors.setter
    def anchors(self, value):
        if value and not isinstance(value[0] if value else None, dict):
            value = [a.to_dict() if hasattr(a, "to_dict") else a for a in value]
        self._data["anchors"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def color(self):
        return self._data.get("color")

    @color.setter
    def color(self, value):
        self._data["color"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def layerIndex(self):
        return self._data.get("layerIndex", 0)

    @layerIndex.setter
    def layerIndex(self, value):
        self._data["layerIndex"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def background(self):
        return self._data.get("background")

    @background.setter
    def background(self, value):
        self._data["background"] = value

    @property
    def isBackground(self):
        return self._data.get("isBackground", False)

    @isBackground.setter
    def isBackground(self, value):
        self._data["isBackground"] = value

    @property
    def location(self):
        return self._data.get("location")

    @location.setter
    def location(self, value):
        self._data["location"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def _font(self):
        """Get font via weak reference."""
        if self._font_ref:
            return self._font_ref()
        return None

    @_font.setter
    def _font(self, font):
        """Set font using weak reference to avoid circular references."""
        font_ref = weakref.ref(font) if font else None
        object.__setattr__(self, "_font_ref", font_ref)

    @property
    def _glyph(self):
        """Get glyph via weak reference."""
        if self._glyph_ref:
            return self._glyph_ref()
        return None

    @_glyph.setter
    def _glyph(self, glyph):
        """Set glyph using weak reference to avoid circular references."""
        glyph_ref = weakref.ref(glyph) if glyph else None
        object.__setattr__(self, "_glyph_ref", glyph_ref)

    def _mark_children_clean(self, context, build_cache=False):
        """Recursively mark children clean."""
        for shape in self.shapes:
            shape.mark_clean(context, recursive=True, build_cache=build_cache)
        for anchor in self.anchors:
            anchor.mark_clean(
                context, recursive=False, build_cache=build_cache
            )
        for guide in self.guides:
            guide.mark_clean(
                context, recursive=False, build_cache=build_cache
            )

    def write(self, stream, indent=0):
        """Override write to ensure shapes are Shape objects."""
        # Access shapes property to trigger conversion if needed
        if self._data.get("shapes"):
            # This will convert dicts to Shape objects
            _ = self.shapes
        # Now call parent write()
        super().write(stream, indent)

    @property
    def master(self):
        font = self._font
        assert font
        if not self._master:
            return None
        return font.master(self._master)

    @property
    def paths(self) -> List[Shape]:
        return [x for x in self.shapes if x.is_path]

    @property
    def components(self) -> List[Shape]:
        return [x for x in self.shapes if x.is_component]

    def recursive_component_set(self):
        mine = set([x.ref for x in self.components])
        theirs = set()
        for c in mine:
            other_layer = self.master.get_glyph_layer(c)
            theirs |= other_layer.recursive_component_set()
        return mine | theirs

    def _background_of(self) -> Optional["Layer"]:
        for layer in self._glyph.layers:
            if layer.background == self.id:
                return layer

    def _background_layer(self) -> Optional["Layer"]:
        if not self.background:
            return
        for layer in self._glyph.layers:
            if layer.id == self.background:
                return layer

    def _nested_component_dict(self) -> Dict[str, "Layer"]:
        result: Dict[str, "Layer"] = {}
        todo = [x.ref for x in self.components]
        while todo:
            current = todo.pop()
            if current in result:
                continue
            if self.master:
                result[current] = self.master.get_glyph_layer(current)
            else:
                # Find a glyph with same layerid?
                for layer in self._font.glyphs[current].layers:
                    if layer.id == self.id:
                        result[current] = layer
                        break
                if current not in result and self.isBackground:
                    master_layer = self._background_of()
                    if master_layer:
                        master = master_layer._font.master(master_layer._master)
                        result[current] = master.get_glyph_layer(current)
                        # pylint: disable=protected-access
                        if result[current] and result[current]._background_layer():
                            result[current] = result[current]._background_layer()

                if current not in result or not result[current]:
                    raise ValueError("Could not find layer")
            todo.extend([x.ref for x in result[current].components])
        return result

    @cached_property
    def bounds(self):
        glyphset = {}
        for c in list(self.recursive_component_set()):
            glyphset[c] = self.master.get_glyph_layer(c)
        pen = BoundsPen(glyphset)
        self.draw(pen)
        return pen.bounds

    @property
    def lsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.bounds[0]

    @property
    def rsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.width - self.bounds[2]

    @property
    def valid(self):
        if not self._font or not self._glyph:
            return False
        return True

    @property
    def anchors_dict(self):
        return {a.name: a for a in self.anchors}

    # Pen protocol support...

    def draw(self, pen):
        pen = PointToSegmentPen(pen)
        return self.drawPoints(pen)

    def drawPoints(self, pen):
        for path in self.paths:
            pen.beginPath()
            for node in path.nodes:
                pen.addPoint(
                    pt=(node.x, node.y),
                    segmentType=node.pen_type,
                    smooth=node.is_smooth,
                )
            pen.endPath()
        for component in self.components:
            pen.addComponent(component.ref, component.transform)

    def clearContours(self):
        self.shapes = []

    def getPen(self):
        return SegmentToPointPen(LayerPen(self))

    def decompose(self):
        pen = DecomposingRecordingPen(self._nested_component_dict())
        self.draw(pen)
        self.clearContours()
        pen.replay(self.getPen())


class LayerPen(AbstractPointPen):
    def __init__(self, target):
        self.target = target
        self.curPath = []

    def beginPath(self, identifier=None, **kwargs):
        self.curPath = []

    def endPath(self):
        """End the current sub path."""
        self.target.shapes.append(Shape(nodes=self.curPath))

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if segmentType == "move":
            return
        ourtype = FROM_PEN_TYPE[segmentType]
        if smooth:
            ourtype = ourtype + "s"
        self.curPath.append(Node(pt[0], pt[1], ourtype))

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        self.target.shapes.append(Shape(ref=baseGlyphName, transform=transformation))
