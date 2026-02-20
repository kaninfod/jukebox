"""
Integration Tests for User Interaction Patterns

These tests verify common user workflows and interactions
between multiple services working together.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys


@pytest.fixture(autouse=True)
def mock_hardware_dependencies():
    """Mock hardware dependencies for all tests"""
    # Mock RPi.GPIO
    rpi_gpio_mock = Mock()
    rpi_gpio_mock.BCM = 11
    rpi_gpio_mock.IN = 1
    rpi_gpio_mock.OUT = 0
    rpi_gpio_mock.PUD_UP = 22
    rpi_gpio_mock.FALLING = 32
    rpi_gpio_mock.LOW = 0
    rpi_gpio_mock.HIGH = 1
    
    sys.modules['RPi'] = Mock()
    sys.modules['RPi.GPIO'] = rpi_gpio_mock
    sys.modules['pychromecast'] = Mock()
    sys.modules['pychromecast.controllers'] = Mock()
    sys.modules['pychromecast.controllers.media'] = Mock()
    
    # Mock device modules
    sys.modules['app.hardware.devices.ili9488'] = Mock()
    sys.modules['app.hardware.devices.rfid'] = Mock()
    sys.modules['app.hardware.devices.pushbutton'] = Mock()
    sys.modules['app.hardware.devices.rotaryencoder'] = Mock()


@pytest.fixture
def full_system_setup():
    """Create a full system setup with mocked hardware"""
    from app.database.album_db import AlbumDatabase
    from app.services.subsonic_service import SubsonicService
    from app.services.chromecast_service import ChromecastService
    from app.hardware.hardware import HardwareManager
    from app.ui.screen_manager import ScreenManager
    from app.services.media_player_service import MediaPlayerService
    from app.services.playback_service import PlaybackService
    from app.core.event_bus import event_bus
    
    # Mock config
    mock_config = Mock()
    mock_config.validate_config.return_value = True
    mock_config.RFID_CS_PIN = 7
    mock_config.NFC_CARD_SWITCH_GPIO = 8
    mock_config.ROTARY_ENCODER_PIN_A = 23
    mock_config.ROTARY_ENCODER_PIN_B = 24
    mock_config.ENCODER_BOUNCETIME = 50
    mock_config.BUTTON_1_GPIO = 5
    mock_config.BUTTON_2_GPIO = 6
    mock_config.BUTTON_3_GPIO = 13
    mock_config.BUTTON_5_GPIO = 26
    mock_config.BUTTON_BOUNCETIME = 300
    mock_config.get_database_url.return_value = "sqlite:///:memory:"
    mock_config.SUBSONIC_URL = "http://test.subsonic.com"
    mock_config.SUBSONIC_USER = "testuser"
    mock_config.SUBSONIC_PASS = "testpass"
    mock_config.SUBSONIC_CLIENT = "testclient"
    mock_config.SUBSONIC_API_VERSION = "1.16.1"
    mock_config.STATIC_FILE_PATH = "/tmp/test_static"
    
    with patch('pychromecast.get_chromecasts'), \
         patch('app.hardware.hardware.ILI9488') as mock_display_class, \
         patch('app.hardware.hardware.RC522Reader'), \
         patch('app.hardware.hardware.RotaryEncoder'), \
         patch('app.hardware.hardware.PushButton'), \
         patch('app.ui.manager.ScreenManager._load_fonts') as mock_load_fonts:
        
        # Mock fonts with the expected structure
        mock_fonts = {
            'title': Mock(),
            'default': Mock(),
            'small': Mock(),
            'large': Mock()
        }
        mock_load_fonts.return_value = mock_fonts
        mock_display = Mock()
        # Configure mock display to return proper dimensions for PIL
        mock_display.device.width = 480
        mock_display.device.height = 320
        mock_display_class.return_value = mock_display
        
        # Create all services with dependency injection
        # Use Mock for album_db to allow test control
        album_db = Mock(spec=AlbumDatabase)
        subsonic_service = SubsonicService(mock_config)
        chromecast_service = ChromecastService("Living Room")
        
        hardware_manager = HardwareManager(
            config=mock_config,
            event_bus=event_bus
        )
        
        display = hardware_manager.initialize_hardware()
        
        screen_manager = ScreenManager(
            display=display,
            event_bus=event_bus
        )
        
        media_player_service = MediaPlayerService(
            playlist=[],
            event_bus=event_bus,
            playback_backend=chromecast_service
        )
        
        playback_service = PlaybackService(
            screen_manager=screen_manager,
            player=media_player_service,
            album_db=album_db,
            subsonic_service=subsonic_service,
            event_bus=event_bus
        )
        
        hardware_manager.screen_manager = screen_manager
        hardware_manager.playback_service = playback_service
        
        return {
            'config': mock_config,
            'event_bus': event_bus,
            'album_db': album_db,
            'subsonic_service': subsonic_service,
            'chromecast_service': chromecast_service,
            'hardware_manager': hardware_manager,
            'screen_manager': screen_manager,
            'media_player_service': media_player_service,
            'playback_service': playback_service,
            'display': display
        }


class TestRFIDWorkflow:
    """Test complete RFID card scanning workflow"""
    
    def test_new_rfid_card_detection(self, full_system_setup):
        """Test workflow when a new RFID card is detected"""
        system = full_system_setup
        playback_service = system['playback_service']
        album_db = system['album_db']
        event_bus = system['event_bus']
        
        from app.core import Event, EventType
        
        # Simulate RFID detection with new card
        test_rfid = "new_rfid_12345"
        rfid_event = Event(
            type=EventType.RFID_READ,
            payload={"rfid": test_rfid}
        )
        
        # Process the RFID event
        result = playback_service.load_rfid(rfid_event)
        
        # Should create new album entry and return True
        assert result is True
        
        # Verify album entry was created in database
        entry = album_db.get_album_entry_by_rfid(test_rfid)
        assert entry is not None
        assert entry.rfid == test_rfid
    
    def test_existing_rfid_card_no_playlist(self, full_system_setup):
        """Test workflow when existing RFID card has no playlist assigned"""
        system = full_system_setup
        playback_service = system['playback_service']
        album_db = system['album_db']
        
        from app.core import Event, EventType
        
    # Create an album entry without album_id
        test_rfid = "existing_rfid_12345"
        album_db.create_album_entry(test_rfid)
        
        # Simulate RFID detection
        rfid_event = Event(
            type=EventType.RFID_READ,
            payload={"rfid": test_rfid}
        )
        
        # Process the RFID event
        result = playback_service.load_rfid(rfid_event)
        
        # Should return False because no playlist is assigned
        assert result is False
    
    def test_existing_rfid_card_with_playlist(self, full_system_setup):
        """Test workflow when existing RFID card has playlist assigned"""
        system = full_system_setup
        playback_service = system['playback_service']
        album_db = system['album_db']
        player = system['media_player_service']
        
        from app.core import Event, EventType
        
        # Create album entry with tracks
        test_rfid = "playlist_rfid_12345"
        album_db.create_album_entry(test_rfid)
        
        album_data = {
            "album_name": "Test Album",
            "artist_name": "Test Artist",
            "album_id": "playlist_123",
            "tracks": [
                {"title": "Track 1", "track_id": "track1", "duration": 180},
                {"title": "Track 2", "track_id": "track2", "duration": 200}
            ]
        }
        album_db.update_album_entry(test_rfid, album_data)
        
        # Simulate RFID detection
        rfid_event = Event(
            type=EventType.RFID_READ,
            payload={"rfid": test_rfid}
        )
        
        # Process the RFID event
        result = playback_service.load_rfid(rfid_event)
        
        # Should successfully load and start playback
        assert result is True
        
        # Verify playlist was loaded into player
        assert len(player.playlist) == 2
        assert player.playlist[0]["title"] == "Track 1"


class TestButtonInteractionWorkflow:
    """Test button press interaction workflows"""
    
    def test_button_press_events(self, full_system_setup):
        """Test that button presses generate correct events"""
        system = full_system_setup
        hardware_manager = system['hardware_manager']
        event_bus = system['event_bus']
        
        from app.core import Event, EventType
        
        # Mock event emission tracking
        emitted_events = []
        original_emit = event_bus.emit
        
        def track_emit(event):
            emitted_events.append(event)
            return original_emit(event)
        
        event_bus.emit = track_emit
        
        # Simulate button presses
        hardware_manager._on_button1_press()  # Previous track
        hardware_manager._on_button2_press()  # Play/Pause
        hardware_manager._on_button3_press()  # Next track
        
        # Filter only BUTTON_PRESSED events
        button_events = [e for e in emitted_events if e.type == EventType.BUTTON_PRESSED]
        
        # Verify correct events were emitted
        assert len(button_events) == 3
        
        assert button_events[0].type == EventType.BUTTON_PRESSED
        assert button_events[0].payload["button"] == 1
        assert button_events[0].payload["action"] == "previous_track"
        
        assert button_events[1].type == EventType.BUTTON_PRESSED
        assert button_events[1].payload["button"] == 2
        assert button_events[1].payload["action"] == "play_pause"
        
        assert button_events[2].type == EventType.BUTTON_PRESSED
        assert button_events[2].payload["button"] == 3
        assert button_events[2].payload["action"] == "next_track"
    
    def test_playback_control_workflow(self, full_system_setup):
        """Test complete playback control workflow"""
        system = full_system_setup
        player = system['media_player_service']
        playback_service = system['playback_service']
        
        from app.services.media_player_service import PlayerStatus
        
        # Load some test tracks
        test_tracks = [
            {"title": "Track 1", "stream_url": "http://test.com/track1"},
            {"title": "Track 2", "stream_url": "http://test.com/track2"}
        ]
        player.playlist = test_tracks
        player.current_index = 0
        
        # Test play
        player.play()
        assert player.status == PlayerStatus.PLAY
        
        # Test pause
        player.play_pause()
        assert player.status == PlayerStatus.PAUSE
        
        # Test resume
        player.play_pause()
        assert player.status == PlayerStatus.PLAY
        
        # Test stop
        player.stop()
        assert player.status == PlayerStatus.STOP


class TestVolumeControlWorkflow:
    """Test volume control workflows"""
    
    def test_volume_control_via_rotary_encoder(self, full_system_setup):
        """Test volume control through rotary encoder"""
        system = full_system_setup
        hardware_manager = system['hardware_manager']
        player = system['media_player_service']
        playback_service = system['playback_service']
        
        from app.core import Event, EventType
        
        initial_volume = player.current_volume
        
        # Simulate rotary encoder clockwise (volume up)
        cw_event = Event(
            type=EventType.ROTARY_ENCODER,
            payload={"direction": "CW"}
        )
        playback_service._handle_rotary_encoder_event(cw_event)
        
        # Volume should have increased
        assert player.current_volume > initial_volume
        
        # Simulate rotary encoder counter-clockwise (volume down)
        ccw_event = Event(
            type=EventType.ROTARY_ENCODER,
            payload={"direction": "CCW"}
        )
        playback_service._handle_rotary_encoder_event(ccw_event)
        
        # Volume should be back to initial or lower
        assert player.current_volume <= initial_volume
    
    def test_volume_bounds_checking(self, full_system_setup):
        """Test volume doesn't go below 0 or above 100"""
        system = full_system_setup
        player = system['jukebox_mediaplayer']
        
        # Test maximum volume
        player.set_volume(100)
        player.volume_up()
        assert player.current_volume <= 100
        
        # Test minimum volume
        player.set_volume(0)
        player.volume_down()
        assert player.current_volume >= 0


