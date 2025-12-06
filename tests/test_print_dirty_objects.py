"""Test print_dirty_objects method."""

from context import Font, Glyph, Layer
from context.BaseObject import DIRTY_FILE_SAVING
import io
import sys


def test_print_dirty_objects_no_changes():
    """Test print_dirty_objects when nothing has changed."""
    font = Font()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    
    # Capture output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    font.print_dirty_objects()
    
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    
    assert "No changes detected" in output


def test_print_dirty_objects_with_changes():
    """Test print_dirty_objects when various objects have changed."""
    font = Font()
    font.initialize_dirty_tracking()
    
    # Add a glyph first
    glyph = Glyph(name="A", codepoints=[65])
    layer = Layer(_master_id="master-1")
    glyph.layers.append(layer)
    font.glyphs.append(glyph)
    
    # Make some changes
    font.upm = 2000
    font.note = "Changed note"
    
    # Mark clean, then make more changes
    font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    
    font.note = "Changed again"
    font.names.family_name = "Test Family"
    
    # Change the glyph that's already in the font
    font.glyphs["A"].codepoints = [65, 0x1F600]
    
    # Capture output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    font.print_dirty_objects()
    
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    
    assert "Dirty Objects Report" in output
    assert "Font:" in output
    assert "Glyphs" in output


def test_print_dirty_objects_without_tracking():
    """Test print_dirty_objects when tracking is not enabled."""
    font = Font()
    
    # Capture output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    font.print_dirty_objects()
    
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    
    assert "not enabled" in output


def test_print_dirty_objects_format_specific():
    """Test that format_specific changes are detected."""
    font = Font()
    font.initialize_dirty_tracking()
    font.mark_clean(DIRTY_FILE_SAVING, recursive=True)
    
    # Change format_specific
    font.format_specific["custom_key"] = "custom_value"
    
    # Capture output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    font.print_dirty_objects()
    
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    
    assert "Font:" in output
    assert "format_specific" in output
