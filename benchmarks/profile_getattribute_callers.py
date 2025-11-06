#!/usr/bin/env python3
"""
Profile to see WHO is calling tracked_getattribute so much.
"""

import cProfile
import pstats
from context import load

# Load Sukoon font
print("Loading Sukoon font...")
font = load("/Users/yanone/Desktop/Sukoon.babelfont")
font.initialize_dirty_tracking()
print(f"Loaded font with {len(font.glyphs)} glyphs")


def small_edit_test():
    """Just edit a few nodes to see the pattern."""
    count = 0
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for shape in layer.shapes:
                if hasattr(shape, "nodes") and shape.nodes is not None:
                    for node in shape.nodes:
                        node.x += 1
                        count += 1
                        if count >= 100:  # Just 100 edits
                            return


print("\nProfiling small edit (100 nodes)...")
print("=" * 80)

# Profile the function
profiler = cProfile.Profile()
profiler.enable()
small_edit_test()
profiler.disable()

# Get stats
stats = pstats.Stats(profiler)
stats.strip_dirs()

# Print callers of tracked_getattribute to understand where it's called from
print("\nCallers of tracked_getattribute:")
print("=" * 80)
stats.print_callers("tracked_getattribute")

print("\n\nDone!")