class TestMenuNavigationWorkflow:
    """Test menu navigation and album selection"""
    
    def test_menu_album_selection(self, full_system_setup):
        """Test selecting album from menu"""
        system = full_system_setup
        playback_service = system['playback_service']
        event_bus = system['event_bus']
        
        from app.core import Event, EventType
        
        # Simulate menu album selection event
        menu_event = Event(
            type=EventType.PLAY_ALBUM,
            payload={
                "album_id": "menu_album_123",
                "album_name": "Menu Selected Album"
            }
        )
        
        # Mock album data in database
        system['album_db'].get_album_data_by_album_id.return_value = {
            "album_name": "Menu Selected Album",
            "artist_name": "Menu Artist",
            "tracks": [
                {"title": "Menu Track 1", "track_id": "menu1", "duration": 180}
            ]
        }
        
        # Process menu selection
        playback_service._handle_play_album_event(menu_event)
        
        # Verify album was loaded
        assert len(system['jukebox_mediaplayer'].playlist) == 1
        assert system['jukebox_mediaplayer'].playlist[0]["title"] == "Menu Track 1"


class TestErrorHandlingWorkflows:
    """Test error handling in various workflows"""
    
    def test_rfid_with_database_error(self, full_system_setup):
        """Test RFID workflow when database has errors"""
        system = full_system_setup
        playback_service = system['playback_service']
        
        from app.core import Event, EventType
        
        # Mock database error
        system['album_db'].get_album_entry_by_rfid.side_effect = Exception("Database error")
        
        rfid_event = Event(
            type=EventType.RFID_READ,
            payload={"rfid": "error_rfid_123"}
        )
        
        # Should handle error gracefully
        try:
            result = playback_service.load_rfid(rfid_event)
            # Should not crash, may return False
            assert result in [True, False]
        except Exception:
            pytest.fail("RFID handling should not raise unhandled exceptions")
    
    def test_playback_with_missing_stream_url(self, full_system_setup):
        """Test playback with missing stream URLs"""
        system = full_system_setup
        player = system['jukebox_mediaplayer']
        
        # Load track without stream_url
        test_tracks = [
            {"title": "Track Without URL", "track_id": "no_stream"}
        ]
        player.playlist = test_tracks
        
        # Should handle missing stream URL gracefully
        try:
            player.cast_current_track()
            # Should not crash
        except Exception:
            pytest.fail("Missing stream URL should not crash playback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
