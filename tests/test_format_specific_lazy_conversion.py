"""Test that lazy conversion of format_specific doesn't mark dirty."""

from context import load, DIRTY_FILE_SAVING
from pathlib import Path


def test_format_specific_read_doesnt_mark_dirty():
    """
    Test that reading format_specific during font loading doesn't mark
    font dirty.

    This tests the fix for the issue where accessing font.format_specific
    triggered lazy conversion from plain dict to TrackedDict, which
    incorrectly marked the font as dirty even though we were just reading
    data.
    """
    # Load the test font
    test_data_dir = Path(__file__).parent / "data"
    font_path = test_data_dir / "Fustat.babelfont"
    
    print(f"\n📖 Loading {font_path}")
    font = load(str(font_path))
    
    # Initialize tracking (simulates what happens in the webapp)
    font.initialize_dirty_tracking()
    
    # Font should be clean after loading and initialization
    assert not font.is_dirty(DIRTY_FILE_SAVING), \
        "Font should be clean after loading and initialization"
    
    # Now read from format_specific (simulates what the webapp does)
    # This should trigger lazy conversion to TrackedDict but NOT mark dirty
    display_string_key = "com.schriftgestalt.Glyphs.displayStrings"
    
    # Check if the key exists
    if display_string_key in font.format_specific:
        value = font.format_specific[display_string_key]
        print(f"✅ Read display string from font: {value}")
    else:
        print("ℹ️ Display string not in font")
    
    # Font should STILL be clean after reading format_specific
    assert not font.is_dirty(DIRTY_FILE_SAVING), \
        "Font should remain clean after reading format_specific"
    
    print("✅ Test passed: Reading format_specific doesn't mark font dirty")


def test_format_specific_write_does_mark_dirty():
    """
    Test that writing to format_specific DOES mark font dirty.
    
    This ensures the dirty tracking still works correctly for actual changes.
    """
    # Load the test font
    test_data_dir = Path(__file__).parent / "data"
    font_path = test_data_dir / "Fustat.babelfont"
    
    font = load(str(font_path))
    font.initialize_dirty_tracking()
    
    # Font should be clean initially
    assert not font.is_dirty(DIRTY_FILE_SAVING)
    
    # Now WRITE to format_specific - this SHOULD mark dirty
    font.format_specific["test.new_key"] = "new value"
    
    # Font should now be dirty
    assert font.is_dirty(DIRTY_FILE_SAVING), \
        "Font should be marked dirty after writing to format_specific"
    
    print("✅ Test passed: Writing to format_specific marks font dirty")


def test_format_specific_repeated_reads():
    """
    Test that multiple reads of format_specific don't mark dirty.
    """
    # Load the test font
    test_data_dir = Path(__file__).parent / "data"
    font_path = test_data_dir / "Fustat.babelfont"
    
    font = load(str(font_path))
    font.initialize_dirty_tracking()
    
    # Font should be clean initially
    assert not font.is_dirty(DIRTY_FILE_SAVING)
    
    # Read multiple times
    for i in range(5):
        key = "com.schriftgestalt.Glyphs.displayStrings"
        _ = font.format_specific.get(key, [])
    
    # Font should STILL be clean
    assert not font.is_dirty(DIRTY_FILE_SAVING), \
        "Font should remain clean after multiple reads"
    
    print("✅ Test passed: Multiple reads don't mark font dirty")


if __name__ == "__main__":
    test_format_specific_read_doesnt_mark_dirty()
    test_format_specific_write_does_mark_dirty()
    test_format_specific_repeated_reads()
    print("\n✅ All format_specific lazy conversion tests passed!")
