import requests
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SubsonicService:
    def __init__(self, config=None):
        """
        Initialize SubsonicService with dependency injection.
        
        Args:
            config: Configuration object for Subsonic settings
        """
        # Inject config dependency - no more direct import needed
        if config:
            self.config = config
        else:
            # Fallback for backward compatibility - this will be removed later
            from app.config import config as default_config
            self.config = default_config
            
        self.base_url = self.config.SUBSONIC_URL.rstrip("/")
        self.username = getattr(self.config, "SUBSONIC_USER", "jukebox")
        self.password = getattr(self.config, "SUBSONIC_PASS", "123jukepi")
        self.client = getattr(self.config, "SUBSONIC_CLIENT", "jukebox")
        self.api_version = getattr(self.config, "SUBSONIC_API_VERSION", "1.16.1")
        logger.info(f"SubsonicService initialized with dependency injection for {self.base_url} as {self.username}")

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
        resp = requests.get(url, params=params, timeout=self.config.HTTP_REQUEST_TIMEOUT)
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

    def get_alphabetical_groups(self) -> List[Dict[str, str]]:
        """
        Return alphabetical groups for organizing artists.
        
        Returns:
            List of dicts with 'name' and 'range' keys
        """
        return [
            {"name": "A-D", "range": ("A", "D")},
            {"name": "E-H", "range": ("E", "H")},
            {"name": "I-L", "range": ("I", "L")},
            {"name": "M-P", "range": ("M", "P")},
            {"name": "Q-T", "range": ("Q", "T")},
            {"name": "U-Z", "range": ("U", "Z")}
        ]

    def get_artists_in_range(self, start_letter: str, end_letter: str) -> List[Dict[str, Any]]:
        """
        Get all artists whose names start with letters in the given range.
        
        Args:
            start_letter: Starting letter (e.g., 'A')
            end_letter: Ending letter (e.g., 'D')
            
        Returns:
            List of artist dicts with 'id' and 'name'
        """
        if not hasattr(self, '_cached_artists') or not self._cached_artists:
            self._cached_artists = self.list_artists()
        
        filtered_artists = []
        for artist in self._cached_artists:
            name = artist.get('name', '').upper()
            if name and start_letter <= name[0] <= end_letter:
                filtered_artists.append(artist)
        
        # Sort alphabetically
        filtered_artists.sort(key=lambda x: x.get('name', '').upper())
        return filtered_artists

    def cache_artists_data(self) -> None:
        """
        Cache all artists data for faster menu navigation.
        """
        logger.info("Caching artists data from Subsonic...")
        try:
            self._cached_artists = self.list_artists()
            logger.info(f"Cached {len(self._cached_artists)} artists")
        except Exception as e:
            logger.error(f"Failed to cache artists data: {e}")
            self._cached_artists = []

    def _fetch_and_cache_coverart(self, audioPlaylistId: str, filename_prefix: str = None) -> Optional[str]:
        """
        Download and cache the album cover image from Subsonic.
        Returns the filename if successful, else None.
        
        Args:
            audioPlaylistId: The album ID to fetch cover art for
            filename_prefix: Optional prefix for filename (e.g., RFID). If None, uses audioPlaylistId
        """

        from PIL import Image
        from io import BytesIO
        import os

        try:
            response = self._api_request("getCoverArt", {"id": audioPlaylistId})

            image = Image.open(BytesIO(response.content))
            image = image.convert('RGBA')
            image = image.resize((120, 120), Image.Resampling.LANCZOS)
            
            # Use audioPlaylistId as filename if no prefix provided
            if filename_prefix:
                filename = f"{filename_prefix}.png"
            else:
                filename = f"{audioPlaylistId}.png"
                
            # Use injected config instead of direct import
            cache_dir = getattr(self.config, "STATIC_FILE_PATH", "static_files")
            logger.info(f"SubsonicService: Caching album cover art to {cache_dir}")
            local_path = os.path.join(cache_dir, filename)
            image.save(local_path, format='PNG')
            logger.info(f"Cached and processed album cover: {local_path}")
            return filename
        except Exception as e:
            logger.warning(f"Failed to cache album cover from {audioPlaylistId}: {e}")
            return None
        
    def add_or_update_album_entry_from_audioPlaylistId(self, audioPlaylistId: str):
        """
        Fetch album info from Subsonic and create album data structure.
        Returns the album data dict or None on failure.
        This is the core fetching logic without RFID dependency.
        """
        import json
        try:
            album_info = self.get_album_info(audioPlaylistId)
            album_name = album_info.get('name', 'Unknown Album')
            artist_name = album_info.get('artist', 'Unknown Artist')
            year = album_info.get('year', None)
            
            # Fetch and cache cover art using audioPlaylistId as filename
            thumbnail_filename = self._fetch_and_cache_coverart(audioPlaylistId)
            
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
                'thumbnail': thumbnail_filename,  # Now properly set!
                'tracks': json.dumps(tracks_data)
            }
            
            logger.info(f"SubsonicService: Fetched album data for {audioPlaylistId}: {album_name} by {artist_name}")
            return album_data
            
        except Exception as e:
            logger.error(f"SubsonicService: Failed to fetch album data for {audioPlaylistId}: {e}")
            return None

    def add_or_update_album_entry(self, rfid: str, audioPlaylistId: str):
        """
        Fetch album info from Subsonic, cache the cover, and upsert the album entry in the database.
        Returns the DB entry or None on failure.
        """
        from app.database.album_db import update_album_entry, create_album_entry, get_album_entry_by_rfid
        
        try:
            # Get the core album data using the new method
            album_data = self.add_or_update_album_entry_from_audioPlaylistId(audioPlaylistId)
            
            if not album_data:
                logger.error(f"SubsonicService: Failed to fetch album data for {audioPlaylistId}")
                return None
            
            # Add RFID-specific data (cover art caching)
            thumbnail_path = self._fetch_and_cache_coverart(audioPlaylistId, filename_prefix=rfid)
            album_data['thumbnail'] = thumbnail_path
            
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
