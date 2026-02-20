#!/usr/bin/env python3
"""Test script to debug image rotation issues"""

from PIL import Image
import sys

if len(sys.argv) < 2:
    print("Usage: python test_rotate.py <image_path>")
    sys.exit(1)

img_path = sys.argv[1]
img = Image.open(img_path)

print(f"Original image: {img.size} (width × height)")

# Test rotate with expand=True (removes black padding)
img_rotated = img.rotate(90, expand=True)
print(f"Rotated (expand=True): {img_rotated.size}")

# Save for inspection
img_rotated.save("/tmp/test_rotated.png")
print("Saved to /tmp/test_rotated.png")
