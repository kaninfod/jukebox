import requests
from typing import List, Dict, Any, Optional
from app.services.music_provider_service import MusicProviderService
import logging

logger = logging.getLogger(__name__)


from app.config import config

class SubsonicService(MusicProviderService):
    def __init__(self):
        self.base_url = getattr(config, "SUBSONIC_URL", "http://192.168.68.102:4533").rstrip("/")
        self.username = getattr(config, "SUBSONIC_USER", "jukebox")
        self.password = getattr(config, "SUBSONIC_PASS", "123jukepi")
        self.client = getattr(config, "SUBSONIC_CLIENT", "jukebox")
        self.api_version = getattr(config, "SUBSONIC_API_VERSION", "1.16.1")
        logger.info(f"SubsonicService initialized for {self.base_url} as {self.username}")

    def get_stream_url(self, track: dict) -> str:
        track_id = track.get('video_id')
        if not track_id:
            return None
        # Build Subsonic stream URL
        params = self._api_params()
        url = f"{self.base_url}/rest/stream?id={track_id}&u={params['u']}&p={params['p']}&v={params['v']}&c={params['c']}"
        return url

    def _api_params(self) -> Dict[str, str]:
        return {
            "u": self.username,
            "p": self.password,
            "c": self.client,
            "v": self.api_version,
            "f": "json"
        }

    def _api_request(self, endpoint: str, extra_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        params = self._api_params()
        if extra_params:
            params.update(extra_params)
        url = f"{self.base_url}/rest/{endpoint}"
        logger.info(f"SubsonicService: Requesting {url} with params {params}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    # logger.info(f"SubsonicService: Response: {resp.json()}")  # Commented to reduce excessive logging
        return resp

    
    def search_song(self, query: str) -> Dict[str, Any]:
        logger.info(f"SubsonicService: Searching for song: {query}")
        data = self._api_request("search3", {"query": query})
        data = data.json()
        songs = data.get("searchResult3", {}).get("song", [])
        if not songs:
            logger.warning("SubsonicService: No songs found.")
            raise Exception("No songs found.")
        return songs[0]

    def get_album_tracks(self, audioPlaylistId: str) -> List[Dict[str, Any]]:
        logger.info(f"SubsonicService: Getting album tracks for albumId: {audioPlaylistId}")
        data = self._api_request("getMusicDirectory", {"id": audioPlaylistId})
        data = data.json()
        directory = data.get("subsonic-response", {}).get("directory", {})
        if "child" not in directory:
            logger.warning(f"No tracks found for albumId: {audioPlaylistId}")
            return []
        songs = directory["child"]
        # Filter only song entries (not folders/discs)
        songs = [s for s in songs if not s.get('isDir')]
        logger.info(f"SubsonicService: Found {len(songs)} tracks for albumId: {audioPlaylistId}")
        return songs

    def get_album_info(self, audioPlaylistId: str) -> Dict[str, Any]:
        logger.info(f"SubsonicService: Getting album info for albumId: {audioPlaylistId}")
        data = self._api_request("getAlbum", {"id": audioPlaylistId})
        data = data.json()
        album = data.get("subsonic-response", {}).get("album", {})
        return album

    def list_artists(self) -> list:
        """
        Return a list of all artists from Subsonic (id, name).
        """
        data = self._api_request("getMusicDirectory", {"id": "al-1"})
        data = data.json()
        directory = data.get("subsonic-response", {}).get("directory", {})
        artists = directory.get("child", [])
        # Only include entries where isDir is True (artists are directories)
        return [
            {"id": artist.get("id"), "name": artist.get("title")}
            for artist in artists if artist.get('isDir', False)
        ]

    def list_albums_for_artist(self, artist_id: str) -> list:
        """
        Return a list of all albums for a given artist (id, name).
        """
        # Subsonic: getMusicDirectory with id=artist_id returns albums for that artist
        data = self._api_request("getMusicDirectory", {"id": artist_id})
        data = data.json()
        directory = data.get("subsonic-response", {}).get("directory", {})
        albums = directory.get("child", [])
        # Each album is a dict with 'id' and 'title'
        return [
            {"id": album.get("id"), "name": album.get("title")}
            for album in albums if album.get('isDir', False)
        ]

    def _fetch_and_cache_coverart(self, audioPlaylistId: str, rfid: str) -> Optional[str]:
        """
        Download and cache the album cover image from the given Subsonic coverart URL.
        Returns the filename if successful, else None.
        """

        from PIL import Image
        from io import BytesIO
        import os

        try:
            response = self._api_request("getCoverArt", {"id": audioPlaylistId})

            image = Image.open(BytesIO(response.content))
            image = image.convert('RGBA')
            image = image.resize((120, 120), Image.Resampling.LANCZOS)
            filename = f"{rfid}.png"
            cache_dir = getattr(config, "STATIC_FILE_PATH", "static_files")
            logger.info(f"SubsonicService: Caching album cover art to {cache_dir}")
            local_path = os.path.join(cache_dir, filename)
            image.save(local_path, format='PNG')
            logger.info(f"Cached and processed album cover: {local_path}")
            return filename
        except Exception as e:
            logger.warning(f"Failed to cache album cover from {audioPlaylistId}: {e}")
            return None
        
    def add_or_update_album_entry(self, rfid: str, audioPlaylistId: str):
        """
        Fetch album info from Subsonic, cache the cover, and upsert the album entry in the database.
        Returns the DB entry or None on failure.
        """
        from app.database.album_db import update_album_entry, create_album_entry, get_album_entry_by_rfid
        import json
        try:
            album_info = self.get_album_info(audioPlaylistId)
            #logger.info(f"SubsonicService: Fetched album info for {album_info}")   
            album_name = album_info.get('name', 'Unknown Album')
            artist_name = album_info.get('artist', 'Unknown Artist')
            year = album_info.get('year', None)
            # Subsonic cover art is referenced by coverArt id, fetch and cache the image
            thumbnail_path = self._fetch_and_cache_coverart(audioPlaylistId, rfid)

            # cover_art_id = album_info.get('coverArt')
            # local_cover_filename = None
            # if cover_art_id:
            #     coverart_url = f"{self.base_url}/rest/getCoverArt?id={cover_art_id}&u={self.username}&p={self.password}&v={self.api_version}&c={self.client}"
            #     local_cover_filename = self._fetch_and_cache_coverart(coverart_url, rfid)
            tracks_data = []
            tracks = self.get_album_tracks(audioPlaylistId)
            
            for track in tracks:
                track_info = {
                    'title': track.get('title', 'Unknown Title'),
                    'duration': str(track.get('duration', '0:00')),
                    'track_number': track.get('track', 0),
                    'video_id': track.get('id', '')
                }
                tracks_data.append(track_info)
            album_data = {
                'provider': 'subsonic',
                'album_name': album_name,
                'artist_name': artist_name,
                'year': year,
                'audioPlaylistId': audioPlaylistId,
                'thumbnail': thumbnail_path,
                'tracks': json.dumps(tracks_data)
            }
            # Upsert logic
            logger.info(f"SubsonicService: Upserting album entry for RFID {rfid}: {album_data}")
            db_entry = get_album_entry_by_rfid(rfid)
            
            if db_entry:
                db_entry = update_album_entry(rfid, album_data)
            else:
                create_album_entry(rfid)
                db_entry = update_album_entry(rfid, album_data)
            return db_entry
        except Exception as e:
            logger.error(f"SubsonicService: Failed to add/update album entry for RFID {rfid}: {e}")
            return None
