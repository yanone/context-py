"""Test complete roundtrip of font data through save/load cycles.

This ensures that all object types serialize and deserialize correctly,
including field aliases, format-specific data, and complex hierarchies.
"""

import pytest
import json
from datetime import datetime
from context import load
from context.Font import Font
from context.Glyph import Glyph
from context.Layer import Layer
from context.Shape import Shape
from context.Node import Node
from context.Anchor import Anchor
from context.Guide import Guide
from context.BaseObject import Position, Color
from context.Master import Master
from context.Axis import Axis
from context.Instance import Instance
from context.Features import Features


@pytest.fixture
def comprehensive_font(tmp_path):
    """Create a comprehensive test font with all object types."""
    font = Font()
    font.upm = 1000
    font.version = [2, 5]
    font.date = datetime.strptime("2025-11-02 12:00:00", "%Y-%m-%d %H:%M:%S")
    font.note = "Test font for roundtrip testing"

    # Set names with I18N
    font.names.familyName = {"en": "RoundtripTest", "de": "Rundreisetest"}
    font.names.styleName = {"en": "Regular"}
    font.names.designer = {"en": "Test Designer"}
    font.names.manufacturerURL = {"en": "https://example.com"}

    # Add format-specific data to font
    font.user_data = {"com.test": {"version": "1.0", "data": [1, 2, 3]}}

    # Add axes (for variable font)
    axis_weight = Axis(
        name="Weight",
        tag="wght",
        min=100,
        max=900,
        default=400,
        _={"com.test": "weight-data"},
    )
    axis_weight._set_parent(font)
    font.axes.append(axis_weight)

    axis_width = Axis(name="Width", tag="wdth", min=75, max=125, default=100)
    axis_width._set_parent(font)
    font.axes.append(axis_width)

    # Add instances
    instance_light = Instance(
        name={"en": "Light", "de": "Leicht"},
        location={"wght": 300, "wdth": 100},
        _={"com.test": "instance-metadata"},
    )
    instance_light._set_parent(font)
    font.instances.append(instance_light)

    instance_bold = Instance(name={"en": "Bold"}, location={"wght": 700, "wdth": 100})
    instance_bold._set_parent(font)
    font.instances.append(instance_bold)

    # Add masters
    master_regular = Master(
        name={"en": "Regular"},
        id="master-regular",
        location={"wght": 400, "wdth": 100},
        kerning={("A", "V"): -50, ("T", "a"): -30},
        guides=[
            Guide(
                name="baseline",
                position=Position(x=0, y=0, angle=0),
                color=Color(r=255, g=0, b=0, a=128),
            ),
            Guide(name="x-height", position=Position(x=0, y=500, angle=0)),
            Guide(name="ascender", position=Position(x=0, y=750, angle=0)),
            Guide(
                name="diagonal",
                position=Position(x=100, y=200, angle=45),
                color=Color(r=0, g=255, b=0, a=200),
            ),
        ],
        _={"com.test": {"master": "data"}},
    )
    master_regular._set_parent(font)
    for guide in master_regular.guides:
        guide._set_parent(master_regular)
    font.masters.append(master_regular)

    master_bold = Master(
        name={"en": "Bold"},
        id="master-bold",
        location={"wght": 700, "wdth": 100},
    )
    master_bold._set_parent(font)
    font.masters.append(master_bold)

    # Add features
    font.features = Features.from_fea(
        """
@lowercase = [a b c d e];
@uppercase = [A B C D E];

# Prefix: kern
lookup kern1 {
    pos A V -50;
    pos T a -30;
} kern1;

feature kern {
    lookup kern1;
} kern;

feature liga {
    sub f f i by f_f_i;
    sub f f by f_f;
} liga;
"""
    )
    font.features._set_parent(font)

    # Create glyph with paths and nodes (including format-specific data)
    glyph_a = Glyph(
        name="A",
        category="base",
        codepoints=[65],
        exported=True,
        _={"com.test": {"glyph": "metadata"}},
    )
    glyph_a._set_parent(font)

    layer_a_regular = Layer(
        width=600,
        height=0,
        _master="master-regular",
        _={"com.test": "layer-data"},
    )
    layer_a_regular._set_parent(glyph_a)
    layer_a_regular._font = font

    # Add guides to layer
    layer_a_regular.guides.append(
        Guide(
            name="left-stem",
            position=Position(x=100, y=0, angle=90),
            color=Color(r=0, g=0, b=255, a=150),
        )
    )
    layer_a_regular.guides[0]._set_parent(layer_a_regular)

    # Add shape with nodes including format-specific data
    shape_outline = Shape(
        nodes=[
            Node(100, 0, "line"),
            Node(200, 0, "line", _={"com.test": "node-data"}),
            Node(300, 700, "line"),
            Node(250, 700, "curve"),
            Node(200, 680, "offcurve"),
            Node(150, 700, "curve"),
        ],
        closed=True,
        _={"com.test": "shape-metadata"},
    )
    shape_outline._set_parent(layer_a_regular)
    for node in shape_outline.nodes:
        node._set_parent(shape_outline)
    layer_a_regular.shapes.append(shape_outline)

    # Add second shape (counter)
    shape_counter = Shape(
        nodes=[
            Node(150, 100, "line"),
            Node(250, 100, "line"),
            Node(220, 600, "line"),
            Node(180, 600, "line"),
        ],
        closed=True,
    )
    shape_counter._set_parent(layer_a_regular)
    for node in shape_counter.nodes:
        node._set_parent(shape_counter)
    layer_a_regular.shapes.append(shape_counter)

    # Add anchors
    anchor_top = Anchor(name="top", x=200, y=700, _={"com.test": "anchor-data"})
    anchor_top._set_parent(layer_a_regular)
    layer_a_regular.anchors.append(anchor_top)

    anchor_bottom = Anchor(name="bottom", x=200, y=0)
    anchor_bottom._set_parent(layer_a_regular)
    layer_a_regular.anchors.append(anchor_bottom)

    glyph_a.layers.append(layer_a_regular)

    # Add bold layer
    layer_a_bold = Layer(width=650, height=0, _master="master-bold")
    layer_a_bold._set_parent(glyph_a)
    layer_a_bold._font = font
    glyph_a.layers.append(layer_a_bold)

    font.glyphs.append(glyph_a)

    # Create glyph with component
    glyph_aacute = Glyph(
        name="Aacute", category="base", codepoints=[193], exported=True
    )
    glyph_aacute._set_parent(font)

    layer_aacute = Layer(width=600, height=0, _master="master-regular")
    layer_aacute._set_parent(glyph_aacute)
    layer_aacute._font = font

    # Add component referencing glyph A
    component_a = Shape(
        ref="A",
        transform=[1, 0, 0, 1, 0, 0],
        _={"com.test": "component-data"},
    )
    component_a._set_parent(layer_aacute)
    layer_aacute.shapes.append(component_a)

    # Add component for accent
    component_acute = Shape(ref="acutecomb", transform=[1, 0, 0, 1, 200, 700])
    component_acute._set_parent(layer_aacute)
    layer_aacute.shapes.append(component_acute)

    glyph_aacute.layers.append(layer_aacute)
    font.glyphs.append(glyph_aacute)

    # Create simple glyph (no paths, will be component reference)
    glyph_acute = Glyph(
        name="acutecomb", category="mark", codepoints=[769], exported=True
    )
    glyph_acute._set_parent(font)

    layer_acute = Layer(width=0, height=0, _master="master-regular")
    layer_acute._set_parent(glyph_acute)
    layer_acute._font = font

    shape_acute = Shape(
        nodes=[
            Node(0, 0, "line"),
            Node(100, 100, "line"),
            Node(50, 100, "line"),
        ],
        closed=True,
    )
    shape_acute._set_parent(layer_acute)
    for node in shape_acute.nodes:
        node._set_parent(shape_acute)
    layer_acute.shapes.append(shape_acute)

    glyph_acute.layers.append(layer_acute)
    font.glyphs.append(glyph_acute)

    # Enable tracking before tests use the font
    font.initialize_dirty_tracking()

    return font


