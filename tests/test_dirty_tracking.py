"""Tests for dirty tracking functionality in context-py."""

import pytest
from context import load, DIRTY_FILE_SAVING, DIRTY_CANVAS_RENDER
from context.Font import Font
from context.Glyph import Glyph
from context.Layer import Layer
from context.Shape import Shape
from context.Node import Node
from context.Anchor import Anchor
from context.Guide import Guide
from context.BaseObject import Position
from context.Master import Master
from context.Axis import Axis
from context.Instance import Instance


@pytest.fixture
def font_file(tmp_path):
    """Create a test .babelfont file by building it in memory and saving."""
    from datetime import datetime

    # Create font in memory
    font = Font()
    font.upm = 1000
    font.version = [1, 0]
    font.date = datetime.strptime("2025-11-01 16:00:00", "%Y-%m-%d %H:%M:%S")

    # Set names
    font.names.familyName = {"en": "TestFont"}
    font.names.styleName = {"en": "Regular"}

    # Add axis
    axis = Axis(name="Weight", tag="wght", min=100, max=900, default=400)
    axis._set_parent(font)
    font.axes.append(axis)

    # Add instance
    instance = Instance(name={"en": "Bold"}, location={"wght": 700})
    instance._set_parent(font)
    font.instances.append(instance)

    # Add master
    master = Master(
        name={"en": "Regular"},
        id="master-1",
        location={},
    )
    master._set_parent(font)
    font.masters.append(master)

    # Create glyph A with shapes, anchors, and guides
    glyph_a = Glyph(name="A", category="base", codepoints=[65], exported=True)
    glyph_a._set_parent(font)

    layer_a = Layer(width=600, height=0, _master="master-1")
    layer_a._set_parent(glyph_a)
    layer_a._font = font

    # Add guide to layer
    guide = Guide(name="baseline", position=Position(x=0, y=0, angle=0))
    guide._set_parent(layer_a)
    layer_a.guides.append(guide)

    # Add shape with nodes
    shape = Shape(
        nodes=[
            Node(100, 100, "line"),
            Node(500, 100, "line"),
            Node(500, 700, "line"),
            Node(100, 700, "line"),
        ],
        closed=True,
    )
    shape._set_parent(layer_a)
    layer_a.shapes.append(shape)

    # Add anchor
    anchor = Anchor(name="top", x=300, y=700)
    anchor._set_parent(layer_a)
    layer_a.anchors.append(anchor)

    glyph_a.layers.append(layer_a)
    font.glyphs.append(glyph_a)

    # Create glyph B (simple, will be used as component reference)
    glyph_b = Glyph(name="B", category="base", codepoints=[66], exported=True)
    glyph_b._set_parent(font)

    layer_b = Layer(width=600, height=0, _master="master-1")
    layer_b._set_parent(glyph_b)
    layer_b._font = font

    glyph_b.layers.append(layer_b)
    font.glyphs.append(glyph_b)

    # Create glyph C with component referencing B
    glyph_c = Glyph(name="C", category="base", codepoints=[67], exported=True)
    glyph_c._set_parent(font)

    layer_c = Layer(width=600, height=0, _master="master-1")
    layer_c._set_parent(glyph_c)
    layer_c._font = font

    # Add component (which is a Shape with ref attribute)
    component = Shape(ref="B", transform=[1, 0, 0, 1, 0, 0])
    component._set_parent(layer_c)
    layer_c.shapes.append(component)

    glyph_c.layers.append(layer_c)
    font.glyphs.append(glyph_c)

    # Enable tracking before saving
    font.initialize_dirty_tracking()

    # Save to disk
    font_path = tmp_path / "TestFont.babelfont"
    font.save(str(font_path))

    return font_path


@pytest.fixture
def simple_font(font_file):
    """Load a font from disk for testing."""
    font = load(str(font_file))
    font.initialize_dirty_tracking()
    return font


