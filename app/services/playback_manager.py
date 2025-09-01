import logging
from typing import Optional, List, Dict
from app.services.ytmusic_service import YTMusicService
from app.services.pytube_service import PytubeService
from app.database.album_db import get_album_entry_by_rfid, create_album_entry
#from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
#from app.services.homeassistant_service import HomeAssistantService
from app.core import event_bus, EventType, Event

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

        event_bus.subscribe(EventType.RFID_READ, self.load_rfid)
        event_bus.subscribe(EventType.BUTTON_PRESSED, self._handle_button_pressed_event)
        event_bus.subscribe(EventType.ROTARY_ENCODER, self._handle_rotary_encoder_event)
        event_bus.subscribe(EventType.HA_STATE_CHANGED, self.player.next_track)
        event_bus.subscribe(EventType.NEXT_TRACK, self.player.next_track)
        event_bus.subscribe(EventType.PREVIOUS_TRACK, self.player.previous_track)
        event_bus.subscribe(EventType.PLAY_PAUSE, self.player.play_pause)
        event_bus.subscribe(EventType.PLAY, self.player.play)
        event_bus.subscribe(EventType.STOP, self.player.stop)
        event_bus.subscribe(EventType.VOLUME_UP, self.player.volume_up)
        event_bus.subscribe(EventType.VOLUME_DOWN, self.player.volume_down)
        event_bus.subscribe(EventType.SET_VOLUME, self.player.set_volume)
        event_bus.subscribe(EventType.HA_VOLUME_CHANGED, self._handle_ha_volume_changed_event)
        #event_bus.subscribe(self.handle_event)
        
        logger.info("PlaybackManager initialized.")


    def _handle_button_pressed_event(self, event):
        if event.payload['button'] == 1:
            result = self.player.previous_track()
            logger.info(f"Previous track: {result}")
        elif event.payload['button'] == 2:
            result = self.player.play_pause()
            logger.info(f"Play/Pause: {result}")
        elif event.payload['button'] == 3:
            result = self.player.next_track(force=True)
            logger.info(f"Next track: {result}")

    def _handle_rotary_encoder_event(self, event):
        if event.payload['direction'] == 'CW':
            self.player.volume_up()
        elif event.payload['direction'] == 'CCW':
            self.player.volume_down()

    def _handle_ha_volume_changed_event(self, event):
        # Convert HA volume (0.0-1.0) to percent (0-100)
        ha_volume = event.payload['volume']
        if ha_volume is not None:
            ha_volume_percent = int(round(float(ha_volume) * 100))
            player_volume = self.player.volume
            if abs(ha_volume_percent - player_volume) > 3:
                self.player.set_volume(ha_volume_percent)

    def cleanup(self):
        logger.info("PlaybackManager cleanup called")


    def load_rfid(self, event: Event) -> bool:
        """Orchestrate the full playback pipeline from RFID scan."""
        rfid = event.payload['rfid']

        # 1. Fetch yt_id from DB
        logger.info(f"looking up RFID {rfid} in database")
        try:
            entry = get_album_entry_by_rfid(rfid)
        except Exception as e:
            logger.error(f"Database lookup failed: {e}")
            return False

        if not entry:
            logger.info(f"Nothing found in database {rfid}")
            try:
                from app.config import config
                file_name = config.get_icon_path("add_circle")
                context = {
                    "title": f"New RFID detected.",
                    "icon_name": file_name,
                    "message": f"Creating new entry in the system",
                    "background": "#00EAFF",
                }
                from app.ui.screens import MessageScreen
                MessageScreen.show(context)

                response = create_album_entry(rfid)
                if response:
                    logger.info(f"Successfully created Album entry for RFID {rfid}")
                    return True
            except Exception as e:
                logger.error(f"Failed to create YTMusic entry: {e}")
                return False
        else:
            if not entry.audioPlaylistId:
                logger.info(f"RFID {rfid} has no associated Audio Playlist ID, prompting for new RFID handling.")
                from app.config import config
                file_name = config.get_icon_path("library_music")
                context = {
                    "title": f"New RFID detected.",
                    "icon_name": file_name,
                    "message": [f"Please assign album in web interface", f"RFID: {rfid}"],
                    "background": "#DF2440",
                }
                from app.ui.screens import MessageScreen
                MessageScreen.show(context)
                return False
            else:
                logger.info(f"Found existing RFID with complete data: {entry.artist_name} - {entry.album_name}")
                audioPlaylistId = entry.audioPlaylistId
                try:
                    from app.config import config
                    #file_name = config.get_icon_path("library_music")
                    file_name = config.get_image_path(f"{rfid}.png")
                    logger.info(f"Loading album: {entry.artist_name} - {entry.album_name} and {file_name}")
                    context = {
                        "title": f"Loading album",
                        "icon_name": file_name,
                        "message": f"{entry.artist_name} - {entry.album_name}",
                        "background": "#2BBE29",
                    }
                    from app.ui.screens import MessageScreen
                    MessageScreen.show(context)
                except Exception as e:
                    logger.error(f"Failed to show loading screen: {e}")

        # 2. Get album/tracks from YTMusicService
        album = self.ytmusic_service.get_album_info(audioPlaylistId)
        tracks = album.get('tracks', [])
        if not tracks:
            logger.error(f"No tracks found for audioPlaylistId {audioPlaylistId}")
            return False

        # Extract album-level info
        album_name = album.get('title', '')
        album_year = album.get('year', '')
        album_cover_filename = entry.thumbnail

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
                # 'image_url': album_image_url,
                'audioPlaylistId': audioPlaylistId,
                'album_cover_filename': album_cover_filename
            })

        # 4. Update the existing JukeboxMediaPlayer's playlist and reset state
        self.player.playlist = playlist_metadata
        self.player.current_index = 0
        self.player.play()
        return True