def compare_fonts(font1, font2, path="font"):
    """Recursively compare two font objects for equality.

    Returns a list of differences found.
    """
    differences = []

    # Compare basic attributes
    for attr in ["upm", "version", "note"]:
        val1 = getattr(font1, attr, None)
        val2 = getattr(font2, attr, None)
        if val1 != val2:
            differences.append(f"{path}.{attr}: {val1} != {val2}")

    # Compare dates (convert to string for comparison)
    if str(font1.date) != str(font2.date):
        differences.append(f"{path}.date: {font1.date} != {font2.date}")

    # Compare names (normalize I18N dicts for comparison)
    for name_field in ["familyName", "styleName", "designer", "manufacturerURL"]:
        val1 = getattr(font1.names, name_field, None)
        val2 = getattr(font2.names, name_field, None)
        # Normalize single-value I18N dicts to get_default() for comparison
        if hasattr(val1, "get_default") and len(val1) == 1:
            val1 = val1.get_default()
        if hasattr(val2, "get_default") and len(val2) == 1:
            val2 = val2.get_default()
        if val1 != val2:
            differences.append(f"{path}.names.{name_field}: {val1} != {val2}")

    # Compare format-specific
    if font1.user_data != font2.user_data:
        differences.append(
            f"{path}.user_data: " f"{font1.user_data} != {font2.user_data}"
        )

    # Compare axes
    if len(font1.axes) != len(font2.axes):
        differences.append(
            f"{path}.axes length: {len(font1.axes)} != {len(font2.axes)}"
        )
    for i, (axis1, axis2) in enumerate(zip(font1.axes, font2.axes)):
        for attr in ["name", "tag", "min", "max", "default"]:
            val1 = getattr(axis1, attr)
            val2 = getattr(axis2, attr)
            if val1 != val2:
                differences.append(f"{path}.axes[{i}].{attr}: {val1} != {val2}")
        if axis1.user_data != axis2.user_data:
            differences.append(
                f"{path}.axes[{i}].user_data: "
                f"{axis1.user_data} != {axis2.user_data}"
            )

    # Compare instances
    if len(font1.instances) != len(font2.instances):
        differences.append(
            f"{path}.instances length: "
            f"{len(font1.instances)} != {len(font2.instances)}"
        )
    for i, (inst1, inst2) in enumerate(zip(font1.instances, font2.instances)):
        if inst1.name != inst2.name:
            differences.append(
                f"{path}.instances[{i}].name: {inst1.name} != {inst2.name}"
            )
        if inst1.location != inst2.location:
            differences.append(
                f"{path}.instances[{i}].location: "
                f"{inst1.location} != {inst2.location}"
            )
        if inst1.user_data != inst2.user_data:
            differences.append(
                f"{path}.instances[{i}].user_data: "
                f"{inst1.user_data} != {inst2.user_data}"
            )

    # Compare masters
    if len(font1.masters) != len(font2.masters):
        differences.append(
            f"{path}.masters length: " f"{len(font1.masters)} != {len(font2.masters)}"
        )
    for i, (master1, master2) in enumerate(zip(font1.masters, font2.masters)):
        for attr in ["name", "id", "location", "kerning"]:
            val1 = getattr(master1, attr)
            val2 = getattr(master2, attr)
            if val1 != val2:
                differences.append(f"{path}.masters[{i}].{attr}: {val1} != {val2}")
        if master1.user_data != master2.user_data:
            differences.append(
                f"{path}.masters[{i}].user_data: "
                f"{master1.user_data} != {master2.user_data}"
            )

        # Compare master guides
        if len(master1.guides) != len(master2.guides):
            differences.append(
                f"{path}.masters[{i}].guides length: "
                f"{len(master1.guides)} != {len(master2.guides)}"
            )
        for j, (guide1, guide2) in enumerate(zip(master1.guides, master2.guides)):
            if guide1.name != guide2.name:
                differences.append(
                    f"{path}.masters[{i}].guides[{j}].name: "
                    f"{guide1.name} != {guide2.name}"
                )
            if guide1.position != guide2.position:
                differences.append(
                    f"{path}.masters[{i}].guides[{j}].position: "
                    f"{guide1.position} != {guide2.position}"
                )
            if guide1.color != guide2.color:
                differences.append(
                    f"{path}.masters[{i}].guides[{j}].color: "
                    f"{guide1.color} != {guide2.color}"
                )

    # Compare features
    if font1.features and font2.features:
        if font1.features.classes != font2.features.classes:
            differences.append(
                f"{path}.features.classes: "
                f"{font1.features.classes} != {font2.features.classes}"
            )
        if font1.features.prefixes != font2.features.prefixes:
            differences.append(
                f"{path}.features.prefixes: "
                f"{font1.features.prefixes} != {font2.features.prefixes}"
            )
        if font1.features.features != font2.features.features:
            differences.append(
                f"{path}.features.features: "
                f"{font1.features.features} != {font2.features.features}"
            )
    elif font1.features or font2.features:
        differences.append(f"{path}.features: one has features, other doesn't")

    # Compare glyphs
    if len(font1.glyphs) != len(font2.glyphs):
        differences.append(
            f"{path}.glyphs length: " f"{len(font1.glyphs)} != {len(font2.glyphs)}"
        )

    for i, (glyph1, glyph2) in enumerate(zip(font1.glyphs, font2.glyphs)):
        gpath = f"{path}.glyphs[{i}]"
        for attr in ["name", "category", "codepoints", "exported"]:
            val1 = getattr(glyph1, attr)
            val2 = getattr(glyph2, attr)
            if val1 != val2:
                differences.append(f"{gpath}.{attr}: {val1} != {val2}")

        if glyph1.user_data != glyph2.user_data:
            differences.append(
                f"{gpath}.user_data: " f"{glyph1.user_data} != {glyph2.user_data}"
            )

        # Compare layers
        if len(glyph1.layers) != len(glyph2.layers):
            differences.append(
                f"{gpath}.layers length: "
                f"{len(glyph1.layers)} != {len(glyph2.layers)}"
            )

        for j, (layer1, layer2) in enumerate(zip(glyph1.layers, glyph2.layers)):
            lpath = f"{gpath}.layers[{j}]"
            for attr in ["width", "height", "_master"]:
                val1 = getattr(layer1, attr)
                val2 = getattr(layer2, attr)
                if val1 != val2:
                    differences.append(f"{lpath}.{attr}: {val1} != {val2}")

            if layer1.user_data != layer2.user_data:
                differences.append(
                    f"{lpath}.user_data: " f"{layer1.user_data} != {layer2.user_data}"
                )

            # Compare guides
            if len(layer1.guides) != len(layer2.guides):
                differences.append(
                    f"{lpath}.guides length: "
                    f"{len(layer1.guides)} != {len(layer2.guides)}"
                )
            for k, (guide1, guide2) in enumerate(zip(layer1.guides, layer2.guides)):
                if guide1.name != guide2.name:
                    differences.append(
                        f"{lpath}.guides[{k}].name: " f"{guide1.name} != {guide2.name}"
                    )
                if guide1.position != guide2.position:
                    differences.append(
                        f"{lpath}.guides[{k}].position: "
                        f"{guide1.position} != {guide2.position}"
                    )
                if guide1.color != guide2.color:
                    differences.append(
                        f"{lpath}.guides[{k}].color: "
                        f"{guide1.color} != {guide2.color}"
                    )

            # Compare shapes
            if len(layer1.shapes) != len(layer2.shapes):
                differences.append(
                    f"{lpath}.shapes length: "
                    f"{len(layer1.shapes)} != {len(layer2.shapes)}"
                )

            for k, (shape1, shape2) in enumerate(zip(layer1.shapes, layer2.shapes)):
                spath = f"{lpath}.shapes[{k}]"
                for attr in ["ref", "transform", "closed"]:
                    val1 = getattr(shape1, attr, None)
                    val2 = getattr(shape2, attr, None)
                    if val1 != val2:
                        differences.append(f"{spath}.{attr}: {val1} != {val2}")

                if shape1.user_data != shape2.user_data:
                    differences.append(
                        f"{spath}.user_data: "
                        f"{shape1.user_data} != "
                        f"{shape2.user_data}"
                    )

                # Compare nodes
                if shape1.nodes and shape2.nodes:
                    if len(shape1.nodes) != len(shape2.nodes):
                        differences.append(
                            f"{spath}.nodes length: "
                            f"{len(shape1.nodes)} != {len(shape2.nodes)}"
                        )

                    for m, (node1, node2) in enumerate(zip(shape1.nodes, shape2.nodes)):
                        npath = f"{spath}.nodes[{m}]"
                        for attr in ["x", "y", "type"]:
                            val1 = getattr(node1, attr)
                            val2 = getattr(node2, attr)
                            if val1 != val2:
                                differences.append(f"{npath}.{attr}: {val1} != {val2}")
                        if node1.user_data != node2.user_data:
                            differences.append(
                                f"{npath}.user_data: "
                                f"{node1.user_data} != "
                                f"{node2.user_data}"
                            )

            # Compare anchors
            if len(layer1.anchors) != len(layer2.anchors):
                differences.append(
                    f"{lpath}.anchors length: "
                    f"{len(layer1.anchors)} != {len(layer2.anchors)}"
                )

            for k, (anchor1, anchor2) in enumerate(zip(layer1.anchors, layer2.anchors)):
                apath = f"{lpath}.anchors[{k}]"
                for attr in ["name", "x", "y"]:
                    val1 = getattr(anchor1, attr)
                    val2 = getattr(anchor2, attr)
                    if val1 != val2:
                        differences.append(f"{apath}.{attr}: {val1} != {val2}")
                if anchor1.user_data != anchor2.user_data:
                    differences.append(
                        f"{apath}.user_data: "
                        f"{anchor1.user_data} != "
                        f"{anchor2.user_data}"
                    )

    return differences


