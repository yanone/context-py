"""Test glyph access by name and index."""

import pytest
from context import Font, Glyph, Layer, Master


@pytest.fixture
def font_with_glyphs():
    """Create a test font with multiple glyphs."""
    font = Font()
    font.upm = 1000

    # Add a master
    master = Master(name={"en": "Regular"}, id="master-1", location={})
    font.masters.append(master)

    # Add glyphs in a specific order
    glyph_names = ["A", "B", "C", "D", "E"]
    for name in glyph_names:
        glyph = Glyph(name=name, category="base", codepoints=[])
        layer = Layer(width=500, _master="master-1")
        glyph.layers.append(layer)
        font.glyphs.append(glyph)

    return font


def test_glyph_access_by_name(font_with_glyphs):
    """Test accessing glyphs by name (existing behavior)."""
    # Access by name should work
    glyph_a = font_with_glyphs.glyphs["A"]
    assert glyph_a.name == "A"
    assert isinstance(glyph_a, Glyph)

    glyph_c = font_with_glyphs.glyphs["C"]
    assert glyph_c.name == "C"

    glyph_e = font_with_glyphs.glyphs["E"]
    assert glyph_e.name == "E"


def test_glyph_access_by_index(font_with_glyphs):
    """Test accessing glyphs by integer index (new behavior)."""
    # Access by index should work
    glyph_0 = font_with_glyphs.glyphs[0]
    assert glyph_0.name == "A"
    assert isinstance(glyph_0, Glyph)

    glyph_1 = font_with_glyphs.glyphs[1]
    assert glyph_1.name == "B"

    glyph_2 = font_with_glyphs.glyphs[2]
    assert glyph_2.name == "C"

    glyph_4 = font_with_glyphs.glyphs[4]
    assert glyph_4.name == "E"


def test_glyph_access_last_index(font_with_glyphs):
    """Test accessing the last glyph using the last valid index."""
    last_index = len(font_with_glyphs.glyphs) - 1
    last_glyph = font_with_glyphs.glyphs[last_index]
    assert last_glyph.name == "E"
    assert isinstance(last_glyph, Glyph)


def test_glyph_access_index_out_of_range(font_with_glyphs):
    """Test that accessing with out-of-range index raises IndexError."""
    with pytest.raises(IndexError, match="out of range"):
        font_with_glyphs.glyphs[100]

    with pytest.raises(IndexError, match="out of range"):
        font_with_glyphs.glyphs[-1]


def test_glyph_access_empty_glyphlist():
    """Test that accessing empty GlyphList raises IndexError."""
    font = Font()
    with pytest.raises(IndexError, match="out of range"):
        font.glyphs[0]


def test_glyph_access_nonexistent_name(font_with_glyphs):
    """Test that accessing non-existent glyph name raises KeyError."""
    with pytest.raises(KeyError):
        font_with_glyphs.glyphs["Z"]


def test_glyph_access_mixed_name_and_index(font_with_glyphs):
    """Test that we can mix name-based and index-based access."""
    # Get by index
    glyph_by_index = font_with_glyphs.glyphs[2]
    # Get by name
    glyph_by_name = font_with_glyphs.glyphs["C"]

    # Should be the same object
    assert glyph_by_index is glyph_by_name
    assert glyph_by_index.name == "C"


def test_glyph_access_iteration_still_works(font_with_glyphs):
    """Test that iteration over glyphs still works correctly."""
    names = [glyph.name for glyph in font_with_glyphs.glyphs]
    assert names == ["A", "B", "C", "D", "E"]


def test_glyph_access_len(font_with_glyphs):
    """Test that len() works correctly on GlyphList."""
    assert len(font_with_glyphs.glyphs) == 5


def test_glyph_access_keys(font_with_glyphs):
    """Test that keys() returns glyph names in order."""
    keys = list(font_with_glyphs.glyphs.keys())
    assert keys == ["A", "B", "C", "D", "E"]


def test_glyph_access_values(font_with_glyphs):
    """Test that values() returns glyph objects in order."""
    values = list(font_with_glyphs.glyphs.values())
    names = [glyph.name for glyph in values]
    assert names == ["A", "B", "C", "D", "E"]


def test_glyph_access_with_tracking(font_with_glyphs):
    """Test that index access works with dirty tracking enabled."""
    # Enable dirty tracking
    font_with_glyphs.initialize_dirty_tracking()

    # Access by index should still work
    glyph = font_with_glyphs.glyphs[2]
    assert glyph.name == "C"
    assert glyph._tracking_enabled

    # Access by name should still work
    glyph2 = font_with_glyphs.glyphs["D"]
    assert glyph2.name == "D"
    assert glyph2._tracking_enabled


def test_glyph_modification_after_index_access(font_with_glyphs):
    """Test that glyphs accessed by index can be modified."""
    # Enable tracking to test modification tracking
    font_with_glyphs.initialize_dirty_tracking()

    # Access by index
    glyph = font_with_glyphs.glyphs[1]
    assert glyph.name == "B"

    # Modify the glyph
    original_category = glyph.category
    glyph.category = "ligature"

    # Verify modification
    assert glyph.category == "ligature"
    assert glyph.category != original_category

    # Access again by name and verify same object
    glyph_by_name = font_with_glyphs.glyphs["B"]
    assert glyph_by_name.category == "ligature"
    assert glyph_by_name is glyph


def test_glyph_index_preserves_order():
    """Test that glyph indices correspond to insertion order."""
    font = Font()
    master = Master(name={"en": "Regular"}, id="master-1", location={})
    font.masters.append(master)

    # Add glyphs in specific order
    names_in_order = ["Z", "A", "M", "B", "Y"]
    for name in names_in_order:
        glyph = Glyph(name=name)
        layer = Layer(width=500, _master="master-1")
        glyph.layers.append(layer)
        font.glyphs.append(glyph)

    # Verify indices match insertion order
    for i, expected_name in enumerate(names_in_order):
        assert font.glyphs[i].name == expected_name
