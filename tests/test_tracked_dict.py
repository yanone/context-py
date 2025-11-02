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
    """Test that nested dict modifications are now auto-detected."""
    font = Font(_={"com.test": {"nested": "value"}})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    # Nested modification should now be detected when user_data is accessed
    font.user_data["com.test"]["nested"] = "changed"

    # Accessing user_data triggers the nested change detection
    _ = font.user_data
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


def test_user_data_sorted_serialization():
    """Test that user_data keys are sorted alphabetically when serialized."""
    import orjson
    from io import BytesIO

    # Create font with unsorted user_data keys
    font = Font(
        _={
            "z.last": "value1",
            "a.first": "value2",
            "m.middle": "value3",
        }
    )

    # Serialize to stream
    stream = BytesIO()
    font.write(stream, 0)
    serialized = stream.getvalue().decode()

    # Check that keys appear in alphabetical order
    a_pos = serialized.find('"a.first"')
    m_pos = serialized.find('"m.middle"')
    z_pos = serialized.find('"z.last"')

    assert (
        a_pos < m_pos < z_pos
    ), f"Keys not in alphabetical order: a={a_pos}, m={m_pos}, z={z_pos}"

    # Also check direct orjson serialization with sorted keys
    sorted_json = orjson.dumps(font.user_data, option=orjson.OPT_SORT_KEYS)
    assert b'"a.first"' in sorted_json
    assert sorted_json.index(b'"a.first"') < sorted_json.index(b'"m.middle"')
    assert sorted_json.index(b'"m.middle"') < sorted_json.index(b'"z.last"')


def test_user_data_nested_sorted_serialization():
    """Test that nested user_data dicts are also sorted."""
    import orjson
    from context import Node

    # Create node with nested unsorted user_data
    node = Node(
        100,
        200,
        "c",
        _={
            "z.namespace": {"z.key": "val1", "a.key": "val2"},
            "a.namespace": {"z.key": "val3", "a.key": "val4"},
        },
    )

    # Check that both outer and inner keys are sorted
    sorted_json = orjson.dumps(node.user_data, option=orjson.OPT_SORT_KEYS)
    decoded = orjson.loads(sorted_json)

    # Verify outer keys are alphabetically sorted
    keys = list(decoded.keys())
    assert keys == sorted(keys)

    # Verify inner keys are alphabetically sorted
    for value in decoded.values():
        if isinstance(value, dict):
            inner_keys = list(value.keys())
            assert inner_keys == sorted(inner_keys)


def test_tracked_dict_deeply_nested():
    """Test that deeply nested dicts (3+ levels) are tracked."""
    font = Font(_={"level1": {"level2": {"level3": "value"}}})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    from context.BaseObject import TrackedDict

    # Verify all levels are TrackedDict
    assert isinstance(font.user_data["level1"], TrackedDict)
    assert isinstance(font.user_data["level1"]["level2"], TrackedDict)

    # Modify deep nested value
    font.user_data["level1"]["level2"]["level3"] = "modified"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_list_with_dicts():
    """Test that dicts inside lists are converted to TrackedDict."""
    font = Font(_={"items": [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    from context.BaseObject import TrackedDict

    # Verify dicts in list are TrackedDict
    assert isinstance(font.user_data["items"][0], TrackedDict)
    assert isinstance(font.user_data["items"][1], TrackedDict)

    # Modify dict inside list
    font.user_data["items"][0]["name"] = "modified"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_add_nested_dict():
    """Test that newly added nested dicts are automatically converted."""
    font = Font(_={"existing": "value"})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    # Add a new nested dict
    font.user_data["new_nested"] = {"inner": "data"}

    from context.BaseObject import TrackedDict

    assert isinstance(font.user_data["new_nested"], TrackedDict)
    assert font.is_dirty(DIRTY_FILE_SAVING)

    # Modify the newly added nested dict
    font.mark_clean(DIRTY_FILE_SAVING)
    font.user_data["new_nested"]["inner"] = "modified"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_popitem():
    """Test that popitem() marks object dirty."""
    font = Font(_={"key1": "value1", "key2": "value2"})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    assert not font.is_dirty(DIRTY_FILE_SAVING)

    # popitem removes and returns an arbitrary item
    key, value = font.user_data.popitem()

    assert key in ["key1", "key2"]
    assert value in ["value1", "value2"]
    assert font.is_dirty(DIRTY_FILE_SAVING)
    assert len(font.user_data) == 1


def test_tracked_dict_mixed_nested_structures():
    """Test complex nested structures with lists and dicts."""
    font = Font(
        _={
            "config": {"options": [{"enabled": True}, {"enabled": False}]},
            "data": [{"nested": {"deep": "value"}}],
        }
    )
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    from context.BaseObject import TrackedDict

    # Verify nested structures are TrackedDict
    assert isinstance(font.user_data["config"], TrackedDict)
    assert isinstance(font.user_data["config"]["options"][0], TrackedDict)
    assert isinstance(font.user_data["data"][0], TrackedDict)
    assert isinstance(font.user_data["data"][0]["nested"], TrackedDict)

    # Modify deeply nested value
    font.user_data["data"][0]["nested"]["deep"] = "modified"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_nested_empty_dicts():
    """Test that empty nested dicts don't cause issues."""
    font = Font(_={"outer": {}, "nested": {"inner": {}}})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    from context.BaseObject import TrackedDict

    # Empty dicts should still be TrackedDict
    assert isinstance(font.user_data["outer"], TrackedDict)
    assert isinstance(font.user_data["nested"]["inner"], TrackedDict)

    # Adding to empty nested dict should mark dirty
    font.user_data["nested"]["inner"]["key"] = "value"

    assert font.is_dirty(DIRTY_FILE_SAVING)


def test_tracked_dict_non_string_keys():
    """Test that non-string keys (integers, etc.) are supported."""
    font = Font(_={"com.test": {1: "int_key", "2": "string_key"}})
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING)

    from context.BaseObject import TrackedDict

    # Nested dict with int key should be TrackedDict
    assert isinstance(font.user_data["com.test"], TrackedDict)
    assert font.user_data["com.test"][1] == "int_key"
    assert font.user_data["com.test"]["2"] == "string_key"

    # Modifying value with int key should mark dirty
    font.user_data["com.test"][1] = "modified"
    assert font.is_dirty(DIRTY_FILE_SAVING)

    # Adding new int key should work
    font.mark_clean(DIRTY_FILE_SAVING)
    font.user_data["com.test"][3] = "new_int_key"
    assert font.is_dirty(DIRTY_FILE_SAVING)

    # Serialization should work with non-string keys
    import orjson

    # This should not raise TypeError
    serialized = orjson.dumps(
        font.user_data, option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS
    )
    assert serialized is not None


def test_node_serialization_with_non_string_keys():
    """Test that Node serialization works with non-string keys in user_data."""
    from io import BytesIO

    # Create a node with non-string keys in user_data
    node = Node(100, 200, "c", _={"com.test": {1: "value"}})

    # Serialize the node (this should not raise TypeError)
    stream = BytesIO()
    node.write(stream, 0)
    serialized = stream.getvalue().decode()

    # Verify the serialization contains the node data
    assert "100" in serialized
    assert "200" in serialized
    assert serialized.startswith("[")
    assert serialized.endswith("]")

    # Verify it includes the user_data
    assert "com.test" in serialized
