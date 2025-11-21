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

    def _is_single_json_file(self):
        """Check if the filename is a single JSON file or a directory."""
        # Check if it's a file (single JSON) or directory (folder structure)
        return os.path.isfile(self.filename)

    def _load_file(self, filename):
        with open(os.path.join(self.filename, filename), "r") as f:
            contents = f.read()
        return orjson.loads(contents)

    def _load(self):
        # Check if loading from single JSON file or folder structure
        if self._is_single_json_file():
            return self._load_from_json()
        else:
            return self._load_from_folder_structure()

    def _load_from_json(self):
        """Load from a single .babelfont.json file."""
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
        self.font.user_data = info.get("_", {})

        # With dict-backed storage, check if the attribute exists
        # Names has 23 I18NDictionary fields
        names_fields = {
            "familyName",
            "styleName",
            "copyright",
            "version",
            "trademark",
            "manufacturer",
            "designer",
            "description",
            "vendorURL",
            "designerURL",
            "license",
            "licenseURL",
            "compatibleFullName",
            "sampleText",
            "postScriptFontName",
            "postScriptSlantAngle",
            "WWSFamilyName",
            "WWSSubfamilyName",
            "lightBackgroundPalette",
            "darkBackgroundPalette",
            "variationsPostScriptNamePrefix",
            "preferredFamilyName",
            "preferredSubfamilyName",
        }
        for k, v in names.items():
            if k in names_fields:
                getattr(self.font.names, k).copy_in(v)
            elif k == "_":
                self.font.names.user_data = v
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
            # For single JSON file, layers are in the glyph data
            # For folder structure, layers are in separate files
            if self._is_single_json_file():
                # Layers are embedded in the glyph data
                layers_data = g.get("layers", [])
                for json_layer in layers_data:
                    layer = self._inflate_layer(json_layer)
                    layer._glyph = glyph
                    layer._set_parent(glyph)
                    glyph.layers.append(layer)
            else:
                # Load layers from separate file
                for json_layer in self._load_file(glyph.babelfont_filename):
                    layer = self._inflate_layer(json_layer)
                    layer._glyph = glyph
                    layer._set_parent(glyph)
                    glyph.layers.append(layer)

        self._load_metadata(info)
        if self._is_single_json_file():
            self._load_features_from_data(info)
        else:
            self._load_features()

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

        # Extract components if present, they'll be added to shapes
        components = json_layer.pop("components", [])

        validate = getattr(self, "_validate", True)
        layer = Layer.from_dict(json_layer, _copy=False, _validate=validate)
        layer._font = self.font

        # Work directly with _data to avoid property overhead during loading
        # Inflate shapes (including components) directly in _data
        shapes_data = layer._data.get("shapes", [])
        inflated_shapes = [self._inflate_shape(layer, s) for s in shapes_data]

        # Add components to shapes
        for component in components:
            inflated_shapes.append(self._inflate_shape(layer, component))

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
        for k in ["note", "upm", "version", "date", "customOpenTypeValues"]:
            if k in info:
                setattr(self.font, k, info[k])
        # Parse date - handle both folder format and ISO 8601 format
        if hasattr(self.font, "date") and self.font.date:
            if isinstance(self.font.date, str):
                # Try folder format first
                try:
                    self.font.date = datetime.strptime(
                        self.font.date, "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    # Try ISO 8601 format: 2024-03-23T23:08:27+01:00
                    # Strip timezone and convert to simple format
                    date_str = self.font.date.split("+")[0].split("-")[0]
                    date_str = self.font.date.split("+")[0].replace("T", " ")
                    # Handle potential trailing timezone info
                    if "-" in date_str.split(" ")[1]:
                        date_str = date_str.rsplit("-", 1)[0]
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

    def _load_features(self):
        """Load features from .fea file (for folder structure)."""
        path = os.path.join(self.filename, "features.fea")
        if os.path.isfile(path):
            with open(path, "r") as f:
                fea_content = f.read()
                # Don't validate glyph names during loading to allow
                # round-tripping of features that reference glyphs
                # not present in the current font
                self.font.features = Features.from_fea(fea_content)
                self.font.features._set_parent(self.font)

    def _load_from_folder(self):
        """Load from .babelfont folder structure."""
        names = self._load_file("names.json")
        info = self._load_file("info.json")
        glyphs = self._load_file("glyphs.json")

        # Merge names into info for unified loading
        info["names"] = names
        info["glyphs"] = glyphs

        return self._load_from_dict(info)

    def _load_from_folder_structure(self):
        """Load from .babelfont folder structure with separate layer files."""
        names = self._load_file("names.json")
        info = self._load_file("info.json")
        glyphs = self._load_file("glyphs.json")
        self.font.user_data = info.get("_", {})

        # Load names
        names_fields = {
            "familyName",
            "styleName",
            "copyright",
            "version",
            "trademark",
            "manufacturer",
            "designer",
            "description",
            "vendorURL",
            "designerURL",
            "license",
            "licenseURL",
            "compatibleFullName",
            "sampleText",
            "postScriptFontName",
            "postScriptSlantAngle",
            "WWSFamilyName",
            "WWSSubfamilyName",
            "lightBackgroundPalette",
            "darkBackgroundPalette",
            "variationsPostScriptNamePrefix",
            "preferredFamilyName",
            "preferredSubfamilyName",
        }
        for k, v in names.items():
            if k in names_fields:
                getattr(self.font.names, k).copy_in(v)
            elif k == "_":
                self.font.names.user_data = v
        self.font.names._set_parent(self.font)

        validate = getattr(self, "_validate", True)

        # Load axes
        self.font.axes = [
            Axis.from_dict(j, _copy=False, _validate=validate)
            for j in info.get("axes", [])
        ]
        for axis in self.font.axes:
            axis._set_parent(self.font)

        # Load instances
        instances = [
            Instance.from_dict(j, _copy=False, _validate=validate)
            for j in info.get("instances", [])
        ]
        self.font.instances = instances
        for instance in self.font.instances:
            instance._set_parent(self.font)

        # Load masters
        self._load_masters(info.get("masters", []))

        # Load glyphs with layers from separate files
        for g in glyphs:
            glyph = Glyph.from_dict(g, _copy=False, _validate=validate)
            glyph._set_parent(self.font)
            self.font.glyphs.append(glyph)
            # Load layers from separate file
            for json_layer in self._load_file(glyph.babelfont_filename):
                layer = self._inflate_layer(json_layer)
                layer._glyph = glyph
                layer._set_parent(glyph)
                glyph.layers.append(layer)

        self._load_metadata(info)
        self._load_features()

        # Store the filename for later saving
        self.font.filename = self.filename

        return self.font

    def _save(self):
        """Save the font to disk."""
        from context.BaseObject import DIRTY_FILE_SAVING

        path = Path(self.filename)
        path.mkdir(parents=True, exist_ok=True)

        # Write info.json (contains font metadata, axes, instances, masters)
        # Check if font's OWN fields are dirty (not propagated from children)
        # info.json contains: upm, version, date, note,
        # custom_opentype_values, first_kern_groups, second_kern_groups,
        # axes, instances, masters
        font_dirty_fields = self.font.get_dirty_fields(DIRTY_FILE_SAVING)
        info_fields = {
            "upm",
            "version",
            "date",
            "note",
            "custom_opentype_values",
            "first_kern_groups",
            "second_kern_groups",
            "axes",
            "instances",
            "masters",
        }
        font_info_dirty = bool(font_dirty_fields & info_fields)
        info_dirty = (
            font_info_dirty
            or any(axis.is_dirty(DIRTY_FILE_SAVING) for axis in self.font.axes)
            or any(inst.is_dirty(DIRTY_FILE_SAVING) for inst in self.font.instances)
            or any(master.is_dirty(DIRTY_FILE_SAVING) for master in self.font.masters)
        )
        info_file = path / "info.json"
        if info_dirty or not info_file.exists():
            reason = "dirty" if info_dirty else "new location"
            print(f"  📝 Writing info.json ({reason})")
            # Temporarily remove glyphs before writing (they're in separate files)
            saved_glyphs = self.font._data.get("glyphs", [])
            self.font._data["glyphs"] = []

            with open(info_file, "wb") as f:
                self.font.write(stream=f)

            # Restore glyphs
            self.font._data["glyphs"] = saved_glyphs
        else:
            print("  ⏩ Skipping info.json (clean)")

        # Write names.json
        names_dirty = self.font.names.is_dirty(DIRTY_FILE_SAVING)
        names_file = path / "names.json"
        if names_dirty or not names_file.exists():
            reason = "dirty" if names_dirty else "new location"
            print(f"  📝 Writing names.json ({reason})")
            with open(names_file, "wb") as f:
                self.font._write_value(f, "glyphs", self.font.names)
        else:
            print("  ⏩ Skipping names.json (clean)")

        # Write features.fea
        features_dirty = (
            self.font.features.is_dirty(DIRTY_FILE_SAVING)
            if self.font.features
            else False
        )
        features_file = path / "features.fea"
        if features_dirty or not features_file.exists():
            reason = "dirty" if features_dirty else "new location"
            print(f"  📝 Writing features.fea ({reason})")
            with open(features_file, "w") as f:
                if self.font.features:
                    f.write(self.font.features.to_fea())
        else:
            print("  ⏩ Skipping features.fea (clean)")

        # Write glyphs - only write individual glyph files if they're dirty
        glyphpath = path / "glyphs"
        glyphpath.mkdir(parents=True, exist_ok=True)

        # Count glyphs written for statistics
        dirty_count = 0
        clean_count = 0

        # Check if any glyph is dirty (needs individual file write)
        for g in self.font.glyphs:
            # Write glyph file if:
            # 1. Glyph is dirty (changed), OR
            # 2. Glyph file doesn't exist yet (new save location)
            glyph_file = path / g.babelfont_filename
            is_dirty = g.is_dirty(DIRTY_FILE_SAVING)
            file_missing = not glyph_file.exists()
            needs_write = is_dirty or file_missing

            if needs_write:
                reason = "dirty" if is_dirty else "new location"
                print(f"  📝 Writing glyph: {g.name} ({reason})")
                with open(glyph_file, "wb") as f2:
                    g._write_value(f2, "layers", g.layers)
                dirty_count += 1
            else:
                clean_count += 1

        # Only write glyphs.json if:
        # 1. Font is dirty for "glyphs" field (glyphs added/removed), OR
        # 2. Any glyph METADATA is dirty (name, codepoints, etc.), OR
        # 3. glyphs.json doesn't exist yet (new save location)
        # NOTE: glyphs.json only contains metadata, not layer data.
        # Layer changes don't require glyphs.json to be rewritten.
        glyphs_json_path = path / "glyphs.json"
        # Check if the "glyphs" field was marked dirty (add/remove)
        font_dirty_fields = self.font.get_dirty_fields(DIRTY_FILE_SAVING)
        font_glyphs_dirty = "glyphs" in font_dirty_fields

        # Check if any glyph's metadata fields are dirty
        # Metadata fields: name, production_name, category, codepoints,
        # exported, direction (layers are separate)
        metadata_fields = {
            "name",
            "production_name",
            "category",
            "codepoints",
            "exported",
            "direction",
        }
        any_glyph_metadata_dirty = False
        for g in self.font.glyphs:
            glyph_dirty_fields = g.get_dirty_fields(DIRTY_FILE_SAVING)
            if glyph_dirty_fields & metadata_fields:
                any_glyph_metadata_dirty = True
                break

        file_missing = not glyphs_json_path.exists()

        if font_glyphs_dirty or any_glyph_metadata_dirty or file_missing:
            if font_glyphs_dirty:
                reason = "font dirty"
            elif any_glyph_metadata_dirty:
                reason = "glyph metadata dirty"
            else:
                reason = "new location"
            print(f"  📝 Writing glyphs.json ({reason})")
            # Write glyphs without layers (layers are in separate .nfsglyph files)
            # Temporarily remove layers before serializing
            saved_layers = {}
            for g in self.font.glyphs:
                saved_layers[g.name] = g._data.get("layers", [])
                g._data["layers"] = []

            with open(glyphs_json_path, "wb") as f:
                self.font._write_value(f, "glyphs", self.font.glyphs)

            # Restore layers
            for g in self.font.glyphs:
                g._data["layers"] = saved_layers[g.name]
        else:
            print("  ⏩ Skipping glyphs.json (clean)")

        # Report statistics
        print(
            f"  💾 Wrote {dirty_count} glyph file(s), "
            f"skipped {clean_count} clean glyph(s)"
        )
