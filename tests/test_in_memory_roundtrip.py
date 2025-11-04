"""
Tests for in-memory round-tripping using orjson.

These tests verify that Font.to_dict() and Font.from_dict() properly
serialize and deserialize font data, and that the JSON representation
is stable (identical after round-tripping).
"""

import orjson
from context import Font, Glyph, Layer, Shape, Node, Anchor, Guide, Names


class TestInMemoryRoundTrip:
    """Test in-memory serialization/deserialization with orjson."""

    def test_simple_font_json_roundtrip(self):
        """Test that a simple font round-trips to identical JSON."""
        # Create a simple font
        font = Font()
        font.upm = 1000
        font.version = (1, 0)

        # Add a simple glyph
        glyph = Glyph(name="A")
        layer = Layer()
        layer.width = 600
        glyph.layers.append(layer)
        font.glyphs.append(glyph)

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify
        font2 = Font.from_dict(orjson.loads(json1))

        # Verify structure is preserved
        assert len(font2.glyphs) == 1
        assert font2.glyphs["A"].name == "A"
        assert font2.glyphs["A"].layers[0].width == 600
        assert font2.upm == 1000

        # Re-serialize - data should be equivalent
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        # Compare by deserializing both and checking equality
        data1 = orjson.loads(json1)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should be identical after round-trip"

    def test_complex_glyph_json_roundtrip(self):
        """Test that a glyph with shapes, anchors, and guides round-trips."""
        font = Font()
        glyph = Glyph(name="A")
        layer = Layer()
        layer.width = 600

        # Add a path shape
        shape = Shape()
        shape.nodes = [
            Node(x=100, y=0, type="line"),
            Node(x=200, y=700, type="line"),
            Node(x=300, y=0, type="line"),
        ]
        shape.closed = True
        layer.shapes.append(shape)

        # Add an anchor
        anchor = Anchor(name="top", x=200, y=700)
        layer.anchors.append(anchor)

        # Add a guide
        guide = Guide(position=350, angle=90, name="right")
        layer.guides.append(guide)

        glyph.layers.append(layer)
        font.glyphs.append(glyph)

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify structure
        font2 = Font.from_dict(orjson.loads(json1))

        assert len(font2.glyphs) == 1
        assert len(font2.glyphs["A"].layers[0].shapes) == 1
        assert len(font2.glyphs["A"].layers[0].shapes[0].nodes) == 3
        assert len(font2.glyphs["A"].layers[0].anchors) == 1
        assert font2.glyphs["A"].layers[0].anchors[0].name == "top"
        assert len(font2.glyphs["A"].layers[0].guides) == 1
        assert font2.glyphs["A"].layers[0].guides[0].name == "right"

        # Re-serialize and compare data (not string order)
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        data1 = orjson.loads(json1)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should be identical after round-trip"

    def test_multiple_glyphs_json_roundtrip(self):
        """Test that a font with multiple glyphs round-trips correctly."""
        font = Font()

        # Add multiple glyphs
        for name in ["A", "B", "C", "space", "period"]:
            glyph = Glyph(name=name)
            layer = Layer()
            layer.width = 500 if name == "space" else 600
            glyph.layers.append(layer)
            font.glyphs.append(glyph)

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify structure
        font2 = Font.from_dict(orjson.loads(json1))

        assert len(font2.glyphs) == 5
        assert font2.glyphs["A"].name == "A"
        assert font2.glyphs["space"].name == "space"
        assert font2.glyphs["space"].layers[0].width == 500

        # Re-serialize and compare data
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        data1 = orjson.loads(json1)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should be identical after round-trip"

    def test_font_with_names_json_roundtrip(self):
        """Test that font names round-trip correctly."""
        font = Font()
        font.names.family_name = "Test Family"
        font.names.style_name = "Bold"
        font.names.designer = "Test Designer"

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify
        font2 = Font.from_dict(orjson.loads(json1))

        # Verify names are preserved (may be I18N dicts after round-trip)
        family = font2.names.family_name
        if isinstance(family, dict):
            assert family.get("dflt") == "Test Family"
        else:
            assert family == "Test Family"

        style = font2.names.style_name
        if isinstance(style, dict):
            assert style.get("dflt") == "Bold"
        else:
            assert style == "Bold"

        # Do a second round-trip to verify stability
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        font3 = Font.from_dict(orjson.loads(json2))
        font_dict3 = font3.to_dict()
        json3 = orjson.dumps(font_dict3)

        # Compare data stability
        data2 = orjson.loads(json2)
        data3 = orjson.loads(json3)
        assert (
            data2 == data3
        ), "Font with names should be stable after second round-trip"

    def test_component_shape_json_roundtrip(self):
        """Test that component shapes round-trip correctly."""
        font = Font()

        # Create base glyph
        base_glyph = Glyph(name="A")
        layer = Layer()
        layer.width = 600
        base_glyph.layers.append(layer)
        font.glyphs.append(base_glyph)

        # Create composite glyph
        composite = Glyph(name="Aacute")
        comp_layer = Layer()
        comp_layer.width = 600

        # Add component
        component = Shape(ref="A")
        component.transform = {"xx": 1, "xy": 0, "yx": 0, "yy": 1, "x": 0, "y": 0}
        comp_layer.shapes.append(component)

        composite.layers.append(comp_layer)
        font.glyphs.append(composite)

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify
        font2 = Font.from_dict(orjson.loads(json1))

        # Verify component
        assert len(font2.glyphs) == 2
        assert font2.glyphs["Aacute"].name == "Aacute"
        assert len(font2.glyphs["Aacute"].layers[0].shapes) == 1
        assert font2.glyphs["Aacute"].layers[0].shapes[0].ref == "A"

        # Re-serialize and compare data
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        data1 = orjson.loads(json1)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should be identical after round-trip"

    def test_no_mutation_on_multiple_roundtrips(self):
        """Test that font_dict can be reused without mutation."""
        font = Font()
        font.upm = 2000

        # Add glyphs
        for i in range(10):
            glyph = Glyph(name=f"glyph{i}")
            layer = Layer()
            layer.width = 600
            glyph.layers.append(layer)
            font.glyphs.append(glyph)

        # Serialize once
        font_dict = font.to_dict()
        json_original = orjson.dumps(font_dict)

        # Deserialize multiple times from the same dict
        for i in range(3):
            font_reloaded = Font.from_dict(orjson.loads(json_original))
            assert len(font_reloaded.glyphs) == 10
            assert font_reloaded.upm == 2000

            # Re-serialize and verify data is identical
            font_dict_reloaded = font_reloaded.to_dict()
            json_reloaded = orjson.dumps(font_dict_reloaded)

            data_orig = orjson.loads(json_original)
            data_reload = orjson.loads(json_reloaded)
            assert data_orig == data_reload

    def test_empty_font_json_roundtrip(self):
        """Test that an empty font round-trips correctly."""
        font = Font()

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1 = orjson.dumps(font_dict1)

        # Deserialize and verify
        font2 = Font.from_dict(orjson.loads(json1))

        # Verify empty font
        assert len(font2.glyphs) == 0
        assert len(font2.axes) == 0
        assert len(font2.masters) == 0

        # Re-serialize and compare data
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        data1 = orjson.loads(json1)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should be identical after round-trip"

    def test_field_aliases_in_json_roundtrip(self):
        """Test that field aliases (e.g., position/pos) work correctly in JSON."""
        font = Font()
        glyph = Glyph(name="A")
        layer = Layer()

        # Add guide with Python API name "position"
        guide = Guide(position=100, angle=0, name="test")
        layer.guides.append(guide)

        glyph.layers.append(layer)
        font.glyphs.append(glyph)

        # Serialize to JSON
        font_dict1 = font.to_dict()
        json1_bytes = orjson.dumps(font_dict1)
        json1_str = json1_bytes.decode("utf-8")

        # Check that file format name "pos" is in JSON
        assert '"pos":100' in json1_str or '"pos": 100' in json1_str

        # Deserialize and verify
        font2 = Font.from_dict(orjson.loads(json1_bytes))

        # Verify Python API still uses "position"
        assert font2.glyphs["A"].layers[0].guides[0].position == 100

        # Re-serialize and compare data
        font_dict2 = font2.to_dict()
        json2 = orjson.dumps(font_dict2)

        data1 = orjson.loads(json1_bytes)
        data2 = orjson.loads(json2)
        assert data1 == data2, "Data should round-trip correctly"
