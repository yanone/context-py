#!/usr/bin/env python3
"""
Benchmark serialization and coordinate editing performance.

Tests:
1. Serialization: Call orjson.dumps(font.to_dict()) 5 times
2. Coordinate edits: Modify all x,y coordinates (+1, then -1) 5 times
"""

import time
import orjson
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

print("\n" + "=" * 60)
print("BENCHMARK 1: Serialization Performance")
print("=" * 60)

# Benchmark 1: Serialization
serialization_times = []
for i in range(5):
    start = time.perf_counter()
    result = orjson.dumps(font.to_dict())
    end = time.perf_counter()
    elapsed = end - start
    serialization_times.append(elapsed)
    print(f"Run {i+1}: {elapsed:.4f} seconds")

avg_serialization = sum(serialization_times) / len(serialization_times)
print(f"\nAverage serialization time: {avg_serialization:.4f} seconds")
print(f"Total time for 5 runs: {sum(serialization_times):.4f} seconds")

print("\n" + "=" * 60)
print("BENCHMARK 2: Coordinate Editing Performance")
print("=" * 60)

# Benchmark 2: Coordinate editing
edit_times = []
for i in range(5):
    start = time.perf_counter()

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

    end = time.perf_counter()
    elapsed = end - start
    edit_times.append(elapsed)
    print(f"Run {i+1}: {elapsed:.4f} seconds")

avg_edit = sum(edit_times) / len(edit_times)
print(f"\nAverage coordinate editing time: {avg_edit:.4f} seconds")
print(f"Total time for 5 runs: {sum(edit_times):.4f} seconds")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Average serialization: {avg_serialization:.4f} seconds")
print(f"Average coord editing: {avg_edit:.4f} seconds")
print(f"Total nodes modified per run: {total_nodes * 2} (x and y)")
