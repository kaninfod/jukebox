import logging
from app.database.album_db import get_album_entry_by_rfid, create_album_entry, get_album_data_by_audioPlaylistId
from app.core import event_bus, EventType, Event

logger = logging.getLogger(__name__)

class PlaybackManager:
    def __init__(self, screen_manager=None, oauth_file: str = "oauth.json", player=None):
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
        
        event_bus.subscribe(EventType.NEXT_TRACK, self.player.next_track)
        event_bus.subscribe(EventType.TRACK_FINISHED, self.player.next_track)
        event_bus.subscribe(EventType.PREVIOUS_TRACK, self.player.previous_track)
        event_bus.subscribe(EventType.PLAY_PAUSE, self.player.play_pause)
        event_bus.subscribe(EventType.PLAY, self.player.play)
        event_bus.subscribe(EventType.STOP, self.player.stop)
        event_bus.subscribe(EventType.VOLUME_UP, self.player.volume_up)
        event_bus.subscribe(EventType.VOLUME_DOWN, self.player.volume_down)
        event_bus.subscribe(EventType.SET_VOLUME, self.player.set_volume)
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
        elif event.payload['button'] == 4:
            result = self.player.stop()
            logger.info(f"stop: {result}")

    def _handle_rotary_encoder_event(self, event):
        """Handle rotary encoder events for volume control when menu is not active"""
        # Check if menu is currently active - if so, don't handle volume
        try:
            #from app.main import get_screen_manager
            #screen_manager = get_screen_manager()
            #if (screen_manager and 
            #    hasattr(screen_manager, 'menu_controller') and 
            #    screen_manager.menu_controller and 
            #    screen_manager.menu_controller.is_active):
            if (self.screen_manager.menu_controller.is_active):
                return  # Let MenuController handle the event
        except Exception:
            pass  # If we can't check menu state, proceed with volume control
            
        # Handle volume control
        if event.payload['direction'] == 'CW':
            self.player.volume_up()
        elif event.payload['direction'] == 'CCW':
            self.player.volume_down()

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
            # Get the album entry that has this audioPlaylistId
            entry = get_album_data_by_audioPlaylistId(audioPlaylistId)
            
            if not entry:
                logger.info(f"No album entry found for audioPlaylistId: {audioPlaylistId} in database")
                
                # Try to fetch from Subsonic and add to DB
                logger.info(f"Attempting to fetch album {audioPlaylistId} from Subsonic")
                
                try:
                    from app.services.subsonic_service import SubsonicService
                    subsonic_service = SubsonicService()
                    
                    # Fetch album data from Subsonic
                    album_data = subsonic_service.add_or_update_album_entry_from_audioPlaylistId(audioPlaylistId)
                    
                    if not album_data:
                        logger.error(f"Album {audioPlaylistId} not found in Subsonic")
                        return False
                    
                    logger.info(f"Found album in Subsonic: {album_data.get('album_name', 'Unknown Album')}")
                    
                    # Add album to database using existing functions
                    # Create a temporary album entry with a unique identifier
                    import uuid
                    temp_rfid = f"temp_{uuid.uuid4().hex[:8]}"
                    
                    from app.database.album_db import create_album_entry, update_album_entry
                    
                    # Create temporary entry
                    create_result = create_album_entry(temp_rfid)
                    if not create_result:
                        logger.error(f"Failed to create temporary entry for album {audioPlaylistId}")
                        return False
                    
                    # Update with album data
                    db_entry = update_album_entry(temp_rfid, album_data)
                    
                    if not db_entry:
                        logger.error(f"Failed to update database entry for Subsonic album {audioPlaylistId}")
                        return False
                    
                    logger.info(f"Successfully added Subsonic album {audioPlaylistId} to database")
                    
                    # Now get the entry from database
                    entry = get_album_data_by_audioPlaylistId(audioPlaylistId)
                    
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
        entry = get_album_entry_by_rfid(rfid)
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
            
            response = create_album_entry(rfid)
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

