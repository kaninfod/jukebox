
import logging

from app.core import EventType, Event
from typing import List, Dict, Optional
from app.services.appstate import AppStateService, AppState

logger = logging.getLogger(__name__)


class PlaybackManager:
    def __init__(self, screen_manager, player, album_db, subsonic_service, event_bus, appstate_service=None):
        """
        Initialize PlaybackManager with dependency injection.
        
        Args:
            screen_manager: ScreenManager instance for UI control
            player: JukeboxMediaPlayer instance for playback control
            album_db: AlbumDatabase instance for album data operations
            subsonic_service: SubsonicService instance for music provider operations
            event_bus: EventBus instance for event communication
            appstate_service: AppStateService instance for app state management
        """
        # Inject all dependencies
        self.screen_manager = screen_manager
        self.player = player
        self.album_db = album_db
        self.subsonic_service = subsonic_service
        self.event_bus = event_bus
        self.appstate_service = appstate_service
        
        

        # Setup event subscriptions using injected event_bus
        self._setup_event_subscriptions()
        
        logger.info("PlaybackManager initialized with dependency injection.")


    # --- App State Management ---
    def set_app_state(self, state: AppState):
        self.appstate_service.set_app_state(state)

    def get_app_state(self) -> AppState:
        return self.appstate_service.get_app_state()

    def is_encoding_mode_active(self) -> bool:
        return self.appstate_service.is_encoding_mode_active()

    def enable_encoding_mode(self):
        self.appstate_service.enable_encoding_mode()

    def disable_encoding_mode(self):
        self.appstate_service.disable_encoding_mode()
        
    def _setup_event_subscriptions(self):
        """Setup all event subscriptions using injected event_bus"""
        self.event_bus.subscribe(EventType.RFID_READ, self.load_rfid)
        self.event_bus.subscribe(EventType.ENCODE_CARD, self._encode_card)
        self.event_bus.subscribe(EventType.BUTTON_PRESSED, self._handle_button_pressed_event)
        self.event_bus.subscribe(EventType.ROTARY_ENCODER, self._handle_rotary_encoder_event)
        self.event_bus.subscribe(EventType.NEXT_TRACK, self.player.next_track)
        self.event_bus.subscribe(EventType.TRACK_FINISHED, self.player.next_track)
        self.event_bus.subscribe(EventType.PREVIOUS_TRACK, self.player.previous_track)
        self.event_bus.subscribe(EventType.PLAY_PAUSE, self.player.play_pause)
        self.event_bus.subscribe(EventType.PLAY, self.player.play)
        self.event_bus.subscribe(EventType.STOP, self.player.stop)
        self.event_bus.subscribe(EventType.VOLUME_UP, self.player.volume_up)
        self.event_bus.subscribe(EventType.VOLUME_DOWN, self.player.volume_down)
        self.event_bus.subscribe(EventType.SET_VOLUME, self.player.set_volume)
        self.event_bus.subscribe(EventType.PLAY_ALBUM, self._handle_play_album_event)


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
        elif event.payload['button'] == 4:
            # Check if menu is currently active - if so, don't handle stop (let MenuController handle back navigation)
            try:
                if (self.screen_manager.menu_controller.is_active):
                    return  # Let MenuController handle the back navigation
            except Exception:
                pass  # If we can't check menu state, proceed with stop
            result = self.player.stop()
            logger.info(f"stop: {result}")

    def _handle_rotary_encoder_event(self, event):
        """Handle rotary encoder events for volume control when menu is not active"""
        # Check if menu is currently active - if so, don't handle volume
        try:
            if (self.screen_manager.menu_controller.is_active):
                return  # Let MenuController handle the event
        except Exception:
            pass  # If we can't check menu state, proceed with volume control
            
        # Handle volume control
        if event.payload['direction'] == 'CW':
            self.player.volume_up()
        elif event.payload['direction'] == 'CCW':
            self.player.volume_down()

    def _handle_play_album_event(self, event):
        """Handle PLAY_ALBUM event from menu system."""
        album_id = event.payload.get('album_id')
        album_name = event.payload.get('album_name', 'Unknown Album')
        
        if album_id:
            logger.info(f"Playing album from menu: {album_name} (ID: {album_id})")
            success = self.load_from_album_id(album_id)
            if success:
                logger.info(f"Successfully loaded and started playback for album: {album_name}")
            else:
                logger.error(f"Failed to load album: {album_name}")
        else:
            logger.warning("No audioPlaylistId provided in PLAY_ALBUM event")



    def get_stream_url_for_track(self, track: Dict) -> Optional[str]:
        """
        Provider-agnostic stream URL resolver for the current track.
        Returns the stream URL or None if not available.
        """
        from app.core.service_container import get_service
        service = get_service('subsonic_service')
        return service.get_stream_url(track)

    def get_cover_url_for_track(self, album_id: str) -> Optional[str]:
        """
        Cover URL resolver for the current track.
        Returns the cover URL or None if not available.
        """
        from app.core.service_container import get_service
        service = get_service('subsonic_service')
        if album_id:
            # Prefer static 512px cover to maximize cacheability and avoid proxying
            try:
                return service.get_cover_static_url(album_id, size=512, absolute=False)
            except AttributeError:
                # Fallback to proxy if service doesn't support static covers yet
                try:
                    return service.get_cover_proxy_url(album_id)
                except Exception:
                    return f"/api/subsonic/cover/{album_id}"
        else:
            return None

    def load_from_album_id(self, album_id: str) -> bool:
        """
        Load and start playback from an album_id using SubsonicService only.
        Args:
            album_id: The album identifier
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading playlist for album_id: {album_id}")
        try:
            album_info = self.subsonic_service.get_album_info(album_id)
            if not album_info:
                logger.error(f"Album info not found in Subsonic for {album_id}")
                return False
            tracks = self.subsonic_service.get_album_tracks(album_id)
            if not tracks:
                logger.error(f"No tracks found in Subsonic for album_id {album_id}")
                return False

            # Ensure static cover variants exist (180/512). Non-blocking if it fails.
            try:
                self.subsonic_service.ensure_cover_variants(album_id, sizes=(180, 512))
            except Exception:
                pass

            playlist_metadata = []
            for track in tracks:
                stream_url = self.get_stream_url_for_track(track)
                playlist_metadata.append({
                    'title': track.get('title'),
                    'track_id': track.get('id'),
                    'stream_url': stream_url,
                    'duration': str(track.get('duration', 0)),
                    'track_number': track.get('track', 0),
                    'artist': album_info.get('artist', ''),
                    'album': album_info.get('name', ''),
                    'year': album_info.get('year', ''),
                    'thumb': self.get_cover_url_for_track(album_info.get('id')),
                    'album_cover_filename': f"{album_id}"
                })
            logger.info(f"Prepared playlist with {len(playlist_metadata)} tracks for album_id {album_id}")
            self.player.playlist = playlist_metadata
            self.player.current_index = 0
            self.player.play()
            return True
        except Exception as e:
            logger.error(f"Failed to load album_id {album_id}: {e}")
            return False

    def load_rfid(self, event: Event) -> bool:
        """Orchestrate the full playback pipeline from RFID scan using new album DB and SubsonicService, or perform NFC encoding if active."""
        rfid = event.payload['rfid']
        album_id = event.payload['album_id']
        logger.info(f"RFID scan detected: {rfid}")
        logger.info(f"USE THIS ALBUM ID: {album_id}")
        from app.core import event_bus, EventType, Event
        event = Event(EventType.SHOW_SCREEN_QUEUED,
            payload={
                "screen_type": "message",
                "context": {
                    "title": "Getting Album Info...",
                    "icon_name": "contactless.png",
                    "message": "Reading card...",
                    "theme": "message_info"
                },
                "duration": 3
            }
        )
        event_bus.emit(event)

        # Use new album_db for RFID mapping
        
        
        if not album_id:
            logger.info(f"No album info on card, RFID {rfid}")
            album_id = self.album_db.get_album_id_by_rfid(rfid)

        if not album_id:
            logger.info(f"No album mapping found for RFID {rfid} in DB")
            event = Event(EventType.SHOW_SCREEN_QUEUED,
                payload={
                    "screen_type": "message",
                    "context": {
                        "title": "Album Not Found",
                        "icon_name": "error.png",
                        "message": "No album mapped to this RFID. You should fix that!",
                        "theme": "message_info"
                    },
                    "duration": 3
                }
            )
            event_bus.emit(event)

        else:
            logger.info(f"Found album_id {album_id} for RFID {rfid}, loading album...")
            self.load_from_album_id(album_id)

        return True

    def _encode_card(self, event: Event) -> bool:
        """Start an NFC encoding session for the given album_id."""
        from app.core import event_bus, EventType, Event

        try:
            from app.services.nfc_encoding_session import nfc_encoding_session
        except ImportError:
            nfc_encoding_session = None
        if not nfc_encoding_session:
            logger.error("NFC Encoding session service not available.")
            return False
        if nfc_encoding_session.active:
            album_id = nfc_encoding_session.album_id
            rfid = event.payload['rfid']
            logger.info(f"NFC encoding session started for album_id {album_id}")
            self.album_db.set_album_mapping(str(rfid), album_id)
            nfc_encoding_session.complete(rfid)
            self.disable_encoding_mode()
            
            event = Event(EventType.SHOW_SCREEN_QUEUED,
                payload={
                    "screen_type": "message",
                    "context": {
                        "title": "Card Encoded!",
                        "icon_name": "contactless.png",
                        "message": f"RFID {rfid} mapped to album {nfc_encoding_session.album_id}",
                        "theme": "message_success"
                    },
                    "duration": 3
                }
            )
            event_bus.emit(event)
        return True
    
    def cleanup(self):
        logger.info("PlaybackManager cleanup called")