"""Test round-trip loading and saving of .babelfont files."""

import tempfile
import os
from pathlib import Path
import context


def test_roundtrip_fustat():
    """Test that we can load Fustat.babelfont, save it, and load it again."""
    # Load the original Fustat.babelfont
    test_data_dir = Path(__file__).parent / "data"
    original_file = test_data_dir / "Fustat.babelfont"

    print(f"\n📖 Loading {original_file}")
    font1 = context.load(str(original_file))

    # Verify basic structure is loaded
    assert font1 is not None
    assert len(font1.glyphs) > 0
    assert len(font1.masters) > 0
    assert len(font1.axes) > 0
    assert len(font1.instances) > 0

    # Check that instance names are I18NDictionary
    for instance in font1.instances:
        from context.BaseObject import I18NDictionary

        assert isinstance(
            instance.name, I18NDictionary
        ), f"Instance {instance} name should be I18NDictionary"

    # Check that features have the dict structure
    if font1.features:
        assert hasattr(font1.features, "classes")
        assert hasattr(font1.features, "prefixes")
        assert hasattr(font1.features, "features")
        assert isinstance(font1.features.classes, dict)
        assert isinstance(font1.features.prefixes, dict)
        assert isinstance(font1.features.features, list)

    # Save to a temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "test_output.babelfont")
        print(f"💾 Saving to {temp_file}")
        font1.save(temp_file)

        # Load the saved file
        print(f"📖 Re-loading from {temp_file}")
        font2 = context.load(temp_file)

        # Compare structures
        assert len(font2.glyphs) == len(font1.glyphs), "Glyph count should match"
        assert len(font2.masters) == len(font1.masters), "Master count should match"
        assert len(font2.axes) == len(font1.axes), "Axis count should match"
        assert len(font2.instances) == len(
            font1.instances
        ), "Instance count should match"

        # Compare instance names (I18NDictionary)
        for i, (inst1, inst2) in enumerate(zip(font1.instances, font2.instances)):
            assert (
                inst1.name == inst2.name
            ), f"Instance {i} name mismatch: {inst1.name} != {inst2.name}"

        # Compare axis names (I18NDictionary)
        for i, (axis1, axis2) in enumerate(zip(font1.axes, font2.axes)):
            assert (
                axis1.name == axis2.name
            ), f"Axis {i} name mismatch: {axis1.name} != {axis2.name}"

        # Compare features
        if font1.features:
            assert font2.features is not None, "Features should exist"
            assert len(font2.features.classes) == len(
                font1.features.classes
            ), "Classes count should match"
            assert len(font2.features.prefixes) == len(
                font1.features.prefixes
            ), "Prefixes count should match"
            assert len(font2.features.features) == len(
                font1.features.features
            ), "Features count should match"

        # Sample glyph names to verify
        glyph_names_1 = {g.name for g in font1.glyphs}
        glyph_names_2 = {g.name for g in font2.glyphs}
        assert glyph_names_1 == glyph_names_2, "Glyph names should match"

        print("✅ Round-trip test passed!")


def test_instance_name_i18n():
    """Test that instance names are properly I18NDictionary."""
    test_data_dir = Path(__file__).parent / "data"
    original_file = test_data_dir / "Fustat.babelfont"

    font = context.load(str(original_file))

    from context.BaseObject import I18NDictionary

    for instance in font.instances:
        # Check that name is I18NDictionary
        assert isinstance(
            instance.name, I18NDictionary
        ), f"Instance name should be I18NDictionary, got {type(instance.name)}"

        # Check that we can access the default value
        assert (
            "dflt" in instance.name or len(instance.name) > 0
        ), "Instance name should have at least one language entry"


def test_features_structure():
    """Test that features have the correct dict structure."""
    test_data_dir = Path(__file__).parent / "data"
    original_file = test_data_dir / "Fustat.babelfont"

    font = context.load(str(original_file))

    if font.features:
        # Check structure
        assert isinstance(
            font.features.classes, dict
        ), "Features.classes should be dict"
        assert isinstance(
            font.features.prefixes, dict
        ), "Features.prefixes should be dict"
        assert isinstance(
            font.features.features, list
        ), "Features.features should be list"

        # Check that features is a list of tuples
        for feature_item in font.features.features:
            assert isinstance(
                feature_item, (list, tuple)
            ), f"Feature item should be list/tuple, got {type(feature_item)}"
            assert (
                len(feature_item) == 2
            ), f"Feature item should have 2 elements (tag, code)"


def test_byte_identical_roundtrip():
    """Test that loading and saving produces byte-identical output.

    This ensures that field ordering, date formats, and all other
    serialization details exactly match the babelfont-rs format,
    which is critical for clean git diffs.
    """
    test_data_dir = Path(__file__).parent / "data"
    original_file = test_data_dir / "Fustat.babelfont"

    print(f"\n📖 Loading {original_file}")
    font = context.load(str(original_file))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "roundtrip.babelfont")

        print(f"💾 Writing to {output_file}")
        with open(output_file, "wb") as f:
            font.write(f)

        # Compare file sizes first (quick check)
        orig_size = os.path.getsize(original_file)
        new_size = os.path.getsize(output_file)

        print(f"📊 Original: {orig_size:,} bytes")
        print(f"📊 Roundtrip: {new_size:,} bytes")

        assert (
            orig_size == new_size
        ), f"File sizes differ: {orig_size:,} vs {new_size:,} bytes"

        # Compare binary content
        with open(original_file, "rb") as f1:
            with open(output_file, "rb") as f2:
                original_bytes = f1.read()
                roundtrip_bytes = f2.read()

        # If not identical, find first difference for debugging
        if original_bytes != roundtrip_bytes:
            for i, (a, b) in enumerate(zip(original_bytes, roundtrip_bytes)):
                if a != b:
                    context_start = max(0, i - 40)
                    context_end = min(len(original_bytes), i + 40)
                    orig_context = original_bytes[context_start:context_end]
                    new_context = roundtrip_bytes[context_start:context_end]
                    raise AssertionError(
                        f"Files differ at byte {i}\n"
                        f"Original: {orig_context!r}\n"
                        f"Roundtrip: {new_context!r}"
                    )

        assert (
            original_bytes == roundtrip_bytes
        ), "Files should be byte-identical for clean git diffs"

        print("✅ Byte-identical roundtrip confirmed!")


if __name__ == "__main__":
    test_roundtrip_fustat()
    test_instance_name_i18n()
    test_features_structure()
    test_byte_identical_roundtrip()
    print("\n✅ All tests passed!")
