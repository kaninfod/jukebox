#!/usr/bin/env python3
"""
Generate album cover thumbnails (180px and 512px) for a single album by ID via SubsonicService.

Usage:
  python scripts/generate_cover_albumid.py <album_id>

The script initializes the app's service container and generates cover variants for the specified album.
"""
import sys
import os
import traceback

# Ensure app package is on path when running from repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.service_container import setup_service_container
from app.config import config

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/generate_cover_albumid.py <album_id>")
        return 1
    album_id = sys.argv[1]
    try:
        container = setup_service_container()
        subsonic = container.get('subsonic_service')
        print(f"Generating covers for album {album_id}...")
        subsonic.ensure_cover_variants(album_id, sizes=(180, 512))
        print(f"Done. Covers stored under: {config.STATIC_FILE_PATH}/covers/{album_id}/cover-<size>.<ext>")
        return 0
    except Exception:
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