def test_complete_roundtrip(comprehensive_font, tmp_path):
    """Test that a font survives multiple save/load cycles unchanged.

    Note: The first save/load may normalize some values (e.g., I18N dicts
    with single values become plain strings then {"dflt": value}), but
    subsequent cycles should be stable.
    """
    # Save the original font
    path1 = tmp_path / "roundtrip1.babelfont"
    comprehensive_font.save(str(path1))

    # Load it back
    font2 = load(str(path1))

    # Save it again
    path2 = tmp_path / "roundtrip2.babelfont"
    font2.save(str(path2))

    # Load it again
    font3 = load(str(path2))

    # Save a third time
    path3 = tmp_path / "roundtrip3.babelfont"
    font3.save(str(path3))

    # Load a third time
    font4 = load(str(path3))

    # The key test: second and third reloads should be identical
    # (format has stabilized after first normalization)
    diffs_2_3 = compare_fonts(font2, font3, "reload1 vs reload2")
    diffs_3_4 = compare_fonts(font3, font4, "reload2 vs reload3")

    if diffs_2_3:
        print("\nDifferences between reload1 and reload2:")
        for diff in diffs_2_3:
            print(f"  {diff}")

    if diffs_3_4:
        print("\nDifferences between reload2 and reload3:")
        for diff in diffs_3_4:
            print(f"  {diff}")

    # After first normalization, subsequent cycles should be stable
    assert not diffs_2_3, "Font changed between reload1 and reload2"
    assert not diffs_3_4, "Font changed between reload2 and reload3"


