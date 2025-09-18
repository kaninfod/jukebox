# Constructor Dependency Injection Example for Jukebox Application

"""
This example shows how to modify the existing jukebox classes to use
constructor dependency injection instead of direct imports.
"""

# =============================================================================
# BEFORE: Current approach with direct imports (High Coupling)
# =============================================================================

class CurrentHardwareManager:
    """Current implementation with direct imports"""
    def __init__(self):
        # These create tight coupling
        from app.config import config
        from app.core.event_bus import event_bus
        self.config = config
        self.event_bus = event_bus
        self.screen_manager = None
        self.playback_manager = None

class CurrentPlaybackManager:
    """Current implementation with direct imports"""
    def __init__(self, screen_manager=None, oauth_file: str = "oauth.json", player=None):
        # These create tight coupling
        from app.database.album_db_old import get_album_entry_by_rfid, create_album_entry
        from app.core import event_bus, EventType, Event
        
        self.player = player or self._get_player_from_main()
        self.screen_manager = screen_manager
        # Direct access to global functions and modules


# =============================================================================
# AFTER: Constructor Dependency Injection (Loose Coupling)
# =============================================================================

class HardwareManager:
    """Modified to accept dependencies via constructor"""
    def __init__(self, config, event_bus):
        # Dependencies injected, no imports needed
        self.config = config
        self.event_bus = event_bus
        self.screen_manager = None
        self.playback_manager = None
        
        # Initialize devices using injected config
        self.devices = {}
        self._initialize_devices()
        
    def _initialize_devices(self):
        """Initialize hardware devices using injected config"""
        # Use self.config instead of importing config
        if self.config.RFID_ENABLED:
            from app.devices.rfid import RFIDReader
            self.devices['rfid'] = RFIDReader(
                config=self.config,
                event_bus=self.event_bus
            )
            
        if self.config.DISPLAY_ENABLED:
            from app.devices.ili9488 import ILI9488Display
            self.devices['display'] = ILI9488Display(
                config=self.config
            )


class ScreenManager:
    """Modified to accept dependencies via constructor"""
    def __init__(self, display, event_bus):
        # Dependencies injected, no imports needed
        self.display = display
        self.event_bus = event_bus
        self.current_screen = None
        self.screens = {}
        
        # Subscribe to events using injected event_bus
        self._setup_event_subscriptions()
        
    def _setup_event_subscriptions(self):
        """Setup event subscriptions using injected event_bus"""
        from app.core import EventType
        self.event_bus.subscribe(EventType.SHOW_IDLE, self.show_idle_screen)
        self.event_bus.subscribe(EventType.SHOW_MESSAGE, self.show_message_screen)
        # ... other subscriptions


class PlaybackManager:
    """Modified to accept all dependencies via constructor"""
    def __init__(self, screen_manager, player, album_db, subsonic_service, event_bus):
        # All dependencies injected, no imports needed
        self.screen_manager = screen_manager
        self.player = player
        self.album_db = album_db
        self.subsonic_service = subsonic_service
        self.event_bus = event_bus
        
        # Setup event subscriptions using injected event_bus
        self._setup_event_subscriptions()
        
    def _setup_event_subscriptions(self):
        """Setup all event subscriptions using injected event_bus"""
        from app.core import EventType
        
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
        
    def load_rfid(self, event):
        """Load album using injected album_db instead of direct import"""
        rfid_uid = event.data
        
        # Use injected album_db instead of importing functions
        album_entry = self.album_db.get_album_entry_by_rfid(rfid_uid)
        
        if album_entry:
            self.load_from_audioPlaylistId(album_entry['audioPlaylistId'])
        else:
            # Use injected subsonic_service to search for albums
            albums = self.subsonic_service.search_albums(query="")
            # Handle new RFID card logic...
            
    def load_from_audioPlaylistId(self, audioPlaylistId):
        """Load album using injected services"""
        # Use injected album_db
        album_data = self.album_db.get_album_data_by_audioPlaylistId(audioPlaylistId)
        
        if album_data:
            # Use injected subsonic_service
            tracks = self.subsonic_service.get_album_tracks(audioPlaylistId)
            self.player.load_playlist(tracks)


