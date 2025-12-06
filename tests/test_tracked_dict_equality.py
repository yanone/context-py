"""Test TrackedDict equality checking to avoid unnecessary dirty marking."""

from context import Font
from context.BaseObject import DIRTY_FILE_SAVING


def test_tracked_dict_no_dirty_on_same_value():
    """Setting the same value in format_specific should not mark dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    
    # Set initial value
    font.format_specific["mykey"] = "myvalue"
    assert font.is_dirty(DIRTY_FILE_SAVING)
    
    # Mark clean
    font.mark_clean(DIRTY_FILE_SAVING)
    assert not font.is_dirty(DIRTY_FILE_SAVING)
    
    # Set same value again - should NOT mark dirty
    font.format_specific["mykey"] = "myvalue"
    assert not font.is_dirty(DIRTY_FILE_SAVING), "Setting same value should not mark dirty"


def test_tracked_dict_dirty_on_different_value():
    """Setting a different value in format_specific should mark dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    
    # Set initial value
    font.format_specific["mykey"] = "myvalue"
    font.mark_clean(DIRTY_FILE_SAVING)
    
    # Set different value - should mark dirty
    font.format_specific["mykey"] = "newvalue"
    assert font.is_dirty(DIRTY_FILE_SAVING), "Setting different value should mark dirty"


def test_tracked_dict_dirty_on_new_key():
    """Adding a new key in format_specific should mark dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    
    font.format_specific["key1"] = "value1"
    font.mark_clean(DIRTY_FILE_SAVING)
    
    # Add new key - should mark dirty
    font.format_specific["key2"] = "value2"
    assert font.is_dirty(DIRTY_FILE_SAVING), "Adding new key should mark dirty"


def test_tracked_dict_no_dirty_on_same_nested_value():
    """Setting the same nested dict value should not mark dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    
    # Set initial nested value
    font.format_specific["nested"] = {"inner": "value"}
    font.mark_clean(DIRTY_FILE_SAVING)
    
    # Set same nested value again - should NOT mark dirty
    font.format_specific["nested"] = {"inner": "value"}
    assert not font.is_dirty(DIRTY_FILE_SAVING), "Setting same nested value should not mark dirty"


def test_tracked_dict_dirty_on_different_nested_value():
    """Setting a different nested dict value should mark dirty."""
    font = Font()
    font.initialize_dirty_tracking()
    
    # Set initial nested value
    font.format_specific["nested"] = {"inner": "value"}
    font.mark_clean(DIRTY_FILE_SAVING)
    
    # Set different nested value - should mark dirty
    font.format_specific["nested"] = {"inner": "different"}
    assert font.is_dirty(DIRTY_FILE_SAVING), "Setting different nested value should mark dirty"
