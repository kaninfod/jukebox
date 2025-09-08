import os
import requests
from typing import Optional, List, Dict, Any
import logging
from ytmusicapi import YTMusic, OAuthCredentials
from app.config import config
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)



# Import the abstract base class for all music providers
from app.services.music_provider_service import MusicProviderService

class YTMusicService(MusicProviderService):
    def get_stream_url(self, track: dict) -> str:
        video_id = track.get('video_id')
        if not video_id:
            return None
        try:
            # Use pytube_service to resolve stream URL from video_id
            return self.pytube_service.get_stream_url(video_id)
        except Exception as e:
            logger.error(f"YTMusicService: Failed to get stream URL for video_id {video_id}: {e}")
            return None
    def __init__(self):
        client_id = config.YTMUSIC_CLIENT_ID
        client_secret = config.YTMUSIC_CLIENT_SECRET
        oauth_file = 'oauth.json'
        self.ytmusic = YTMusic(oauth_file, oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret))
        logger.info("YTMusicService initialized.")


    def add_or_update_album_entry(self, rfid: str, audioPlaylistId: str):
        """
        Fetch album info from YTMusic, cache the cover, and upsert the album entry in the database.
        Returns the DB entry or None on failure.
        """
        from app.database.album_db import update_album_entry, create_album_entry, get_album_entry_by_rfid
        import json
        try:
            browse_id = self.ytmusic.get_album_browse_id(audioPlaylistId)
            album_info = self.ytmusic.get_album(browse_id)
            album_name = album_info.get('title', 'Unknown Album')
            artist_name = 'Unknown Artist'
            if album_info.get('artists') and len(album_info['artists']) > 0:
                artist_name = album_info['artists'][0].get('name', 'Unknown Artist')
            year = album_info.get('year', None)
            thumbnail_url = None
            thumbnails = album_info.get('thumbnails', [])
            for thumb in thumbnails:
                if thumb.get('width') == 120 and thumb.get('height', 120) == 120:
                    thumbnail_url = thumb.get('url')
                    break
            # Download and cache the album cover (use RFID as filename, config for cache path)
            local_cover_filename = self.fetch_and_cache_album_cover(thumbnail_url, rfid) if thumbnail_url else None
            tracks_data = []
            tracks = album_info.get('tracks', [])
            for track in tracks:
                track_info = {
                    'title': track.get('title', 'Unknown Title'),
                    'duration': track.get('duration', '0:00'),
                    'track_number': track.get('trackNumber', 0),
                    'video_id': track.get('videoId', '')
                }
                tracks_data.append(track_info)
            album_data = {
                'album_name': album_name,
                'artist_name': artist_name,
                'year': year,
                'audioPlaylistId': audioPlaylistId,
                'thumbnail': local_cover_filename,
                'tracks': json.dumps(tracks_data)
            }
            # Upsert logic
            db_entry = get_album_entry_by_rfid(rfid)
            if db_entry:
                db_entry = update_album_entry(rfid, album_data)
            else:
                create_album_entry(rfid)
                db_entry = update_album_entry(rfid, album_data)
            return db_entry
        except Exception as e:
            logger.error(f"YTMusicService: Failed to add/update album entry for RFID {rfid}: {e}")
            return None

    @staticmethod
    def fetch_and_cache_album_cover(url: str, rfid: str, cache_dir: Optional[str] = None) -> Optional[str]:
        """
        Download, process (convert to RGBA and resize), and cache the album cover image from the given URL.
        Returns the filename if successful, else None.
        """
        if not url:
            return None
        from app.config import config
        from PIL import Image
        from io import BytesIO
        if cache_dir is None:
            cache_dir = getattr(config, "STATIC_FILE_PATH", "album_covers")
        os.makedirs(cache_dir, exist_ok=True)
        ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
        # If image will be RGBA, use .png extension
        is_png = False
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            image = image.resize((120, 120), Image.Resampling.LANCZOS)
            if image.mode == 'RGBA':
                ext = '.png'
                is_png = True
            filename = f"{rfid}{ext}"
            local_path = os.path.join(cache_dir, filename)
            if is_png:
                image.save(local_path, format='PNG')
            else:
                image = image.convert('RGB')  # JPEG does not support alpha
                image.save(local_path, format='JPEG')
            logger.info(f"Cached and processed album cover: {local_path}")
            return filename
        except Exception as e:
            logger.warning(f"Failed to cache album cover from {url}: {e}")
            return None

    def search_song(self, query: str) -> Dict[str, Any]:
        logger.info(f"YTMusicService: Searching for song: {query}")
        try:
            results = self.ytmusic.search(query, filter="songs")
            if not results:
                logger.warning("YTMusicService: No songs found.")
                raise Exception("No songs found.")
            return results[0]
        except Exception as e:
            logger.error(f"YTMusicService: Error searching for song '{query}': {e}")
            raise

    def get_album_tracks(self, audioPlaylistId: str) -> List[Dict[str, Any]]:
        logger.info(f"YTMusicService: Getting album tracks for audioPlaylistId: {audioPlaylistId}")
        try:
            browse_id = self.ytmusic.get_album_browse_id(audioPlaylistId)
            album_info = self.ytmusic.get_album(browse_id)
            tracks = album_info.get('tracks', [])
            return tracks
        except Exception as e:
            logger.error(f"YTMusicService: Error getting album tracks for audioPlaylistId '{audioPlaylistId}': {e}")
            raise

    def get_album_info(self, audioPlaylistId: str) -> Dict[str, Any]:
        try:
            logger.info(f"YTMusicService: Getting album info for audioPlaylistId: {audioPlaylistId}")
            browse_id = self.ytmusic.get_album_browse_id(audioPlaylistId)
            logger.info(f"YTMusicService: Got album info for audioPlaylistId: {audioPlaylistId}, browse_id: {browse_id}")
            data = self.ytmusic.get_album(browse_id)
            logger.info(f"YTMusicService: Retrieved album info for audioPlaylistId: {data}")
            return data
        except Exception as e:
            logger.error(f"YTMusicService: Error getting album info for audioPlaylistId '{audioPlaylistId}': {e}")
            raise