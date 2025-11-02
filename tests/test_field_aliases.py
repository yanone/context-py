"""Test the field aliasing system in BaseObject."""

import io
import json
from context import Guide
from context.BaseObject import Position


def test_guide_serializes_with_pos():
    """Guide should serialize with 'pos' in file format."""
    guide = Guide(position=Position(100, 200, 90), name="test")
    stream = io.BytesIO()
    guide.write(stream)
    result = stream.getvalue().decode("utf-8")

    # Parse JSON to check structure
    data = json.loads(result)
    assert "pos" in data, "Should use 'pos' in file format"
    assert "position" not in data, "Should not have 'position' in file format"
    assert data["pos"] == [100, 200, 90]


def test_guide_loads_from_pos():
    """Guide should load from file format with 'pos'."""
    # Simulate loading from file format
    file_data = {"pos": [100, 200, 90], "name": "test"}
    normalized = Guide._normalize_fields(file_data)

    assert "position" in normalized, "Should convert 'pos' to 'position'"
    assert "pos" not in normalized, "Should not have 'pos' after normalization"

    # Create guide from normalized data
    guide = Guide(**normalized)
    assert guide.position == Position(100, 200, 90)
    assert guide.name == "test"


def test_guide_python_api_uses_position():
    """Python API should use 'position' not 'pos'."""
    guide = Guide(position=Position(50, 100, 0))

    # Accessing via Python API
    assert hasattr(guide, "position")
    assert guide.position == Position(50, 100, 0)

    # Modifying via Python API
    guide.position = Position(150, 250, 45)
    assert guide.position == Position(150, 250, 45)


def test_field_alias_roundtrip():
    """Complete roundtrip: Python API → file format → Python API."""
    # Create using Python API
    original = Guide(position=Position(300, 400, 180), name="baseline")

    # Serialize to file format
    stream = io.BytesIO()
    original.write(stream)
    serialized = stream.getvalue().decode("utf-8")
    file_data = json.loads(serialized)

    # Verify file format uses 'pos'
    assert "pos" in file_data
    assert "position" not in file_data

    # Deserialize back (simulating load from disk)
    normalized = Guide._normalize_fields(file_data)
    reloaded = Guide(**normalized)

    # Verify Python API still works
    assert reloaded.position == original.position
    assert reloaded.name == original.name
