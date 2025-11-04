"""Test that newly created objects get tracking enabled automatically."""

import pytest
from context import (
    Font,
    Glyph,
    Layer,
    Shape,
    Anchor,
    Guide,
    Node,
    Axis,
    Instance,
    Master,
)
from context.BaseObject import DIRTY_FILE_SAVING, DIRTY_CANVAS_RENDER, Position


def test_new_glyph_has_tracking_enabled():
    """When a new glyph is appended to a tracked font, it should get tracking enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    # Create and append a new glyph
    new_glyph = Glyph(name="B")
    font.glyphs.append(new_glyph)

    # Verify tracking is enabled
    assert new_glyph._tracking_enabled
    assert new_glyph._dirty_flags is not None
    assert new_glyph._dirty_fields is not None

    # Verify parent is set
    assert new_glyph._get_parent() == font


def test_new_layer_has_tracking_enabled():
    """Layers now use TrackedList - tracking auto-enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    glyph = Glyph(name="A")
    font.glyphs.append(glyph)

    # Create and append a new layer
    new_layer = Layer(name="Bold", _master="master-bold")
    glyph.layers.append(new_layer)

    # Verify tracking is enabled
    assert new_layer._tracking_enabled
    assert new_layer._dirty_flags is not None
    assert new_layer._dirty_fields is not None

    # Verify parent is set
    assert new_layer._get_parent() == glyph


def test_new_shape_has_tracking_enabled():
    """Shapes now use TrackedList - tracking auto-enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    glyph = Glyph(name="A")
    font.glyphs.append(glyph)

    layer = Layer(name="Regular", _master="master-regular")
    glyph.layers.append(layer)

    # Create and append a new shape
    node1 = Node(x=0, y=0, type="line")
    node2 = Node(x=100, y=0, type="line")
    node3 = Node(x=100, y=100, type="line")
    new_shape = Shape(nodes=[node1, node2, node3], closed=True)
    layer.shapes.append(new_shape)

    # Verify tracking is enabled
    assert new_shape._tracking_enabled
    assert new_shape._dirty_flags is not None
    assert new_shape._dirty_fields is not None

    # Verify parent is set
    assert new_shape._get_parent() == layer


def test_new_anchor_has_tracking_enabled():
    """Anchors now use TrackedList - tracking auto-enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    glyph = Glyph(name="A")
    font.glyphs.append(glyph)

    layer = Layer(name="Regular", _master="master-regular")
    glyph.layers.append(layer)

    # Create and append a new anchor
    new_anchor = Anchor(name="top", x=250, y=700)
    layer.anchors.append(new_anchor)

    # Verify tracking is enabled
    assert new_anchor._tracking_enabled
    assert new_anchor._dirty_flags is not None
    assert new_anchor._dirty_fields is not None

    # Verify parent is set
    assert new_anchor._get_parent() == layer


def test_new_guide_has_tracking_enabled():
    """Guides now use TrackedList - tracking auto-enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    glyph = Glyph(name="A")
    font.glyphs.append(glyph)

    layer = Layer(name="Regular", _master="master-regular")
    glyph.layers.append(layer)

    # Create and append a new guide
    new_guide = Guide(name="baseline", position=Position(x=0, y=0, angle=0))
    layer.guides.append(new_guide)

    # Verify tracking is enabled
    assert new_guide._tracking_enabled
    assert new_guide._dirty_flags is not None
    assert new_guide._dirty_fields is not None

    # Verify parent is set
    assert new_guide._get_parent() == layer


def test_new_axis_has_tracking_enabled():
    """When a new axis is appended to a tracked font, it should get tracking enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    # Create and append a new axis
    new_axis = Axis(tag="wght", name="Weight", minimum=100, default=400, maximum=900)
    font.axes.append(new_axis)

    # Verify tracking is enabled
    assert new_axis._tracking_enabled
    assert new_axis._dirty_flags is not None
    assert new_axis._dirty_fields is not None

    # Verify parent is set
    assert new_axis._get_parent() == font


def test_new_instance_has_tracking_enabled():
    """When a new instance is appended to a tracked font, it should get tracking enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    # Create and append a new instance
    new_instance = Instance(name={"en": "Bold"}, location={"wght": 700})
    font.instances.append(new_instance)

    # Verify tracking is enabled
    assert new_instance._tracking_enabled
    assert new_instance._dirty_flags is not None
    assert new_instance._dirty_fields is not None

    # Verify parent is set
    assert new_instance._get_parent() == font


def test_new_master_has_tracking_enabled():
    """When a new master is appended to a tracked font, it should get tracking enabled."""
    font = Font()
    font.initialize_dirty_tracking()

    # Create and append a new master
    new_master = Master(name={"en": "Bold"}, id="master-bold", location={"wght": 700})
    font.masters.append(new_master)

    # Verify tracking is enabled
    assert new_master._tracking_enabled
    assert new_master._dirty_flags is not None
    assert new_master._dirty_fields is not None

    # Verify parent is set
    assert new_master._get_parent() == font


def test_new_object_marks_parent_dirty():
    """When a new object is appended, it should mark the parent dirty."""
    font = Font()
    font.initialize_dirty_tracking()

    # Mark everything clean
    font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # Append a new glyph
    new_glyph = Glyph(name="B")
    font.glyphs.append(new_glyph)

    # Font should be marked dirty
    assert font.is_dirty(DIRTY_FILE_SAVING)
    assert font.is_dirty(DIRTY_CANVAS_RENDER)


def test_nested_new_objects_mark_owner_dirty():
    """When nested objects created, immediate owner gets marked dirty."""
    font = Font()
    font.initialize_dirty_tracking()

    # Create glyph and layer
    glyph = Glyph(name="A")
    font.glyphs.append(glyph)

    layer = Layer(name="Regular", _master="master-regular")
    glyph.layers.append(layer)

    # Mark everything clean
    font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    glyph.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    assert not font.is_dirty(DIRTY_FILE_SAVING)
    assert not glyph.is_dirty(DIRTY_FILE_SAVING)
    assert not layer.is_dirty(DIRTY_FILE_SAVING)

    # Append a shape to the layer
    node1 = Node(x=0, y=0, type="line")
    node2 = Node(x=100, y=0, type="line")
    node3 = Node(x=100, y=100, type="line")
    shape = Shape(nodes=[node1, node2, node3], closed=True)
    layer.shapes.append(shape)

    # Layer (the immediate owner) should be dirty
    assert layer.is_dirty(DIRTY_FILE_SAVING)


def test_new_object_without_tracking_doesnt_break():
    """Creating objects on a font without tracking should not break."""
    font = Font()
    # Don't initialize tracking

    # Should work without errors
    new_glyph = Glyph(name="B")
    font.glyphs.append(new_glyph)

    # Tracking should not be enabled
    assert not new_glyph._tracking_enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
