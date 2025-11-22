from datetime import datetime, timezone, timedelta
import re
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
import orjson


# One would hope this would be easy.


class Context(BaseConvertor):
    suffix = ".babelfont"

    def _load(self):
        """Load from a single .babelfont JSON file."""
        with open(self.filename, "rb") as f:
            data = orjson.loads(f.read())

        # Load from the single JSON structure
        return self._load_from_dict(data)

    def _load_from_dict(self, data):
        """Load font from a dictionary (used for single JSON file loading)."""
        # Extract main sections
        names = data.get("names", {})
        info = data  # Font-level info is at the root level
        glyphs = data.get("glyphs", [])
        self.font.format_specific = info.get("format_specific", {})

        # Load names - create a new Names object from only the non-empty fields
        # This preserves byte-identical roundtrip by not adding empty fields
        from context import Names

        if names:
            # Create Names directly from the data dict
            # Names.from_dict will only include fields present in the dict
            self.font.names = Names.from_dict(names, _copy=False, _validate=False)
            self.font.names._set_parent(self.font)
        else:
            # No names in data, keep the empty Names created by Font()
            self.font.names._set_parent(self.font)

        validate = getattr(self, "_validate", True)

        self.font.axes = [
            Axis.from_dict(j, _copy=False, _validate=validate)
            for j in info.get("axes", [])
        ]
        for axis in self.font.axes:
            axis._set_parent(self.font)

        instances = [
            Instance.from_dict(j, _copy=False, _validate=validate)
            for j in info.get("instances", [])
        ]
        self.font.instances = instances
        for instance in self.font.instances:
            instance._set_parent(self.font)

        self._load_masters(info.get("masters", []))

        for g in glyphs:
            glyph = Glyph.from_dict(g, _copy=False, _validate=validate)
            glyph._set_parent(self.font)
            self.font.glyphs.append(glyph)
            # Layers are already in the glyph from from_dict, but we need
            # to inflate them (convert dicts to Layer objects with proper
            # parent references and inflated shapes/nodes)
            inflated_layers = []
            for json_layer in glyph._data.get("layers", []):
                layer = self._inflate_layer(json_layer)
                layer._glyph = glyph
                layer._set_parent(glyph)
                inflated_layers.append(layer)
            # Replace the raw layer dicts with inflated Layer objects
            glyph._data["layers"] = [
                l.to_dict() if hasattr(l, "to_dict") else l for l in inflated_layers
            ]

        self._load_metadata(info)
        self._load_features_from_data(info)

        # Store the filename for later saving
        self.font.filename = self.filename

        # Note: We don't mark objects clean here because tracking isn't
        # initialized during load. This will be handled in initialize_dirty_tracking()
        # which sets the font as clean for FILE_SAVING after enabling tracking.

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
        validate = getattr(self, "_validate", True)
        for json_master in masters:
            # Master.from_dict handles kerning conversion now
            master = Master.from_dict(json_master, _copy=False, _validate=validate)
            master.font = self.font
            master._set_parent(self.font)
            # Guide conversion handled by Master.from_dict
            # Just ensure parent refs are set
            for guide in master.guides:
                if not hasattr(guide, "_parent_ref") or guide._parent_ref is None:
                    guide._set_parent(master)
            self.font.masters.append(master)

    def _inflate_layer(self, json_layer):
        # Ensure json_layer is a dict (not already a Layer object)
        if isinstance(json_layer, Layer):
            return json_layer

        validate = getattr(self, "_validate", True)
        layer = Layer.from_dict(json_layer, _copy=False, _validate=validate)
        layer._font = self.font

        # Work directly with _data to avoid property overhead during loading
        # Inflate shapes directly in _data
        shapes_data = layer._data.get("shapes", [])
        inflated_shapes = [self._inflate_shape(layer, s) for s in shapes_data]

        # Store as dicts back in _data (shapes will be Shape objects)
        layer._data["shapes"] = [
            s.to_dict() if hasattr(s, "to_dict") else s for s in inflated_shapes
        ]

        return layer

    def _inflate_shape(self, layer, s):
        # If s is already a Shape object (from dict-backed property getter),
        # just set parent
        if isinstance(s, Shape):
            s._set_parent(layer)
            return s

        # Otherwise create Shape from dict
        validate = getattr(self, "_validate", True)
        shape = Shape.from_dict(s, _copy=False, _validate=validate)
        shape._set_parent(layer)

        # Work directly with _data to avoid property overhead
        # Inflate nodes directly in _data
        nodes_data = shape._data.get("nodes", [])
        if nodes_data:
            inflated_nodes = [self._inflate_node(n) for n in nodes_data]
            for node in inflated_nodes:
                node._set_parent(shape)
            # Store as dicts back in _data
            shape._data["nodes"] = [
                n.to_dict() if hasattr(n, "to_dict") else n for n in inflated_nodes
            ]
        return shape

    def _inflate_node(self, n):
        # n can be [x, y, type] or [x, y, type, formatspecific]
        # Node.from_dict handles both list and dict formats
        validate = getattr(self, "_validate", True)
        return Node.from_dict(n, _copy=False, _validate=validate)

    def _load_metadata(self, info):
        # Load basic metadata fields
        for k in ["note", "upm", "version", "date", "customOpenTypeValues"]:
            if k in info:
                setattr(self.font, k, info[k])

        # Load babelfont-rs specific fields directly into _data
        # These fields should be preserved as-is for round-trip compatibility
        for k in [
            "custom_ot_values",
            "variation_sequences",
            "first_kern_groups",
            "second_kern_groups",
            "format_specific",
            "source",
        ]:
            if k in info:
                self.font._data[k] = info[k]

        # Parse date - handle both folder format and ISO 8601 format
        if hasattr(self.font, "date") and self.font.date:
            if isinstance(self.font.date, str):
                # Parse date with timezone support
                # Try ISO 8601 format first: 2024-03-23T23:08:27+01:00
                try:
                    # Match ISO 8601 with timezone offset
                    # e.g., "2024-03-23T23:08:27+01:00"
                    iso_match = re.match(
                        r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})"
                        r"([+-]\d{2}:\d{2})",
                        self.font.date,
                    )
                    if iso_match:
                        date_str, time_str, tz_str = iso_match.groups()
                        # Parse timezone offset
                        tz_sign = 1 if tz_str[0] == "+" else -1
                        tz_hours, tz_mins = map(int, tz_str[1:].split(":"))
                        tz_offset = timezone(
                            timedelta(
                                hours=tz_sign * tz_hours, minutes=tz_sign * tz_mins
                            )
                        )
                        # Parse datetime with timezone
                        dt = datetime.strptime(
                            f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"
                        )
                        self.font.date = dt.replace(tzinfo=tz_offset)
                    else:
                        # Try simple format without timezone
                        date_str = self.font.date.split(".")[0]
                        date_str = date_str.split("+")[0]
                        date_str = date_str.replace("T", " ")
                        self.font.date = datetime.strptime(
                            date_str, "%Y-%m-%d %H:%M:%S"
                        )
                except (ValueError, AttributeError):
                    # Fallback to simple format
                    date_str = self.font.date.split(".")[0]
                    date_str = date_str.split("+")[0].replace("T", " ")
                    self.font.date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    def _load_features_from_data(self, info):
        """Load features from data dict (for single JSON file)."""
        if "features" in info and info["features"]:
            features_data = info["features"]
            # Features are stored as structured dict, not FEA text
            if isinstance(features_data, dict):
                self.font.features = Features.from_dict(
                    features_data, _copy=False, _validate=False
                )
                self.font.features._set_parent(self.font)
            elif isinstance(features_data, str):
                # Handle string format (FEA text)
                self.font.features = Features.from_fea(features_data)
                self.font.features._set_parent(self.font)

    def _save(self):
        """Save the font to a single .babelfont JSON file."""
        # Write the entire font as a single JSON file
        with open(self.filename, "wb") as f:
            self.font.write(stream=f)
