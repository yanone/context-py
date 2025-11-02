#!/usr/bin/env python3
"""Benchmark font loading performance with and without tracking."""
import time
import context

# Test with Sukoon font (large Arabic font with many glyphs)
font_path = "/Users/yanone/Desktop/Sukoon.babelfont"

print(f"Benchmarking: {font_path}")
print("=" * 70)
print()

# Test 1: Load WITH tracking initialization (what editor does)
print("1. Loading WITH initialize_dirty_tracking() (editor behavior)")
print("-" * 70)
times_with_tracking = []
for i in range(5):
    start = time.time()
    font = context.load(font_path)
    font.initialize_dirty_tracking()  # Explicitly initialize tracking
    elapsed = time.time() - start
    times_with_tracking.append(elapsed)
    print(f"  Run {i+1}: {elapsed:.3f}s")

avg_with = sum(times_with_tracking) / len(times_with_tracking)
print(f"  Average: {avg_with:.3f}s")
print(f"  Min: {min(times_with_tracking):.3f}s")
print(f"  Max: {max(times_with_tracking):.3f}s")
print()

# Test 2: Load WITHOUT tracking initialization
print("2. Loading WITHOUT initialize_dirty_tracking() (raw load)")
print("-" * 70)
times_without_tracking = []
for i in range(5):
    start = time.time()
    font = context.load(font_path)  # Just load, no tracking init
    elapsed = time.time() - start
    times_without_tracking.append(elapsed)
    print(f"  Run {i+1}: {elapsed:.3f}s")

avg_without = sum(times_without_tracking) / len(times_without_tracking)
print(f"  Average: {avg_without:.3f}s")
print(f"  Min: {min(times_without_tracking):.3f}s")
print(f"  Max: {max(times_without_tracking):.3f}s")
print()

# Calculate overhead
overhead = avg_with - avg_without
overhead_pct = (overhead / avg_without) * 100 if avg_without > 0 else 0

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Font: {font.names.familyName.get_default()}")
print(f"Glyphs: {len(font.glyphs)}")
print(f"Masters: {len(font.masters)}")
print()
print(f"Average with tracking:    {avg_with:.3f}s")
print(f"Average without tracking: {avg_without:.3f}s")
print(f"Tracking overhead:        {overhead:.3f}s ({overhead_pct:.1f}%)")
print()
print("The overhead includes:")
print("  - Enabling tracking flag on all objects")
print("  - Converting user_data dicts to TrackedDict")
print("  - Initializing dirty tracking structures")
print("  - Setting initial dirty state (DIRTY_CANVAS_RENDER)")
print()

if overhead_pct < 10:
    print(f"✓ Overhead is minimal ({overhead_pct:.1f}%) - optimization successful!")
elif overhead_pct < 20:
    print(f"○ Overhead is acceptable ({overhead_pct:.1f}%)")
else:
    print(f"⚠ Overhead is significant ({overhead_pct:.1f}%) - may need optimization")
