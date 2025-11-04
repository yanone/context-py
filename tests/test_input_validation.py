"""
Input validation tests for context classes.

Tests type checking and allowed values for property setters.
"""

import pytest
from context import Anchor, Guide, Node


class TestNodeValidation:
    """Test Node property validation."""

    def test_x_accepts_valid_int(self):
        """x should accept integer values including negatives."""
        node = Node()
        node.x = 100
        assert node.x == 100
        node.x = -50
        assert node.x == -50

    def test_x_rejects_invalid_types(self):
        """x should reject non-integer types."""
        node = Node()
        with pytest.raises(ValueError, match="must be int"):
            node.x = 100.5
        with pytest.raises(ValueError, match="must be int"):
            node.x = "100"

    def test_y_accepts_valid_int(self):
        """y should accept integer values including negatives."""
        node = Node()
        node.y = 200
        assert node.y == 200
        node.y = -100
        assert node.y == -100

    def test_y_rejects_invalid_types(self):
        """y should reject non-integer types."""
        node = Node()
        with pytest.raises(ValueError, match="must be int"):
            node.y = 200.75
        with pytest.raises(ValueError, match="must be int"):
            node.y = "200"

    def test_type_accepts_valid_values(self):
        """type should accept all valid short-form node types."""
        node = Node()
        valid_types = ["o", "os", "c", "cs", "l", "ls", "q", "qs"]
        for node_type in valid_types:
            node.type = node_type
            assert node.type == node_type

    def test_type_rejects_invalid_values(self):
        """type should reject invalid node type values."""
        node = Node()
        with pytest.raises(ValueError, match="must be one of"):
            node.type = "invalid"
        with pytest.raises(ValueError, match="must be one of"):
            node.type = "line"  # Long form not allowed

    def test_type_rejects_invalid_types(self):
        """type should reject non-string types."""
        node = Node()
        with pytest.raises(ValueError, match="must be str"):
            node.type = 123


class TestGuideValidation:
    """Test Guide property validation."""

    def test_name_accepts_valid_string(self):
        """name should accept string values."""
        guide = Guide()
        guide.name = "my-guide"
        assert guide.name == "my-guide"
        guide.name = ""
        assert guide.name == ""

    def test_name_rejects_invalid_types(self):
        """name should reject non-string types."""
        guide = Guide()
        with pytest.raises(ValueError, match="must be str"):
            guide.name = 123
        with pytest.raises(ValueError, match="must be str"):
            guide.name = None

    def test_position_accepts_valid_types(self):
        """position should accept Position/dict/list/tuple with integer x/y."""
        from context import Position

        guide = Guide()

        # Test Position object with integers
        pos = Position(100, 200, 45)
        guide.position = pos
        assert guide.position.x == 100

        # Test list with integers
        guide.position = [150, 250, 90]
        assert guide.position.x == 150

        # Test dict with integers
        guide.position = {"x": 200, "y": 300, "angle": 0}
        assert guide.position.x == 200

    def test_position_rejects_invalid_types(self):
        """position should reject invalid types."""
        guide = Guide()
        with pytest.raises(ValueError, match="must be"):
            guide.position = "invalid"
        with pytest.raises(ValueError, match="must be"):
            guide.position = 123

    def test_position_rejects_float_coordinates(self):
        """position should reject float x/y coordinates."""
        guide = Guide()
        # Dict with float x
        with pytest.raises(ValueError, match="Position x must be int"):
            guide.position = {"x": 100.5, "y": 200, "angle": 0}
        # Dict with float y
        with pytest.raises(ValueError, match="Position y must be int"):
            guide.position = {"x": 100, "y": 200.5, "angle": 0}

    def test_color_accepts_valid_types(self):
        """color should accept Color, dict, list, or tuple."""
        from context import Color

        guide = Guide()

        # Test Color object
        col = Color(255, 0, 0, 128)
        guide.color = col
        assert guide.color.r == 255

        # Test list
        guide.color = [0, 255, 0, 255]
        assert guide.color.g == 255

        # Test dict
        guide.color = {"r": 0, "g": 0, "b": 255, "a": 200}
        assert guide.color.b == 255

    def test_color_rejects_invalid_types(self):
        """color should reject invalid types."""
        guide = Guide()
        with pytest.raises(ValueError, match="must be"):
            guide.color = "invalid"
        with pytest.raises(ValueError, match="must be"):
            guide.color = 123


class TestAnchorValidation:
    """Test Anchor property validation."""

    def test_name_accepts_valid_string(self):
        """name should accept string values."""
        anchor = Anchor()
        anchor.name = "top"
        assert anchor.name == "top"
        anchor.name = ""
        assert anchor.name == ""

    def test_name_rejects_invalid_types(self):
        """name should reject non-string types."""
        anchor = Anchor()
        with pytest.raises(ValueError, match="must be str"):
            anchor.name = 123
        with pytest.raises(ValueError, match="must be str"):
            anchor.name = None

    def test_x_accepts_valid_int(self):
        """x should accept integer values including negatives."""
        anchor = Anchor()
        anchor.x = 100
        assert anchor.x == 100
        anchor.x = -50
        assert anchor.x == -50
        anchor.x = 0
        assert anchor.x == 0

    def test_x_rejects_invalid_types(self):
        """x should reject non-integer types including floats."""
        anchor = Anchor()
        with pytest.raises(ValueError, match="must be int"):
            anchor.x = 100.5
        with pytest.raises(ValueError, match="must be int"):
            anchor.x = "100"
        with pytest.raises(ValueError, match="must be int"):
            anchor.x = None

    def test_y_accepts_valid_int(self):
        """y should accept integer values including negatives."""
        anchor = Anchor()
        anchor.y = 200
        assert anchor.y == 200
        anchor.y = -100
        assert anchor.y == -100
        anchor.y = 0
        assert anchor.y == 0

    def test_y_rejects_invalid_types(self):
        """y should reject non-integer types including floats."""
        anchor = Anchor()
        with pytest.raises(ValueError, match="must be int"):
            anchor.y = 200.75
        with pytest.raises(ValueError, match="must be int"):
            anchor.y = "200"
        with pytest.raises(ValueError, match="must be int"):
            anchor.y = None
