"""
Unit Tests for Individual Services

These tests verify each service works correctly in isolation
with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json


class TestSubsonicService:
    """Test SubsonicService functionality"""
    
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.SUBSONIC_URL = "http://test.subsonic.com"
        config.SUBSONIC_USER = "testuser"
        config.SUBSONIC_PASS = "testpass"
        config.SUBSONIC_CLIENT = "testclient"
        config.SUBSONIC_API_VERSION = "1.16.1"
        config.STATIC_FILE_PATH = "/tmp/test_static"
        return config
    
    def test_subsonic_service_initialization(self, mock_config):
        """Test SubsonicService initializes with injected config"""
        from app.services.subsonic_service import SubsonicService
        
        service = SubsonicService(mock_config)
        
        assert service.config == mock_config
        assert service.base_url == "http://test.subsonic.com"
        assert service.username == "testuser"
        assert service.password == "testpass"
    
    def test_get_stream_url(self, mock_config):
        """Test stream URL generation"""
        from app.services.subsonic_service import SubsonicService
        
        service = SubsonicService(mock_config)
        track = {"track_id": "test123"}
        
        url = service.get_stream_url(track)
        
        assert "test123" in url
        assert "testuser" in url
        assert "testpass" in url
    
    def test_get_stream_url_no_track_id(self, mock_config):
        """Test stream URL with missing track ID"""
        from app.services.subsonic_service import SubsonicService
        
        service = SubsonicService(mock_config)
        track = {}
        
        url = service.get_stream_url(track)
        
        assert url is None
    
    @patch('app.services.subsonic_service.requests.get')
    def test_search_song(self, mock_get, mock_config):
        """Test song search functionality"""
        from app.services.subsonic_service import SubsonicService
        
        # Mock response - the method calls data.json() so we need to structure it correctly
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "searchResult3": {
                "song": [
                    {"id": "123", "title": "Test Song", "artist": "Test Artist"}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        service = SubsonicService(mock_config)
        result = service.search_song("test")
        
        assert result is not None
        assert result["id"] == "123"
        assert result["title"] == "Test Song"


class TestAlbumDatabase:
    """Test AlbumDatabase functionality"""
    
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.get_database_url.return_value = "sqlite:///:memory:"
        return config
    
    @pytest.fixture 
    def album_db(self, mock_config):
        from app.database.album_db import AlbumDatabase
        return AlbumDatabase(mock_config)
    
    def test_album_database_initialization(self, mock_config):
        """Test AlbumDatabase initializes with injected config"""
        from app.database.album_db import AlbumDatabase
        
        db = AlbumDatabase(mock_config)
        
        assert db.config == mock_config
        assert db.database_url == "sqlite:///:memory:"
    
    def test_create_album_entry(self, album_db):
        """Test creating a new album entry"""
        result = album_db.create_album_entry("test_rfid_123")
        
        assert result["status"] == "RFID created"
        assert result["rfid"] == "test_rfid_123"
    
    def test_create_duplicate_album_entry(self, album_db):
        """Test creating duplicate RFID entry"""
        # Create first entry
        album_db.create_album_entry("test_rfid_123")
        
        # Try to create duplicate
        result = album_db.create_album_entry("test_rfid_123")
        
        assert result["status"] == "RFID already exists"
    
    def test_get_album_entry_by_rfid(self, album_db):
        """Test retrieving album by RFID"""
        # Create entry first
        album_db.create_album_entry("test_rfid_123")
        
        # Retrieve it
        entry = album_db.get_album_entry_by_rfid("test_rfid_123")
        
        assert entry is not None
        assert entry.rfid == "test_rfid_123"
    
    def test_get_nonexistent_album_entry(self, album_db):
        """Test retrieving non-existent album"""
        entry = album_db.get_album_entry_by_rfid("nonexistent")
        
        assert entry is None
    
    def test_update_album_entry(self, album_db):
        """Test updating album entry"""
        # Create entry first
        album_db.create_album_entry("test_rfid_123")
        
        # Update it
        album_data = {
            "album_name": "Test Album",
            "artist_name": "Test Artist", 
            "album_id": "playlist123"
        }
        entry = album_db.update_album_entry("test_rfid_123", album_data)
        
        assert entry is not None
        assert entry["album_name"] == "Test Album"
        assert entry["artist_name"] == "Test Artist"
    assert entry["album_id"] == "playlist123"


class TestJukeboxMediaPlayer:
    """Test JukeboxMediaPlayer functionality"""
    
    @pytest.fixture
    def mock_event_bus(self):
        return Mock()
    
    @pytest.fixture
    def mock_chromecast_service(self):
        mock_cc = Mock()
        mock_cc.device_name = "Test Chromecast"
        mock_cc.get_volume.return_value = 0.6
        mock_cc.set_volume = Mock()
        mock_cc.play_media = Mock()
        mock_cc.pause = Mock()
        mock_cc.resume = Mock()
        mock_cc.stop = Mock()
        return mock_cc
    
    def test_jukebox_mediaplayer_initialization(self, mock_event_bus, mock_chromecast_service):
        """Test JukeboxMediaPlayer initializes with dependencies"""
        from app.services.media_player_service import MediaPlayerService
        
        player = MediaPlayerService(
            playlist=[],
            event_bus=mock_event_bus,
            chromecast_service=mock_chromecast_service
        )
        
        assert player.event_bus == mock_event_bus
        assert player.cc_service == mock_chromecast_service
        assert player.current_volume == 60  # 0.6 * 100
    
    def test_volume_controls(self, mock_event_bus, mock_chromecast_service):
        """Test volume up/down controls"""
        from app.services.media_player_service import MediaPlayerService
        
        player = MediaPlayerService(
            playlist=[],
            event_bus=mock_event_bus,
            chromecast_service=mock_chromecast_service
        )
        
        initial_volume = player.current_volume
        
        # Test volume up
        player.volume_up()
        assert player.current_volume == initial_volume + 5
        
        # Test volume down  
        player.volume_down()
        assert player.current_volume == initial_volume  # Back to original
    
    def test_set_volume(self, mock_event_bus, mock_chromecast_service):
        """Test setting specific volume"""
        from app.services.media_player_service import MediaPlayerService
        
        player = MediaPlayerService(
            playlist=[],
            event_bus=mock_event_bus,
            chromecast_service=mock_chromecast_service
        )
        
        # Test setting volume
        player.set_volume(75)
        assert player.current_volume == 75
        
        # Verify chromecast service was called with normalized volume
        mock_chromecast_service.set_volume.assert_called_with(0.75)
    
    def test_playlist_loading(self, mock_event_bus, mock_chromecast_service):
        """Test loading playlist"""
        from app.services.media_player_service import MediaPlayerService
        
        test_tracks = [
            {"title": "Track 1", "artist": "Artist 1"},
            {"title": "Track 2", "artist": "Artist 2"}
        ]
        
        player = MediaPlayerService(
            playlist=test_tracks,
            event_bus=mock_event_bus,
            chromecast_service=mock_chromecast_service
        )
        
        assert len(player.playlist) == 2
        assert player.current_track["title"] == "Track 1"


class TestPlaybackManager:
    """Test PlaybackManager functionality"""
    
    @pytest.fixture
    def mock_dependencies(self):
        return {
            'screen_manager': Mock(),
            'player': Mock(),
            'album_db': Mock(),
            'subsonic_service': Mock(),
            'event_bus': Mock()
        }
    
    def test_playback_service_initialization(self, mock_dependencies):
        """Test PlaybackManager initializes with all dependencies"""
        from app.services.playback_service import PlaybackService
        
        pm = PlaybackService(**mock_dependencies)
        
        assert pm.screen_manager == mock_dependencies['screen_manager']
        assert pm.player == mock_dependencies['player']
        assert pm.album_db == mock_dependencies['album_db']
        assert pm.subsonic_service == mock_dependencies['subsonic_service']
        assert pm.event_bus == mock_dependencies['event_bus']
    
    def test_load_from_album_id_existing_album(self, mock_dependencies):
        """Test loading existing album by album_id"""
        from app.services.playback_service import PlaybackService

        # Mock database response
        mock_album_data = {
            'album_name': 'Test Album',
            'artist_name': 'Test Artist',
            'tracks': [
                {'title': 'Track 1', 'track_id': 'track1', 'duration': 180},
                {'title': 'Track 2', 'track_id': 'track2', 'duration': 200}
            ]
        }
        mock_dependencies['album_db'].get_album_data_by_album_id.return_value = mock_album_data

        pm = PlaybackService(**mock_dependencies)
        result = pm.load_from_album_id("test_playlist_123")

        assert result is True
        mock_dependencies['album_db'].get_album_data_by_album_id.assert_called_with("test_playlist_123")
        mock_dependencies['player'].play.assert_called_once()

    def test_load_from_album_id_nonexistent_album(self, mock_dependencies):
        """Test loading non-existent album"""
        from app.services.playback_service import PlaybackService
        # Mock database returning None
        mock_dependencies['album_db'].get_album_data_by_album_id.return_value = None
        # Mock subsonic service returning None
        mock_dependencies['subsonic_service'].add_or_update_album_entry_from_album_id.return_value = None

        pm = PlaybackService(**mock_dependencies)
        result = pm.load_from_album_id("nonexistent_playlist")

        assert result is False


class TestHardwareManager:
    """Test HardwareManager functionality"""
    
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.RFID_CS_PIN = 7
        config.NFC_CARD_SWITCH_GPIO = 8
        config.ROTARY_ENCODER_PIN_A = 23
        config.ROTARY_ENCODER_PIN_B = 24
        config.ENCODER_BOUNCETIME = 50
        config.BUTTON_1_GPIO = 5
        config.BUTTON_2_GPIO = 6
        config.BUTTON_3_GPIO = 13
        config.BUTTON_5_GPIO = 26
        config.BUTTON_BOUNCETIME = 300
        return config
    
    @pytest.fixture
    def mock_event_bus(self):
        return Mock()
    
    def test_hardware_manager_initialization(self, mock_config, mock_event_bus):
        """Test HardwareManager initializes with dependencies"""
        from app.hardware.hardware import HardwareManager
        
        hw = HardwareManager(
            config=mock_config,
            event_bus=mock_event_bus
        )
        
        assert hw.config == mock_config
        assert hw.event_bus == mock_event_bus
    
    @patch('app.hardware.hardware.GPIO')
    def test_handle_new_uid_emits_event(self, mock_gpio, mock_config, mock_event_bus):
        """Test that RFID UID detection emits correct event"""
        from app.hardware.hardware import HardwareManager
        from app.core import Event, EventType
        
        hw = HardwareManager(
            config=mock_config,
            event_bus=mock_event_bus
        )
        
        # Simulate RFID detection
        test_uid = "test_uid_123"
        hw._handle_new_uid(test_uid)
        
        # Verify event was emitted
        mock_event_bus.emit.assert_called_once()
        emitted_event = mock_event_bus.emit.call_args[0][0]
        assert emitted_event.type == EventType.RFID_READ
        assert emitted_event.payload["rfid"] == test_uid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
