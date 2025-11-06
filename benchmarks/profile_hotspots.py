#!/usr/bin/env python3
"""
Profile coordinate editing to find performance hotspots.
"""

import cProfile
import pstats
from context import load

# Load Sukoon font
print("Loading Sukoon font...")
font = load("/Users/yanone/Desktop/Sukoon.babelfont")
font.initialize_dirty_tracking()
print(f"Loaded font with {len(font.glyphs)} glyphs")

# Count total nodes for reference
total_nodes = 0
for glyph in font.glyphs:
    for layer in glyph.layers:
        for shape in layer.shapes:
            if hasattr(shape, "nodes") and shape.nodes is not None:
                total_nodes += len(shape.nodes)
print(f"Total nodes in font: {total_nodes}")


def coordinate_edit_benchmark():
    """Run one iteration of coordinate editing."""
    # +1 pass
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for shape in layer.shapes:
                if hasattr(shape, "nodes") and shape.nodes is not None:
                    for node in shape.nodes:
                        node.x += 1
                        node.y += 1

    # -1 pass (restore)
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for shape in layer.shapes:
                if hasattr(shape, "nodes") and shape.nodes is not None:
                    for node in shape.nodes:
                        node.x -= 1
                        node.y -= 1


print("\nProfiling coordinate editing...")
print("=" * 80)

# Profile the function
profiler = cProfile.Profile()
profiler.enable()
coordinate_edit_benchmark()
profiler.disable()

# Get stats
stats = pstats.Stats(profiler)
stats.strip_dirs()
stats.sort_stats("cumulative")

# Print top 30 functions by cumulative time
print("\nTop 30 functions by CUMULATIVE time:")
print("=" * 80)
stats.print_stats(30)

# Print top 30 functions by total time (self time)
print("\n\nTop 30 functions by SELF time:")
print("=" * 80)
stats.sort_stats("time")
stats.print_stats(30)

# Print callers for mark_dirty to understand propagation
print("\n\nCallers of mark_dirty:")
print("=" * 80)
stats.print_callers("mark_dirty")

print("\n\nDone!")
