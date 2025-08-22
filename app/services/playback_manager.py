import logging
from typing import Optional, List, Dict
from app.database import get_ytmusic_entry_by_rfid
from app.services.ytmusic_service import YTMusicService
from app.services.pytube_service import PytubeService

from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
from app.ui.screens.rfid_loading import RfidStatus
from app.services.homeassistant_service import HomeAssistantService


logger = logging.getLogger(__name__)

class PlaybackManager:
    def __init__(self, screen_manager=None, oauth_file: str = "oauth.json"):
        self.ytmusic_service = YTMusicService()
        self.pytube_service = PytubeService()
        self.player: JukeboxMediaPlayer = JukeboxMediaPlayer([])
        self.oauth_file = oauth_file
        self.screen_manager = screen_manager
        
        logging.info("PlaybackManager initialized.")

    def load_rfid(self, rfid: str) -> bool:
        """Orchestrate the full playback pipeline from RFID scan."""
        # 1. Fetch yt_id from DB
        logging.info(f"looking up RFID {rfid} in database")
        entry = get_ytmusic_entry_by_rfid(rfid)
        
        if not entry:
            logging.info(f"Nothing found in database {rfid}")
            context = {
                "status": RfidStatus.NEW_RFID,
                "rfid_id": f"{rfid}"
            }
            self.screen_manager.show_rfid_loading_screen(context)
            return False
        else:
            logger.info(f"Found existing RFID with complete data: {entry.artist_name} - {entry.album_name}")
            yt_id = entry.yt_id
            context = {
                "status": RfidStatus.LOADING_ALBUM,
                "album_name": f"{entry.artist_name} - {entry.album_name}"
            }
            self.screen_manager.show_rfid_loading_screen(context)
            logging.info(f"RFID {rfid} resolved to yt_id {yt_id}")


        # 2. Get album/tracks from YTMusicService
        album = self.ytmusic_service.get_album_info(yt_id)
        logging.info(f"Fetched album info for yt_id {yt_id}")
        tracks = album.get('tracks', [])
        if not tracks:
            logging.error(f"No tracks found for yt_id {yt_id}")
            return False

        # Extract album-level info
        album_name = album.get('title', '')
        album_year = album.get('year', '')
        # Extract album image URL with width 120 from thumbnails
        album_image_url = ''
        for thumb in album.get('thumbnails', []):
            if thumb.get('width') == 120:
                album_image_url = thumb.get('url', '')
                break

        # 3. Store playlist metadata with all required info (no stream_url)
        playlist_metadata = []
        for track in tracks:
            playlist_metadata.append({
                'title': track.get('title'),
                'video_id': track.get('videoId'),
                'stream_url': None,  # Will be fetched lazily
                'duration': track.get('duration'),
                'track_number': track.get('trackNumber'),
                'artist': track.get('artists', [{}])[0].get('name', ''),
                'album': album_name,
                'year': album_year,
                'image_url': album_image_url
            })

        # 4. Update the existing JukeboxMediaPlayer's playlist and reset state
        self.player.playlist = playlist_metadata
        self.player.current_index = 0
        self.player.status = None
        self.player.play()
        self.screen_manager.show_approaching_screen()

        return True