def test_field_aliases_in_files(comprehensive_font, tmp_path):
    """Verify that field aliases work correctly in saved files.

    The file format should use 'pos' while Python API uses 'position'.
    """
    # Save the font
    font_path = tmp_path / "alias_test.babelfont"
    comprehensive_font.save(str(font_path))

    # Check that master guides use 'pos' in the file
    info_file = font_path / "info.json"
    with open(info_file, "r") as f:
        info_data = json.load(f)

    master_data = info_data["masters"][0]
    if master_data.get("guides"):
        guide_data = master_data["guides"][0]
        assert "pos" in guide_data, "Master guides should use 'pos' in file"
        assert (
            "position" not in guide_data
        ), "Master guides should not use 'position' in file"

    # Check that layer guides use 'pos' in the file
    glyph_file = font_path / "glyphs" / "A_.nfsglyph"
    with open(glyph_file, "r") as f:
        layers_data = json.load(f)

    layer_data = layers_data[0]
    if layer_data.get("guides"):
        guide_data = layer_data["guides"][0]
        assert "pos" in guide_data, "Layer guides should use 'pos' in file"
        assert (
            "position" not in guide_data
        ), "Layer guides should not use 'position' in file"

    # Verify that loading back works with Python API
    font_loaded = load(str(font_path))
    master = font_loaded.masters[0]
    assert hasattr(master.guides[0], "position"), "Should have 'position' attr"
    assert master.guides[0].position.x == 0, "Position should have correct value"