class TestDirtyFlagBasics:
    """Test basic dirty flag functionality."""

    def test_new_object_has_dirty_tracking(self, simple_font):
        """Loaded objects should have dirty tracking initialized."""
        assert hasattr(simple_font, "_dirty_flags")
        assert hasattr(simple_font, "_dirty_fields")
        assert hasattr(simple_font, "_parent_ref")

    def test_is_dirty_returns_false_when_clean(self, simple_font):
        """Clean objects should report as not dirty."""
        assert not simple_font.is_dirty(DIRTY_FILE_SAVING)
        assert not simple_font.glyphs["A"].is_dirty(DIRTY_FILE_SAVING)

    def test_mark_dirty_sets_flag(self, simple_font):
        """Marking an object dirty should set the flag."""
        glyph = simple_font.glyphs["A"]
        glyph.mark_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)

    def test_mark_clean_clears_flag(self, simple_font):
        """Marking an object clean should clear the flag."""
        glyph = simple_font.glyphs["A"]
        glyph.mark_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        glyph.mark_clean(DIRTY_FILE_SAVING)
        assert not glyph.is_dirty(DIRTY_FILE_SAVING)


class TestMultipleContexts:
    """Test that different contexts can be tracked independently."""

    def test_independent_contexts(self, simple_font):
        """Different contexts should be independent."""
        glyph = simple_font.glyphs["A"]

        glyph.mark_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert not glyph.is_dirty(DIRTY_CANVAS_RENDER)

        glyph.mark_dirty(DIRTY_CANVAS_RENDER)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_CANVAS_RENDER)

    def test_clean_one_context_preserves_others(self, simple_font):
        """Cleaning one context shouldn't affect others."""
        glyph = simple_font.glyphs["A"]

        glyph.mark_dirty(DIRTY_FILE_SAVING)
        glyph.mark_dirty(DIRTY_CANVAS_RENDER)

        glyph.mark_clean(DIRTY_CANVAS_RENDER)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert not glyph.is_dirty(DIRTY_CANVAS_RENDER)


class TestFieldTracking:
    """Test field-level dirty tracking."""

    def test_track_specific_field(self, simple_font):
        """Dirty tracking should record which field changed."""
        glyph = simple_font.glyphs["A"]
        glyph.mark_dirty(DIRTY_FILE_SAVING, field_name="width")

        dirty_fields = glyph.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "width" in dirty_fields

    def test_multiple_fields(self, simple_font):
        """Should track multiple changed fields."""
        glyph = simple_font.glyphs["A"]
        glyph.mark_dirty(DIRTY_FILE_SAVING, field_name="width")
        glyph.mark_dirty(DIRTY_FILE_SAVING, field_name="height")

        dirty_fields = glyph.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "width" in dirty_fields
        assert "height" in dirty_fields


class TestAutomaticTracking:
    """Test automatic dirty tracking on attribute changes."""

    def test_setattr_marks_dirty(self, simple_font):
        """Changing an attribute should automatically mark object dirty."""
        layer = simple_font.glyphs["A"].layers[0]

        # Should be clean initially
        assert not layer.is_dirty(DIRTY_FILE_SAVING)

        # Change attribute
        layer.width = 1000

        # Should now be dirty
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_CANVAS_RENDER)

    def test_setattr_tracks_field(self, simple_font):
        """Automatic tracking should record the field name."""
        layer = simple_font.glyphs["A"].layers[0]
        layer.width = 1000

        dirty_fields = layer.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "width" in dirty_fields

    def test_same_value_no_dirty(self, simple_font):
        """Setting the same value shouldn't mark as dirty."""
        layer = simple_font.glyphs["A"].layers[0]
        original_width = layer.width

        layer.width = original_width
        assert not layer.is_dirty(DIRTY_FILE_SAVING)


class TestParentPropagation:
    """Test that dirty flags propagate up the parent hierarchy."""

    def test_layer_change_propagates_to_glyph(self, simple_font):
        """Changing a layer should mark the glyph dirty."""
        glyph = simple_font.glyphs["A"]
        layer = glyph.layers[0]

        layer.width = 1000

        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)

    def test_layer_change_propagates_to_font(self, simple_font):
        """Changing a layer should mark the font dirty."""
        layer = simple_font.glyphs["A"].layers[0]

        layer.width = 1000

        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

    def test_propagation_without_parent(self, simple_font):
        """Test that changes propagate up the hierarchy."""
        # Get the layer from the loaded font (it has a proper parent)
        glyph = simple_font.glyphs["A"]
        layer = glyph.layers[0]

        # Clear dirty flags first
        simple_font.mark_clean(DIRTY_CANVAS_RENDER, recursive=True)

        # Mark layer dirty - should propagate to glyph and font
        layer.mark_dirty(DIRTY_CANVAS_RENDER, propagate=True)

        # Verify propagation
        assert layer.is_dirty(DIRTY_CANVAS_RENDER)
        assert glyph.is_dirty(DIRTY_CANVAS_RENDER)
        assert simple_font.is_dirty(DIRTY_CANVAS_RENDER)


