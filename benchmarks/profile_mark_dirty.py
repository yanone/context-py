#!/usr/bin/env python3
"""
Analyze mark_dirty performance in detail.
"""

import cProfile
import pstats
from context import load

# Load Sukoon font
print("Loading Sukoon font...")
font = load("/Users/yanone/Desktop/Sukoon.babelfont")
font.initialize_dirty_tracking()


def edit_100_nodes():
    """Edit just 100 nodes to see pattern clearly."""
    count = 0
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for shape in layer.shapes:
                if hasattr(shape, "nodes") and shape.nodes is not None:
                    for node in shape.nodes:
                        node.x += 1
                        count += 1
                        if count >= 100:
                            return


print("\nProfiling 100 node edits...")

# Profile
profiler = cProfile.Profile()
profiler.enable()
edit_100_nodes()
profiler.disable()

stats = pstats.Stats(profiler)
stats.strip_dirs()
stats.sort_stats("cumulative")

# Show mark_dirty and its components
print("\n" + "=" * 80)
print("mark_dirty and related functions:")
print("=" * 80)
stats.print_stats("mark_dirty|_get_parent|currentframe|inspect")

print("\n" + "=" * 80)
print("Callers of _get_parent:")
print("=" * 80)
stats.print_callers("_get_parent")

print("\n\nDone!")