def testuser_data_roundtrip(comprehensive_font, tmp_path):
    """Verify that user_data data survives roundtrips on all objects."""
    # Save and reload
    font_path = tmp_path / "formatspecific_test.babelfont"
    comprehensive_font.save(str(font_path))
    font_loaded = load(str(font_path))

    # Check font level
    assert font_loaded.user_data == comprehensive_font.user_data

    # Check axis level
    assert font_loaded.axes[0].user_data == {"com.test": "weight-data"}

    # Check instance level
    assert font_loaded.instances[0].user_data == {"com.test": "instance-metadata"}

    # Check master level
    assert font_loaded.masters[0].user_data == {"com.test": {"master": "data"}}

    # Check glyph level
    glyph_a = next(g for g in font_loaded.glyphs if g.name == "A")
    assert glyph_a.user_data == {"com.test": {"glyph": "metadata"}}

    # Check layer level
    assert glyph_a.layers[0].user_data == {"com.test": "layer-data"}

    # Check shape level
    shape = glyph_a.layers[0].shapes[0]
    assert shape.user_data == {"com.test": "shape-metadata"}

    # Check node level (second node has formatspecific)
    node = glyph_a.layers[0].shapes[0].nodes[1]
    assert node.user_data == {"com.test": "node-data"}

    # Check anchor level
    anchor = glyph_a.layers[0].anchors[0]
    assert anchor.user_data == {"com.test": "anchor-data"}

    # Check component level
    glyph_aacute = next(g for g in font_loaded.glyphs if g.name == "Aacute")
    component = glyph_aacute.layers[0].shapes[0]
    assert component.user_data == {"com.test": "component-data"}


