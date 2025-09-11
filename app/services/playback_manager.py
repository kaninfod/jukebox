import logging
from app.core import EventType, Event

logger = logging.getLogger(__name__)

class PlaybackManager:
    def __init__(self, screen_manager, player, album_db, subsonic_service, event_bus):
        """
        Initialize PlaybackManager with dependency injection.
        
        Args:
            screen_manager: ScreenManager instance for UI control
            player: JukeboxMediaPlayer instance for playback control
            album_db: AlbumDatabase instance for album data operations
            subsonic_service: SubsonicService instance for music provider operations
            event_bus: EventBus instance for event communication
        """
        # Inject all dependencies - no more imports needed
        self.screen_manager = screen_manager
        self.player = player
        self.album_db = album_db
        self.subsonic_service = subsonic_service
        self.event_bus = event_bus

        # Setup event subscriptions using injected event_bus
        self._setup_event_subscriptions()
        
        logger.info("PlaybackManager initialized with dependency injection.")
        
    def _setup_event_subscriptions(self):
        """Setup all event subscriptions using injected event_bus"""
        self.event_bus.subscribe(EventType.RFID_READ, self.load_rfid)
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
        audioPlaylistId = event.payload.get('audioPlaylistId')
        album_name = event.payload.get('album_name', 'Unknown Album')
        
        if audioPlaylistId:
            logger.info(f"Playing album from menu: {album_name} (ID: {audioPlaylistId})")
            success = self.load_from_audioPlaylistId(audioPlaylistId)
            if success:
                logger.info(f"Successfully loaded and started playback for album: {album_name}")
            else:
                logger.error(f"Failed to load album: {album_name}")
        else:
            logger.warning("No audioPlaylistId provided in PLAY_ALBUM event")

    def cleanup(self):
        logger.info("PlaybackManager cleanup called")


    def load_from_audioPlaylistId(self, audioPlaylistId: str) -> bool:
        """
        Load and start playback from an audioPlaylistId using Subsonic.
        
        Args:
            audioPlaylistId: The audio playlist identifier
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading playlist for audioPlaylistId: {audioPlaylistId}")
        
        try:
            # Get the album entry that has this audioPlaylistId using injected album_db
            entry = self.album_db.get_album_data_by_audioPlaylistId(audioPlaylistId)
            
            if not entry:
                logger.info(f"No album entry found for audioPlaylistId: {audioPlaylistId} in database")
                
                # Try to fetch from Subsonic and add to DB
                logger.info(f"Attempting to fetch album {audioPlaylistId} from Subsonic")
                
                try:
                    # Use injected subsonic_service instead of creating new instance
                    album_data = self.subsonic_service.add_or_update_album_entry_from_audioPlaylistId(audioPlaylistId)
                    
                    if not album_data:
                        logger.error(f"Album {audioPlaylistId} not found in Subsonic")
                        return False
                    
                    logger.info(f"Found album in Subsonic: {album_data.get('album_name', 'Unknown Album')}")
                    
                    # Add album to database using injected album_db
                    # Create a temporary album entry with a unique identifier
                    import uuid
                    temp_rfid = f"temp_{uuid.uuid4().hex[:8]}"
                    
                    # Create temporary entry using injected album_db
                    create_result = self.album_db.create_album_entry(temp_rfid)
                    if not create_result:
                        logger.error(f"Failed to create temporary entry for album {audioPlaylistId}")
                        return False
                    
                    # Update with album data using injected album_db
                    db_entry = self.album_db.update_album_entry(temp_rfid, album_data)
                    
                    if not db_entry:
                        logger.error(f"Failed to update database entry for Subsonic album {audioPlaylistId}")
                        return False
                    
                    logger.info(f"Successfully added Subsonic album {audioPlaylistId} to database")
                    
                    # Now get the entry from database using injected album_db
                    entry = self.album_db.get_album_data_by_audioPlaylistId(audioPlaylistId)
                    
                    if not entry:
                        logger.error(f"Failed to retrieve newly created entry for {audioPlaylistId}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error fetching album {audioPlaylistId} from Subsonic: {e}")
                    return False
            logger.info(f"Found album entry: {entry}")
            # Use DB data for playlist
            tracks = entry['tracks']
            # If tracks is a JSON string, parse it
            if isinstance(tracks, str):
                import json
                try:
                    tracks = json.loads(tracks)
                except Exception as e:
                    logger.error(f"Failed to parse tracks JSON for audioPlaylistId {audioPlaylistId}: {e}")
                    return False
            
            if not tracks:
                logger.error(f"No tracks found in DB for audioPlaylistId {audioPlaylistId}")
                return False

            playlist_metadata = []
            for track in tracks:
                playlist_metadata.append({
                    'title': track.get('title'),
                    'video_id': track.get('video_id'),
                    'stream_url': None,
                    'duration': track.get('duration'),
                    'track_number': track.get('track_number', track.get('trackNumber', track.get('track', 0))),
                    'artist': entry.get('artist_name', ''),
                    'album': entry.get('album_name', ''),
                    'year': entry.get('year', ''),
                    'album_cover_filename': entry.get('thumbnail', None),
                    'provider': 'subsonic'
                })
            
            logger.info(f"Prepared playlist with {len(playlist_metadata)} tracks for audioPlaylistId {audioPlaylistId}")

            # Load into player and start playback
            self.player.playlist = playlist_metadata
            self.player.current_index = 0
            self.player.play()
            return True
            
        except Exception as e:
            logger.error(f"Failed to load audioPlaylistId {audioPlaylistId}: {e}")
            return False

    def load_rfid(self, event: Event) -> bool:
        """Orchestrate the full playback pipeline from RFID scan."""
        rfid = event.payload['rfid']
        # Use injected album_db instead of direct import
        entry = self.album_db.get_album_entry_by_rfid(rfid)
        if not entry:
             # album does not exist and should be created

            logger.info(f"Nothing found in database {rfid}")
            context = {
                "title": f"New RFID detected.",
                "icon_name": "add_circle",
                "message": f"Creating new entry in the system",
                "background": "#00EAFF",
            }
            from app.ui.screens import MessageScreen
            MessageScreen.show(context)
            
            # Use injected album_db instead of direct import
            response = self.album_db.create_album_entry(rfid)
            if response:
                logger.info(f"Successfully created Album entry for RFID {rfid}")
                return True
            return False
        
        # the database has an entry for the rfid but is has not been associated with an audio playlist
        if not entry.audioPlaylistId:
            logger.info(f"RFID {rfid} has no associated Audio Playlist ID, prompting for new RFID handling.")
            context = {
                "title": f"New RFID detected.",
                "icon_name": "library_music",
                "message": [f"Please assign album in web interface", f"RFID: {rfid}"],
                "theme": "message_info"
            }
            from app.ui.screens import MessageScreen
            MessageScreen.show(context)
            return False
        
        # Bingo! the rfid exists and it is associated with an audio playlist
        else:
            # Delegate to the load_from_audioPlaylistId method
            return self.load_from_audioPlaylistId(entry.audioPlaylistId)

