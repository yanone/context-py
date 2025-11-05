"""
Input validation tests for context classes.

Tests type checking and allowed values for property setters.
"""

import pytest
from context import Anchor, Guide, Layer, Node, Shape


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

    def test_x_rejects_none(self):
        """x is a required field and should reject None."""
        node = Node()
        with pytest.raises(ValueError, match="required field and cannot be None"):
            node.x = None

    def test_y_rejects_none(self):
        """y is a required field and should reject None."""
        node = Node()
        with pytest.raises(ValueError, match="required field and cannot be None"):
            node.y = None

    def test_type_rejects_none(self):
        """type is a required field and should reject None."""
        node = Node()
        with pytest.raises(ValueError, match="required field and cannot be None"):
            node.type = None

    def test_type_rejects_empty_string(self):
        """type is a required field and should reject empty string."""
        node = Node()
        with pytest.raises(ValueError, match="required field and cannot be empty"):
            node.type = ""


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


class TestShapeValidation:
    """Test Shape property validation."""

    def test_ref_accepts_valid_string(self):
        """ref should accept string values."""
        shape = Shape()
        shape.ref = "a"
        assert shape.ref == "a"
        shape.ref = ""
        assert shape.ref == ""

    def test_ref_rejects_invalid_types(self):
        """ref should reject non-string types."""
        shape = Shape()
        with pytest.raises(ValueError, match="must be str"):
            shape.ref = 123
        with pytest.raises(ValueError, match="must be str"):
            shape.ref = None

    def test_closed_accepts_valid_bool(self):
        """closed should accept boolean values."""
        shape = Shape()
        shape.closed = True
        assert shape.closed is True
        shape.closed = False
        assert shape.closed is False

    def test_closed_rejects_invalid_types(self):
        """closed should reject non-boolean types."""
        shape = Shape()
        with pytest.raises(ValueError, match="must be bool"):
            shape.closed = 1
        with pytest.raises(ValueError, match="must be bool"):
            shape.closed = "True"

    def test_direction_accepts_valid_values(self):
        """direction should accept 1 or -1."""
        shape = Shape()
        shape.direction = 1
        assert shape.direction == 1
        shape.direction = -1
        assert shape.direction == -1

    def test_direction_rejects_invalid_values(self):
        """direction should reject values other than 1 or -1."""
        shape = Shape()
        with pytest.raises(ValueError, match="must be one of"):
            shape.direction = 0
        with pytest.raises(ValueError, match="must be one of"):
            shape.direction = 2

    def test_direction_rejects_invalid_types(self):
        """direction should reject non-integer types."""
        shape = Shape()
        with pytest.raises(ValueError, match="must be int"):
            shape.direction = 1.0
        with pytest.raises(ValueError, match="must be int"):
            shape.direction = "1"


class TestLayerValidation:
    """Test Layer property validation."""

    def test_width_accepts_valid_int(self):
        """width should accept integer values."""
        layer = Layer()
        layer.width = 600
        assert layer.width == 600
        layer.width = 0
        assert layer.width == 0

    def test_width_rejects_invalid_types(self):
        """width should reject non-integer types including floats."""
        layer = Layer()
        with pytest.raises(ValueError, match="must be int"):
            layer.width = 600.5
        with pytest.raises(ValueError, match="must be int"):
            layer.width = "600"

    def test_height_accepts_valid_int(self):
        """height should accept integer values."""
        layer = Layer()
        layer.height = 800
        assert layer.height == 800
        layer.height = 0
        assert layer.height == 0

    def test_height_rejects_invalid_types(self):
        """height should reject non-integer types including floats."""
        layer = Layer()
        with pytest.raises(ValueError, match="must be int"):
            layer.height = 800.5
        with pytest.raises(ValueError, match="must be int"):
            layer.height = "800"

    def test_vertWidth_accepts_valid_int(self):
        """vertWidth should accept integer values and None."""
        layer = Layer()
        layer.vertWidth = 1000
        assert layer.vertWidth == 1000
        layer.vertWidth = None
        assert layer.vertWidth is None

    def test_vertWidth_rejects_invalid_types(self):
        """vertWidth should reject non-integer types (except None)."""
        layer = Layer()
        with pytest.raises(ValueError, match="must be int"):
            layer.vertWidth = 1000.5
        with pytest.raises(ValueError, match="must be int"):
            layer.vertWidth = "1000"

    def test_name_accepts_valid_string(self):
        """name should accept string values and None."""
        layer = Layer()
        layer.name = "Bold"
        assert layer.name == "Bold"
        layer.name = None
        assert layer.name is None

    def test_name_rejects_invalid_types(self):
        """name should reject non-string types (except None)."""
        layer = Layer()
        with pytest.raises(ValueError, match="must be str"):
            layer.name = 123
        with pytest.raises(ValueError, match="must be str"):
            layer.name = []