def test_node_serialization_formats(tmp_path):
    """Test that nodes serialize in both 3 and 4 element formats correctly."""
    from context import Font, Glyph, Layer, Shape, Node, Master

    font = Font()
    font.initialize_dirty_tracking()
    font.upm = 1000

    master = Master(name={"en": "Regular"}, id="master-1", location={})
    master._set_parent(font)
    font.masters.append(master)

    glyph = Glyph(name="test")
    glyph._set_parent(font)

    layer = Layer(width=500, _master="master-1")
    layer._set_parent(glyph)
    layer._font = font

    # Create shape with mix of nodes (with and without formatspecific)
    shape = Shape(
        nodes=[
            Node(0, 0, "line"),  # 3-element format
            Node(100, 0, "line", _={"key": "value"}),  # 4-element format
            Node(100, 100, "curve"),  # 3-element format
            Node(50, 100, "offcurve"),  # 3-element format
        ],
        closed=True,
    )
    shape._set_parent(layer)
    for node in shape.nodes:
        node._set_parent(shape)
    layer.shapes.append(shape)

    glyph.layers.append(layer)
    font.glyphs.append(glyph)

    # Save and reload
    font_path = tmp_path / "node_format_test.babelfont"
    font.save(str(font_path))

    # Check file format
    glyph_file = font_path / "glyphs" / "test.nfsglyph"
    with open(glyph_file, "r") as f:
        layers_data = json.load(f)

    nodes_data = layers_data[0]["shapes"][0]["nodes"]
    assert len(nodes_data[0]) == 3, "Node without formatspecific should be 3-element"
    assert len(nodes_data[1]) == 4, "Node with formatspecific should be 4-element"
    assert len(nodes_data[2]) == 3, "Node without formatspecific should be 3-element"

    # Load back and verify
    font_loaded = load(str(font_path))
    glyph_loaded = next(g for g in font_loaded.glyphs if g.name == "test")
    nodes_loaded = glyph_loaded.layers[0].shapes[0].nodes

    assert nodes_loaded[0].user_data == {}
    assert nodes_loaded[1].user_data == {"key": "value"}
    assert nodes_loaded[2].user_data == {}