class JukeboxMediaPlayer:
    """Modified to accept dependencies via constructor"""
    def __init__(self, tracks, event_bus, chromecast_service=None):
        # Dependencies injected, no imports needed
        self.tracks = tracks
        self.event_bus = event_bus
        self.chromecast_service = chromecast_service
        self.current_track_index = 0
        self.is_playing = False
        
    def play(self):
        """Play using injected chromecast_service"""
        if self.chromecast_service and self.tracks:
            current_track = self.tracks[self.current_track_index]
            self.chromecast_service.play_track(current_track)
            self.is_playing = True
            
            # Emit event using injected event_bus
            from app.core import EventType, Event
            self.event_bus.emit(EventType.TRACK_CHANGED, Event(
                event_type=EventType.TRACK_CHANGED,
                data=current_track
            ))


class SubsonicService:
    """Modified to accept dependencies via constructor"""
    def __init__(self, config):
        # Config injected, no direct import
        self.config = config
        self.base_url = config.SUBSONIC_URL
        self.username = config.SUBSONIC_USERNAME
        self.password = config.SUBSONIC_PASSWORD
        self._cache = {}
        
    def get_albums(self):
        """Get albums using injected config"""
        # Use self.config instead of importing config
        url = f"{self.base_url}/rest/getAlbumList2"
        params = {
            'u': self.username,
            'p': self.password,
            'f': 'json',
            'type': 'alphabeticalByName'
        }
        # ... rest of implementation


# =============================================================================
# MODIFIED MAIN.PY with Dependency Injection
# =============================================================================

def startup_event_with_dependency_injection():
    """Modified startup using dependency injection"""
    import logging
    from app.core.event_bus import event_bus
    from app.config import config
    
    # Step 1: Validate configuration
    if not config.validate_config():
        logging.error("❌ Configuration validation failed. Please check your .env file.")
        return
    
    # Step 2: Create database services with injected config
    from app.database.album_db_old import AlbumDatabase
    album_db = AlbumDatabase(config)
    
    # Step 3: Create music services with injected config
    subsonic_service = SubsonicService(config)
    
    # Step 4: Create chromecast service with injected config
    from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
    chromecast_service = PyChromecastServiceOnDemand(config, event_bus)
    
    # Step 5: Initialize hardware manager with injected dependencies
    hardware_manager = HardwareManager(config, event_bus)
    
    # Step 6: Initialize display hardware
    display = hardware_manager.initialize_hardware()
    
    # Step 7: Initialize screen manager with injected dependencies
    screen_manager = ScreenManager(display, event_bus)
    
    # Step 8: Initialize media player with injected dependencies
    jukebox_mediaplayer = JukeboxMediaPlayer(
        tracks=[],
        event_bus=event_bus,
        chromecast_service=chromecast_service
    )
    
    # Step 9: Initialize playback manager with ALL dependencies injected
    playback_manager = PlaybackManager(
        screen_manager=screen_manager,
        player=jukebox_mediaplayer,
        album_db=album_db,
        subsonic_service=subsonic_service,
        event_bus=event_bus
    )
    
    # Step 10: Set cross-references (these could also be injected)
    hardware_manager.screen_manager = screen_manager
    hardware_manager.playback_manager = playback_manager
    
    # Step 11: Start the system
    from app.ui.screens import IdleScreen
    IdleScreen.show()
    logging.info("🚀 Jukebox app startup complete with dependency injection")
    
    # Return services for global access if needed
    return {
        'hardware_manager': hardware_manager,
        'screen_manager': screen_manager,
        'playback_manager': playback_manager,
        'jukebox_mediaplayer': jukebox_mediaplayer
    }


# =============================================================================
# BENEFITS COMPARISON
# =============================================================================

"""
BEFORE (High Coupling):
- HardwareManager imports config directly → Hard to test with different configs
- PlaybackManager imports album_db functions → Hard to mock database
- ScreenManager imports event_bus → Hard to test event handling
- Services create their own dependencies → Difficult dependency management

AFTER (Low Coupling):
- All dependencies explicit in constructors → Easy to see what each class needs
- No hidden imports in class implementations → Clear dependency graph
- Easy to test with mocks → Just pass mock objects to constructors
- Single place (main.py) manages all dependencies → Clear dependency wiring
- Can easily swap implementations → Just pass different objects to constructors

TESTING EXAMPLE:
# Before - hard to test
def test_playback_manager():
    pm = PlaybackManager()  # Hidden dependencies on global config, database, etc.

# After - easy to test  
def test_playback_manager():
    mock_screen = Mock()
    mock_player = Mock()
    mock_db = Mock()
    mock_subsonic = Mock()
    mock_event_bus = Mock()
    
    pm = PlaybackManager(mock_screen, mock_player, mock_db, mock_subsonic, mock_event_bus)
    # Now you can test pm with complete control over all dependencies
"""
