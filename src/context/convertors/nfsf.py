from datetime import datetime
from context import (
    Anchor,
    Axis,
    Features,
    Glyph,
    Guide,
    Instance,
    Layer,
    Master,
    Node,
    Shape,
)
from context.convertors import BaseConvertor
from pathlib import Path
import orjson
import os


# One would hope this would be easy.


class Context(BaseConvertor):
    suffix = ".babelfont"

    def _load_file(self, filename):
        contents = open(os.path.join(self.filename, filename), "r").read()
        return orjson.loads(contents)

    def _load(self):
        names = self._load_file("names.json")
        info = self._load_file("info.json")
        glyphs = self._load_file("glyphs.json")
        self.font._formatspecific = info.get("_", {})
        for k, v in names.items():
            if k in self.font.names.__dataclass_fields__:
                getattr(self.font.names, k).copy_in(v)
            elif k == "_":
                self.font.names._formatspecific = v
        # Set parent reference for names
        self.font.names._set_parent(self.font)

        self.font.axes = [Axis(**j) for j in info.get("axes", [])]
        for axis in self.font.axes:
            axis._set_parent(self.font)

        self.font.instances = [Instance(**j) for j in info.get("instances", [])]
        for instance in self.font.instances:
            instance._set_parent(self.font)

        self._load_masters(info.get("masters", []))

        for g in glyphs:
            glyph = Glyph(**g)
            glyph._set_parent(self.font)
            self.font.glyphs.append(glyph)
            for json_layer in self._load_file(glyph.babelfont_filename):
                layer = self._inflate_layer(json_layer)
                layer._glyph = glyph
                layer._set_parent(glyph)
                glyph.layers.append(layer)

        self._load_metadata(info)
        self._load_features()

        # Store the filename for later saving
        self.font.filename = self.filename

        # Mark entire font as clean for file_saving since it matches disk state
        # But keep dirty for canvas_render so UI knows to draw
        self._mark_all_clean_for_file_saving(self.font)

        return self.font

    def _mark_all_clean_for_file_saving(self, obj):
        """Recursively mark object and children as clean for file_saving."""
        from context.BaseObject import DIRTY_FILE_SAVING

        if hasattr(obj, "mark_clean"):
            obj.mark_clean(DIRTY_FILE_SAVING, recursive=False)

        # Handle Font
        if hasattr(obj, "glyphs"):
            for glyph in obj.glyphs:
                self._mark_all_clean_for_file_saving(glyph)
        if hasattr(obj, "masters"):
            for master in obj.masters:
                self._mark_all_clean_for_file_saving(master)
        if hasattr(obj, "axes"):
            for axis in obj.axes:
                self._mark_all_clean_for_file_saving(axis)
        if hasattr(obj, "instances"):
            for instance in obj.instances:
                self._mark_all_clean_for_file_saving(instance)
        if hasattr(obj, "names"):
            self._mark_all_clean_for_file_saving(obj.names)
        if hasattr(obj, "features"):
            self._mark_all_clean_for_file_saving(obj.features)

        # Handle Glyph
        if hasattr(obj, "layers"):
            for layer in obj.layers:
                self._mark_all_clean_for_file_saving(layer)

        # Handle Layer
        if hasattr(obj, "shapes"):
            for shape in obj.shapes:
                self._mark_all_clean_for_file_saving(shape)
        if hasattr(obj, "anchors"):
            for anchor in obj.anchors:
                self._mark_all_clean_for_file_saving(anchor)
        if hasattr(obj, "guides"):
            for guide in obj.guides:
                self._mark_all_clean_for_file_saving(guide)

        # Handle Shape
        if hasattr(obj, "nodes") and obj.nodes:
            for node in obj.nodes:
                self._mark_all_clean_for_file_saving(node)

    def _load_masters(self, masters):
        for json_master in masters:
            if "kerning" in json_master:
                json_master["kerning"] = {
                    tuple(k.split("//")): v for k, v in json_master["kerning"].items()
                }
            master = Master(**json_master)
            master.font = self.font
            master._set_parent(self.font)
            master.guides = [Guide(**Guide._normalize_fields(m)) for m in master.guides]
            for guide in master.guides:
                guide._set_parent(master)
            self.font.masters.append(master)

    def _inflate_layer(self, json_layer):
        # Extract components if present, they'll be added to shapes
        components = json_layer.pop("components", [])

        layer = Layer(**json_layer)
        layer.guides = [Guide(**Guide._normalize_fields(m)) for m in layer.guides]
        layer.anchors = [Anchor(**m) for m in layer.anchors]
        layer._font = self.font
        # Set parent references for change tracking
        for guide in layer.guides:
            guide._set_parent(layer)
        for anchor in layer.anchors:
            anchor._set_parent(layer)

        # Inflate regular shapes
        layer.shapes = [self._inflate_shape(layer, s) for s in layer.shapes]

        # Inflate components (which are also Shape objects)
        for component in components:
            layer.shapes.append(self._inflate_shape(layer, component))

        return layer

    def _inflate_shape(self, layer, s):
        shape = Shape(**s)
        shape._set_parent(layer)
        if shape.nodes:
            shape.nodes = [self._inflate_node(n) for n in shape.nodes]
            for node in shape.nodes:
                node._set_parent(shape)
        return shape

    def _inflate_node(self, n):
        # n can be [x, y, type] or [x, y, type, formatspecific]
        if len(n) == 3:
            return Node(*n)
        else:
            # 4th element is format-specific data (dict or JSON)
            x, y, node_type, formatspecific = n
            return Node(x, y, node_type, _=formatspecific)

    def _load_metadata(self, info):
        for k in ["note", "upm", "version", "date", "customOpenTypeValues"]:
            if k in info:
                setattr(self.font, k, info[k])
        self.font.date = datetime.strptime(self.font.date, "%Y-%m-%d %H:%M:%S")

    def _load_features(self):
        path = os.path.join(self.filename, "features.fea")
        if os.path.isfile(path):
            with open(path, "r") as f:
                fea_content = f.read()
                # Don't validate glyph names during loading to allow
                # round-tripping of features that reference glyphs
                # not present in the current font
                self.font.features = Features.from_fea(fea_content)
                self.font.features._set_parent(self.font)

    def _save(self):
        path = Path(self.filename)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "info.json", "wb") as f:
            self.font.write(stream=f)

        with open(path / "names.json", "wb") as f:
            self.font._write_value(f, "glyphs", self.font.names)

        with open(path / "features.fea", "w") as f:
            if self.font.features:
                f.write(self.font.features.to_fea())

        with open(path / "glyphs.json", "wb") as f:
            for g in self.font.glyphs:
                glyphpath = path / "glyphs"
                glyphpath.mkdir(parents=True, exist_ok=True)
                with open(path / g.babelfont_filename, "wb") as f2:
                    g._write_value(f2, "layers", g.layers)
            self.font._write_value(f, "glyphs", self.font.glyphs)
