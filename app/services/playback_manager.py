import logging
from typing import Optional, List, Dict
from app.database import get_ytmusic_entry_by_rfid, create_ytmusic_entry
from app.services.ytmusic_service import YTMusicService
from app.services.pytube_service import PytubeService

from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
from app.ui.screens.rfid_loading import RfidStatus
from app.services.homeassistant_service import HomeAssistantService
from app.ui.event_bus import ui_event_bus, UIEvent

logger = logging.getLogger(__name__)

class PlaybackManager:
    def __init__(self, screen_manager=None, oauth_file: str = "oauth.json", player=None):
        self.ytmusic_service = YTMusicService()
        self.pytube_service = PytubeService()
        if player is not None:
            self.player = player
        else:
            from app.main import get_jukebox_mediaplayer
            self.player = get_jukebox_mediaplayer()
        self.oauth_file = oauth_file
        self.screen_manager = screen_manager
        ui_event_bus.subscribe(self.handle_event)
        logging.info("PlaybackManager initialized.")

    def handle_event(self, event: UIEvent):
        # All screen changes should be triggered via events and handled here.
        if event.type == 'button_pressed':
            if event.payload['button'] == 1:
                result = self.player.previous_track()
                logger.info(f"Previous track: {result}")
            elif event.payload['button'] == 2:
                result = self.player.play_pause()
                logger.info(f"Play/Pause: {result}")
            elif event.payload['button'] == 3:
                result = self.player.next_track()
                logger.info(f"Next track: {result}")
        elif event.type == 'RotaryEncoder':
            if event.payload['direction'] == 'CW':
                self.player.volume_up()
            elif event.payload['direction'] == 'CCW':
                self.player.volume_down()
        elif event.type == 'ha_state_changed':
            self.player.next_track()
        elif event.type == 'ha_volume_changed':
            # Convert HA volume (0.0-1.0) to percent (0-100)
            ha_volume = event.payload['volume']
            if ha_volume is not None:
                ha_volume_percent = int(round(float(ha_volume) * 100))
                player_volume = self.player.volume
                if abs(ha_volume_percent - player_volume) > 3:
                    self.player.set_volume(ha_volume_percent)

    def cleanup(self):
        logging.info("PlaybackManager cleanup called")
        # Add any additional cleanup logic here if needed

    def load_rfid(self, rfid: str) -> bool:
        """Orchestrate the full playback pipeline from RFID scan."""
        # 1. Fetch yt_id from DB
        logging.info(f"looking up RFID {rfid} in database")
        try:
            entry = get_ytmusic_entry_by_rfid(rfid)
        except Exception as e:
            logging.error(f"Database lookup failed: {e}")
            return False

        if not entry:
            logging.info(f"Nothing found in database {rfid}")
            try:
                response = create_ytmusic_entry(rfid)
            except Exception as e:
                logging.error(f"Failed to create YTMusic entry: {e}")
                return False
            else:
                context = {
                    "status": RfidStatus.NEW_RFID,
                    "rfid_id": f"{rfid}"
                }
                from app.ui.screens.rfid_loading import RfidNewRfidScreen
                RfidNewRfidScreen.show(context)
                return True
        else:
            logger.info(f"Found existing RFID with complete data: {entry.artist_name} - {entry.album_name}")
            yt_id = entry.yt_id
            context = {
                "status": RfidStatus.LOADING_ALBUM,
                "album_name": f"{entry.artist_name} - {entry.album_name}"
            }
            from app.ui.screens.rfid_loading import RfidLoadingScreen
            RfidLoadingScreen.show(context)
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
        # Fetch album cover filename from DB using yt_id
        from app.database import get_ytmusic_data_by_yt_id
        album_cover_filename = None
        if yt_id:
            db_data = get_ytmusic_data_by_yt_id(yt_id)
            if db_data:
                album_cover_filename = db_data.get('thumbnail')

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
                'image_url': album_image_url,
                'yt_id': yt_id,
                'album_cover_filename': album_cover_filename
            })

        # 4. Update the existing JukeboxMediaPlayer's playlist and reset state
        self.player.playlist = playlist_metadata
        self.player.current_index = 0
        logging.debug(f"[PlaybackManager] BEFORE play() player id={id(self.player)} current_volume={getattr(self.player, 'current_volume', None)}")
        self.player.play()
        logging.debug(f"[PlaybackManager] AFTER play() player id={id(self.player)} current_volume={getattr(self.player, 'current_volume', None)}")
        # from app.ui.screens.home import HomeScreen
        # HomeScreen.show()

        return True