class TestRecursiveCleaning:
    """Test recursive cleaning of object hierarchies."""

    def test_recursive_clean_clears_children(self, simple_font):
        """Recursive clean should clear all children."""
        layer = simple_font.glyphs["A"].layers[0]
        glyph = simple_font.glyphs["A"]

        # Make changes
        layer.width = 1000

        # Verify dirty
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Clean recursively from font
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # All should be clean
        assert not layer.is_dirty(DIRTY_FILE_SAVING)
        assert not glyph.is_dirty(DIRTY_FILE_SAVING)
        assert not simple_font.is_dirty(DIRTY_FILE_SAVING)

    def test_non_recursive_clean_preserves_children(self, simple_font):
        """Non-recursive clean should only clean the object."""
        layer = simple_font.glyphs["A"].layers[0]
        glyph = simple_font.glyphs["A"]

        layer.width = 1000

        # Clean only the font, not recursively
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=False)

        # Font clean, but children still dirty
        assert not simple_font.is_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_FILE_SAVING)


class TestShapeAndNodeTracking:
    """Test dirty tracking with shapes and nodes."""

    def test_shape_marks_layer_dirty(self, simple_font):
        """Modifying a shape should mark the layer dirty."""
        layer = simple_font.glyphs["A"].layers[0]

        # Clear dirty flags
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify the existing shape
        if layer.shapes:
            shape = layer.shapes[0]
            # Modifying nodes list should mark shape dirty
            shape.nodes = []

            # Layer should be marked dirty
            assert layer.is_dirty(DIRTY_FILE_SAVING)

    def test_node_change_propagates_hierarchy(self, simple_font):
        """Node position changes should propagate up the hierarchy.

        Nodes now inherit from BaseObject and have parent references,
        so modifying node attributes automatically marks the node dirty,
        which propagates through the parent Shape to Layer, Glyph, and Font.
        """
        # Get references to all levels from the loaded font
        font = simple_font
        glyph = font.glyphs["A"]
        layer = glyph.layers[0]

        # The fixture includes a shape with nodes
        assert len(layer.shapes) > 0
        shape = layer.shapes[0]
        assert len(shape.nodes) > 0
        node = shape.nodes[0]

        # Clean everything (loaded fonts start clean for file_saving)
        font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
        assert not node.is_dirty(DIRTY_FILE_SAVING)
        assert not shape.is_dirty(DIRTY_FILE_SAVING)
        assert not layer.is_dirty(DIRTY_FILE_SAVING)
        assert not glyph.is_dirty(DIRTY_FILE_SAVING)
        assert not font.is_dirty(DIRTY_FILE_SAVING)

        # Modify a node's position - this should automatically propagate
        original_x = node.x
        node.x = original_x + 50

        # Verify the node itself is marked dirty
        assert node.is_dirty(DIRTY_FILE_SAVING)

        # Verify propagation up the hierarchy happens automatically
        assert shape.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert glyph.is_dirty(DIRTY_FILE_SAVING)
        assert font.is_dirty(DIRTY_FILE_SAVING)

        # Verify the node field was tracked
        dirty_fields = node.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "x" in dirty_fields


class TestGlyphListTracking:
    """Test that GlyphList tracks changes."""

    def test_append_glyph_marks_font_dirty(self, simple_font):
        """Appending a glyph should mark the font dirty."""
        from context.Glyph import Glyph

        # Font should be clean initially
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
        assert not simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Add a new glyph
        new_glyph = Glyph(name="B")
        new_glyph._set_parent(simple_font)
        simple_font.glyphs.append(new_glyph)

        # Font should now be dirty
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)


