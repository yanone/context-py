"""
Input validation tests for context classes.

Tests type checking and allowed values for property setters.
"""

import pytest
from context import Node


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
