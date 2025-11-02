"""Tests for TrackedDict wrapper that tracks dictionary modifications."""

from context import Font, Glyph, Layer, Node
from context.BaseObject import DIRTY_FILE_SAVING, DIRTY_CANVAS_RENDER


def test_tracked_dict_setitem():
    """Test that setting dict items marks object dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # Set a key in user_data
    font.user_data["com.test"] = "value"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_delitem():
    """Test that deleting dict items marks object dirty."""
    font = Font(_={"com.test": "value"})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # Delete a key from user_data
    del font.user_data["com.test"]

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_update():
    """Test that dict.update() marks object dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # Update with multiple keys
    font.user_data.update({"com.test1": "value1", "com.test2": "value2"})

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_clear():
    """Test that dict.clear() marks object dirty."""
    font = Font(_={"com.test": "value"})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    font.user_data.clear()

    assert font.is_dirty(DIRTY_FILE_SAVING)
    assert len(font.user_data) == 0


def test_tracked_dict_pop():
    """Test that dict.pop() marks object dirty."""
    font = Font(_={"com.test": "value"})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    value = font.user_data.pop("com.test")

    assert value == "value"
    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_setdefault():
    """Test that dict.setdefault() marks object dirty when setting."""
    font = Font()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # setdefault should mark dirty when key doesn't exist
    font.user_data.setdefault("com.test", "default")

    assert font.is_dirty(DIRTY_FILE_SAVING)

    # setdefault should NOT mark dirty when key exists
    font.mark_clean(DIRTY_FILE_SAVING)
    font.user_data.setdefault("com.test", "different")

    assert not font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_nested_modification():
    """Test that nested dict modifications work (but don't auto-track)."""
    font = Font(_={"com.test": {"nested": "value"}})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    # Nested modification won't auto-track (standard Python behavior)
    font.user_data["com.test"]["nested"] = "changed"

    # But the top-level TrackedDict itself wasn't modified
    # Users need to trigger dirty tracking manually or reassign
    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # Reassigning the nested dict triggers tracking
    font.user_data["com.test"] = font.user_data["com.test"]
    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_initialization_with_underscore():
    """Test that _= initialization creates TrackedDict."""
    font = Font(_={"com.test": "value"})
    font.initialize_dirty_tracking()

    from context.BaseObject import TrackedDict

    assert isinstance(font.user_data, TrackedDict)
    assert font.user_data["com.test"] == "value"


def test_tracked_dict_assignment_converts_to_tracked():
    """Test that assigning a regular dict converts to TrackedDict."""
    font = Font()
    font.initialize_dirty_tracking()

    # Assign a regular dict
    font.user_data = {"com.test": "value"}

    from context.BaseObject import TrackedDict

    assert isinstance(font.user_data, TrackedDict)


def test_tracked_dict_on_different_objects():
    """Test TrackedDict on various object types."""
    glyph = Glyph(name="a", _={"com.test": "glyph"})
    layer = Layer(_={"com.test": "layer"})
    node = Node(100, 200, "c", _={"com.test": "node"})

    # Initialize tracking for all objects
    from context.BaseObject import BaseObject

    for obj in [glyph, layer, node]:
        object.__setattr__(obj, "_tracking_enabled", True)
        if obj._dirty_flags is None:
            object.__setattr__(obj, "_dirty_flags", {})
        if obj._dirty_fields is None:
            object.__setattr__(obj, "_dirty_fields", {})
        # Convert user_data to TrackedDict
        from context.BaseObject import TrackedDict

        if isinstance(obj.user_data, dict) and not isinstance(
            obj.user_data, TrackedDict
        ):
            tracked = TrackedDict(owner=obj)
            tracked.update(obj.user_data)
            object.__setattr__(obj, "user_data", tracked)

    from context.BaseObject import TrackedDict

    assert isinstance(glyph.user_data, TrackedDict)
    assert isinstance(layer.user_data, TrackedDict)
    assert isinstance(node.user_data, TrackedDict)

    # Test modifications mark dirty
    glyph.mark_clean(DIRTY_FILE_SAVING)
    layer.mark_clean(DIRTY_FILE_SAVING)
    node.mark_clean(DIRTY_FILE_SAVING)

    glyph.user_data["new"] = "value"
    layer.user_data["new"] = "value"
    node.user_data["new"] = "value"

    assert glyph.is_dirty(DIRTY_FILE_SAVING)
    assert layer.is_dirty(DIRTY_FILE_SAVING)
    assert node.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_preserves_dict_interface():
    """Test that TrackedDict behaves like a normal dict."""
    font = Font(_={"key1": "value1", "key2": "value2"})
    font.initialize_dirty_tracking()

    # Test dict operations
    assert len(font.user_data) == 2
    assert "key1" in font.user_data
    assert "key3" not in font.user_data
    assert list(font.user_data.keys()) == ["key1", "key2"]
    assert list(font.user_data.values()) == ["value1", "value2"]
    assert list(font.user_data.items()) == [("key1", "value1"), ("key2", "value2")]

    # Test iteration
    keys = []
    for key in font.user_data:
        keys.append(key)
    assert keys == ["key1", "key2"]


def test_tracked_dict_multiple_contexts():
    """Test that TrackedDict marks dirty for all relevant contexts."""
    font = Font()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)
    font.mark_clean(DIRTY_CANVAS_RENDER)

    assert not font.is_dirty(DIRTY_FILE_SAVING)
    assert not font.is_dirty(DIRTY_CANVAS_RENDER)

    font.user_data["com.test"] = "value"

    assert font.is_dirty(DIRTY_FILE_SAVING)
    assert font.is_dirty(DIRTY_CANVAS_RENDER)