class TestParentReferences:
    """Test weak reference parent tracking."""

    def test_parent_reference_is_weak(self, simple_font):
        """Parent references should use weak references."""
        import weakref

        layer = simple_font.glyphs["A"].layers[0]

        assert layer._parent_ref is not None
        assert isinstance(layer._parent_ref, weakref.ref)

    def test_get_parent_returns_object(self, simple_font):
        """_get_parent should dereference the weak reference."""
        glyph = simple_font.glyphs["A"]
        layer = glyph.layers[0]

        parent = layer._get_parent()
        assert parent is glyph

    def test_parent_survives_post_init(self, simple_font):
        """Parent references should survive __post_init__ calls."""
        # This tests the fix for the initialization order issue
        glyph = simple_font.glyphs["A"]
        layer = glyph.layers[0]

        # Parent should be set and valid
        assert layer._get_parent() is not None
        assert layer._get_parent() is glyph


class TestLoadedFontState:
    """Test that loaded fonts have correct initial dirty state."""

    def test_loaded_font_clean_for_file_saving(self, simple_font):
        """Font loaded from disk should be clean for file_saving."""
        # Should be clean for file_saving (matches disk)
        assert not simple_font.is_dirty(DIRTY_FILE_SAVING)
        first_glyph = simple_font.glyphs["A"]
        assert not first_glyph.is_dirty(DIRTY_FILE_SAVING)

    def test_loaded_font_dirty_for_canvas_render(self, simple_font):
        """Font loaded from disk should be dirty for canvas_render."""
        # Should be dirty for canvas_render (needs initial draw)
        assert simple_font.is_dirty(DIRTY_CANVAS_RENDER)


