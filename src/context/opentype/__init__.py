"""
OpenType information and data.

This submodule contains general information about OpenType features, tables,
and specifications.
"""

from .features import (
    DISCRETIONARY_FEATURES,
    DEFAULT_ON_FEATURES,
    REQUIRED_FEATURES,
)

__all__ = [
    "DISCRETIONARY_FEATURES",
    "DEFAULT_ON_FEATURES",
    "REQUIRED_FEATURES",
]