def test_save_without_tracking_identical(comprehensive_font, tmp_path):
    """Test that saving produces identical results with or without tracking.

    This ensures that initialize_dirty_tracking() doesn't affect serialization.
    We load the same font twice: once with tracking (via load()) and once
    without (by temporarily bypassing initialization), then save both and
    verify the output files are identical.
    """
    import context
    from context import Font

    # First: Save the comprehensive font (which has tracking enabled)
    path_original = tmp_path / "original.babelfont"
    comprehensive_font.save(str(path_original))

    # Second: Load it WITH tracking (explicitly initialize)
    font_with_tracking = load(str(path_original))
    font_with_tracking.initialize_dirty_tracking()
    path_with_tracking = tmp_path / "with_tracking.babelfont"
    font_with_tracking.save(str(path_with_tracking))

    # Third: Load it WITHOUT initializing tracking
    font_without_tracking = load(str(path_original))
    # DON'T call font_without_tracking.initialize_dirty_tracking()

    # Save without tracking
    path_no_tracking = tmp_path / "without_tracking.babelfont"
    font_without_tracking.save(str(path_no_tracking))

    # Fourth: Compare the saved files - they should be identical
    import os

    # Compare info.json files
    with open(path_with_tracking / "info.json") as f:
        data_with = json.load(f)
    with open(path_no_tracking / "info.json") as f:
        data_without = json.load(f)

    assert (
        data_with == data_without
    ), "info.json should be identical with/without tracking"

    # Compare names.json files
    with open(path_with_tracking / "names.json") as f:
        names_with = json.load(f)
    with open(path_no_tracking / "names.json") as f:
        names_without = json.load(f)

    assert names_with == names_without, "names.json should be identical"

    # Compare features.fea if present
    features_with = path_with_tracking / "features.fea"
    features_without = path_no_tracking / "features.fea"
    if features_with.exists() and features_without.exists():
        assert (
            features_with.read_text() == features_without.read_text()
        ), "features.fea should be identical"

    # Compare glyph files
    glyphs_dir_with = path_with_tracking / "glyphs"
    glyphs_dir_without = path_no_tracking / "glyphs"

    glyph_files_with = sorted(os.listdir(glyphs_dir_with))
    glyph_files_without = sorted(os.listdir(glyphs_dir_without))

    assert (
        glyph_files_with == glyph_files_without
    ), "Should have same glyph files with/without tracking"

    # Compare each glyph file
    for glyph_file in glyph_files_with:
        with open(glyphs_dir_with / glyph_file) as f:
            glyph_data_with = json.load(f)
        with open(glyphs_dir_without / glyph_file) as f:
            glyph_data_without = json.load(f)

        assert (
            glyph_data_with == glyph_data_without
        ), f"Glyph file {glyph_file} should be identical with/without tracking"

    # Finally: Load both saved versions and verify functionally identical
    font_loaded_with = load(str(path_with_tracking))
    font_loaded_with.initialize_dirty_tracking()
    font_loaded_without = load(str(path_no_tracking))
    font_loaded_without.initialize_dirty_tracking()

    # Use the compare_fonts function from earlier in this file
    diffs = compare_fonts(font_loaded_with, font_loaded_without, "with vs without")

    if diffs:
        print("\nDifferences found between fonts saved with/without tracking:")
        for diff in diffs:
            print(f"  {diff}")

    assert not diffs, "Fonts should be identical regardless of tracking state"