class TestAnchorTracking:
    """Test dirty tracking with anchors."""

    def test_anchor_change_propagates(self, simple_font):
        """Modifying an anchor should mark the layer dirty."""
        layer = simple_font.glyphs["A"].layers[0]

        # Fixture includes an anchor
        assert len(layer.anchors) > 0
        anchor = layer.anchors[0]

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify anchor position
        anchor.x = 400

        # Should propagate: anchor -> layer -> glyph -> font
        assert anchor.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.glyphs["A"].is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = anchor.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "x" in dirty_fields

    def test_anchor_name_change(self, simple_font):
        """Changing anchor name should mark it dirty."""
        layer = simple_font.glyphs["A"].layers[0]
        anchor = layer.anchors[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        anchor.name = "top_modified"

        assert anchor.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = anchor.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "name" in dirty_fields


class TestGuideTracking:
    """Test dirty tracking with guides."""

    def test_guide_change_propagates(self, simple_font):
        """Modifying a guide should mark the layer dirty."""
        from context.BaseObject import Position

        layer = simple_font.glyphs["A"].layers[0]

        # Fixture includes a guide
        assert len(layer.guides) > 0
        guide = layer.guides[0]

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify guide position (Position is immutable, replace entire object)
        guide.position = Position(x=0, y=100, angle=0)

        # Should propagate: guide -> layer -> glyph -> font
        assert guide.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.glyphs["A"].is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = guide.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "position" in dirty_fields

    def test_guide_angle_change(self, simple_font):
        """Changing guide angle should mark it dirty."""
        from context.BaseObject import Position

        layer = simple_font.glyphs["A"].layers[0]
        guide = layer.guides[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Position is immutable, so replace entire object
        guide.position = Position(x=guide.position.x, y=guide.position.y, angle=90)

        assert guide.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = guide.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "position" in dirty_fields


class TestMasterTracking:
    """Test dirty tracking with masters."""

    def test_master_change_propagates(self, simple_font):
        """Modifying a master should mark the font dirty."""
        # Get the master from the font
        assert len(simple_font.masters) > 0
        master = simple_font.masters[0]

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify master name
        master.name = {"en": "Bold"}

        # Should propagate to font
        assert master.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = master.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "name" in dirty_fields

    def test_master_location_change(self, simple_font):
        """Changing master location should mark it dirty."""
        master = simple_font.masters[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify location
        master.location = {"wght": 700}

        assert master.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = master.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "location" in dirty_fields


class TestNamesTracking:
    """Test dirty tracking with font names."""

    def test_names_change_propagates(self, simple_font):
        """Modifying font names should mark the font dirty."""
        names = simple_font.names

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify family name
        names.familyName = {"en": "NewFont"}

        # Should propagate to font
        assert names.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = names.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "familyName" in dirty_fields

    def test_names_style_change(self, simple_font):
        """Changing style name should mark names dirty."""
        names = simple_font.names

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        names.styleName = {"en": "Bold"}

        assert names.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = names.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "styleName" in dirty_fields


class TestAxisTracking:
    """Test dirty tracking with axes."""

    def test_axis_change_propagates(self, simple_font):
        """Modifying an axis should mark the font dirty."""
        # Get the axis from the loaded font
        assert len(simple_font.axes) > 0
        axis = simple_font.axes[0]

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify axis
        axis.max = 1000

        # Should propagate to font
        assert axis.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = axis.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "max" in dirty_fields

    def test_axis_name_change(self, simple_font):
        """Changing axis name should mark it dirty."""
        # Get the axis from the loaded font
        assert len(simple_font.axes) > 0
        axis = simple_font.axes[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        axis.name = "Weight Modified"

        assert axis.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = axis.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "name" in dirty_fields


class TestInstanceTracking:
    """Test dirty tracking with instances."""

    def test_instance_change_propagates(self, simple_font):
        """Modifying an instance should mark the font dirty."""
        # Get the instance from the loaded font
        assert len(simple_font.instances) > 0
        instance = simple_font.instances[0]

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify instance
        instance.location = {"wght": 800}

        # Should propagate to font
        assert instance.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = instance.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "location" in dirty_fields

    def test_instance_name_change(self, simple_font):
        """Changing instance name should mark it dirty."""
        # Get the instance from the loaded font
        assert len(simple_font.instances) > 0
        instance = simple_font.instances[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        instance.name = {"en": "ExtraBold"}

        assert instance.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = instance.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "name" in dirty_fields


class TestComponentTracking:
    """Test dirty tracking with components.

    Note: In context-py, components are Shape objects with a 'ref' attribute.
    """

    def test_component_change_propagates(self, simple_font):
        """Modifying a component should mark the layer dirty."""
        # Glyph C has a component referencing B
        layer = simple_font.glyphs["C"].layers[0]

        # Verify component exists (components are Shape objects with ref attribute)
        assert len(layer.components) > 0
        component = layer.components[0]
        assert component.is_component
        assert component.ref == "B"

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Modify component transformation
        component.transform = [1, 0, 0, 1, 100, 0]

        # Should propagate: component -> layer -> glyph -> font
        assert component.is_dirty(DIRTY_FILE_SAVING)
        assert layer.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.glyphs["C"].is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = component.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "transform" in dirty_fields

    def test_component_ref_change(self, simple_font):
        """Changing component reference should mark it dirty."""
        # Glyph C has a component referencing B
        layer = simple_font.glyphs["C"].layers[0]
        component = layer.components[0]

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        component.ref = "A"

        assert component.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = component.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "ref" in dirty_fields


class TestFeaturesTracking:
    """Test dirty tracking with features."""

    def test_features_change_propagates(self, simple_font):
        """Modifying features should mark the font dirty."""
        features = simple_font.features

        # Clean everything
        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Note: In-place modifications (like .append()) don't trigger
        # __setattr__, so we need to reassign the field to trigger tracking
        new_features = list(features.features)
        new_features.append(("liga", "sub f i by fi;"))
        features.features = new_features

        # Should propagate to font
        assert features.is_dirty(DIRTY_FILE_SAVING)
        assert simple_font.is_dirty(DIRTY_FILE_SAVING)

        # Verify field tracking
        dirty_fields = features.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "features" in dirty_fields

    def test_features_multiple_changes(self, simple_font):
        """Multiple feature changes should be tracked."""
        features = simple_font.features

        simple_font.mark_clean(DIRTY_FILE_SAVING, recursive=True)

        # Reassign to trigger __setattr__
        new_classes = dict(features.classes)
        new_classes["myclass"] = ["A", "B", "C"]
        features.classes = new_classes

        assert features.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = features.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "classes" in dirty_fields

        features.mark_clean(DIRTY_FILE_SAVING)
        assert not features.is_dirty(DIRTY_FILE_SAVING)

        # Another change
        new_prefixes = dict(features.prefixes)
        new_prefixes["myprefix"] = "# New comment"
        features.prefixes = new_prefixes

        assert features.is_dirty(DIRTY_FILE_SAVING)
        dirty_fields = features.get_dirty_fields(DIRTY_FILE_SAVING)
        assert "prefixes" in dirty_fields
