#!/usr/bin/env python3
"""
Pre-generate album cover thumbnails (180px and 512px) for all albums visible via SubsonicService.

Usage:
  python scripts/generate_covers.py

The script initializes the app's service container and walks through artists → albums,
ensuring cover variants exist in static_files/covers/{album_id}/cover-{size}.{ext}.
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
    try:
        container = setup_service_container()
        subsonic = container.get('subsonic_service')
        artists = subsonic.list_artists() or []
        total_albums = 0
        generated = 0
        print(f"Found {len(artists)} artists. Walking albums...")
        for artist in artists:
            albums = subsonic.list_albums_for_artist(artist['id']) or []
            total_albums += len(albums)
            for album in albums:
                aid = album['id']
                try:
                    subsonic.ensure_cover_variants(aid, sizes=(180, 512))
                    generated += 1
                    if generated % 25 == 0:
                        print(f"Processed {generated}/{total_albums} albums...")
                except Exception as e:
                    print(f"WARN: Failed to generate covers for album {aid}: {e}")
        print(f"Done. Processed {generated}/{total_albums} albums.")
        print(f"Covers stored under: {config.STATIC_FILE_PATH}/covers/<album_id>/cover-<size>.<ext>")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
