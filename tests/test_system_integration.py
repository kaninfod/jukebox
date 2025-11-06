"""
End-to-End System Tests for Jukebox Application

These tests verify the complete system startup, dependency injection,
and integration between all major components.
"""
import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
import logging

# Mock hardware dependencies for testing
@pytest.fixture(autouse=True)
def mock_hardware_dependencies():
    """Mock all hardware-specific imports that don't work in test environment"""
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
    
    # Mock PIL for image processing
    sys.modules['PIL'] = Mock()
    sys.modules['PIL.Image'] = Mock()
    sys.modules['PIL.ImageDraw'] = Mock()
    sys.modules['PIL.ImageFont'] = Mock()
    
    # Mock pychromecast
    sys.modules['pychromecast'] = Mock()
    sys.modules['pychromecast.controllers'] = Mock()
    sys.modules['pychromecast.controllers.media'] = Mock()
    
    # Mock hardware device modules
    sys.modules['app.hardware.devices.ili9488'] = Mock()
    sys.modules['app.hardware.devices.rfid'] = Mock()
    sys.modules['app.hardware.devices.pushbutton'] = Mock()
    sys.modules['app.hardware.devices.rotaryencoder'] = Mock()


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    config = Mock()
    config.validate_config.return_value = True
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
    config.SUBSONIC_URL = "http://test.subsonic.com"
    config.SUBSONIC_USER = "testuser"
    config.SUBSONIC_PASS = "testpass"
    config.SUBSONIC_CLIENT = "testclient"
    config.SUBSONIC_API_VERSION = "1.16.1"
    config.STATIC_FILE_PATH = "/tmp/test_static"
    config.get_database_url.return_value = "sqlite:///test_jukebox.db"
    config.get_icon_path.return_value = "test_icon.png"
    return config


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus"""
    from app.core.event_bus import EventBus
    return EventBus()


class TestSystemStartup:
    """Test complete system startup with dependency injection"""
    
    def test_system_dependencies_creation(self, mock_config, mock_event_bus):
        """Test that all core dependencies can be created"""
        from app.database.album_db import AlbumDatabase
        from app.services.subsonic_service import SubsonicService
        from app.services.chromecast_service import ChromecastService
        
        # Test database creation
        album_db = AlbumDatabase(mock_config)
        assert album_db.config == mock_config
        
        # Test subsonic service creation
        subsonic_service = SubsonicService(mock_config)
        assert subsonic_service.config == mock_config
        assert subsonic_service.base_url == "http://test.subsonic.com"
        
        # Test chromecast service creation
        with patch('pychromecast.get_chromecasts'):
            chromecast_service = ChromecastService("Test Device")
            assert chromecast_service.device_name == "Test Device"
    
    def test_hardware_manager_initialization(self, mock_config, mock_event_bus):
        """Test HardwareManager with dependency injection"""
        from app.hardware.hardware import HardwareManager
        
        # Mock the device classes
        with patch('app.hardware.hardware.ILI9488') as mock_display, \
             patch('app.hardware.hardware.RC522Reader') as mock_rfid, \
             patch('app.hardware.hardware.RotaryEncoder') as mock_encoder, \
             patch('app.hardware.hardware.PushButton') as mock_button:
            
            # Create hardware manager with dependencies
            hw_manager = HardwareManager(
                config=mock_config,
                event_bus=mock_event_bus
            )
            
            # Verify dependencies are set
            assert hw_manager.config == mock_config
            assert hw_manager.event_bus == mock_event_bus
            
            # Test hardware initialization
            display = hw_manager.initialize_hardware()
            
            # Verify device initialization was called with correct parameters
            mock_display.assert_called_once()
            mock_rfid.assert_called_once_with(
                cs_pin=mock_config.RFID_CS_PIN,
                on_new_uid=hw_manager._handle_new_uid
            )
    
    def test_screen_manager_initialization(self, mock_config, mock_event_bus):
        """Test ScreenManager with dependency injection"""
        from app.ui.screen_manager import ScreenManager
        
        mock_display = Mock()
        
        # Mock fonts with the expected structure
        mock_fonts = {
            'title': Mock(),
            'default': Mock(),
            'small': Mock(),
            'large': Mock()
        }
        
        with patch('app.ui.manager.ScreenManager._load_fonts') as mock_load_fonts:
            mock_load_fonts.return_value = mock_fonts
            
            screen_manager = ScreenManager(
                display=mock_display,
                event_bus=mock_event_bus
            )
            
            assert screen_manager.display == mock_display
            assert screen_manager.event_bus == mock_event_bus
    
    def test_jukebox_mediaplayer_initialization(self, mock_config, mock_event_bus):
        """Test JukeboxMediaPlayer with dependency injection"""
        from app.services.media_player_service import MediaPlayerService
        
        mock_chromecast = Mock()
        mock_chromecast.device_name = "Test Chromecast"
        mock_chromecast.get_volume.return_value = 0.5
        
        player = MediaPlayerService(
            playlist=[],
            event_bus=mock_event_bus,
            chromecast_service=mock_chromecast
        )
        
        assert player.event_bus == mock_event_bus
        assert player.cc_service == mock_chromecast
        assert player.current_volume == 50  # 0.5 * 100
    
    def test_playback_service_initialization(self, mock_config, mock_event_bus):
        """Test PlaybackManager with all dependencies"""
        from app.services.playback_service import PlaybackService
        from app.database.album_db import AlbumDatabase
        from app.services.subsonic_service import SubsonicService
        
        # Create dependencies
        mock_screen_manager = Mock()
        mock_player = Mock()
        album_db = AlbumDatabase(mock_config)
        subsonic_service = SubsonicService(mock_config)
        
        # Create PlaybackService with all dependencies
        playback_service = PlaybackService(
            screen_manager=mock_screen_manager,
            player=mock_player,
            album_db=album_db,
            subsonic_service=subsonic_service,
            event_bus=mock_event_bus
        )
        
        # Verify all dependencies are set
        assert playback_service.screen_manager == mock_screen_manager
        assert playback_service.player == mock_player
        assert playback_service.album_db == album_db
        assert playback_service.subsonic_service == subsonic_service
        assert playback_service.event_bus == mock_event_bus


class TestSystemIntegration:
    """Test integration between system components"""
    
    def test_full_system_startup_simulation(self, mock_config, mock_event_bus):
        """Simulate the complete startup process from main.py"""
        from app.database.album_db import AlbumDatabase
        from app.services.subsonic_service import SubsonicService
        from app.services.chromecast_service import ChromecastService
        from app.hardware.hardware import HardwareManager
        from app.ui.screen_manager import ScreenManager
        from app.services.media_player_service import MediaPlayerService
        from app.services.playback_service import PlaybackService
        
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
            mock_display_class.return_value = mock_display
            
            # Step 1: Create core dependencies (like main.py)
            album_db = AlbumDatabase(mock_config)
            subsonic_service = SubsonicService(mock_config)
            chromecast_service = ChromecastService("Living Room")
            
            # Step 2: Initialize hardware manager
            hardware_manager = HardwareManager(
                config=mock_config,
                event_bus=mock_event_bus,
                screen_manager=None
            )
            
            # Step 3: Initialize display hardware
            display = hardware_manager.initialize_hardware()
            assert display == mock_display
            
            # Step 4: Initialize screen manager
            screen_manager = ScreenManager(
                display=display,
                event_bus=mock_event_bus
            )
            
            # Step 5: Initialize MediaPlayerService
            jukebox_mediaplayer = MediaPlayerService(
                playlist=[],
                event_bus=mock_event_bus,
                chromecast_service=chromecast_service
            )
            
            # Step 6: Initialize PlaybackService
            playback_service = PlaybackService(
                screen_manager=screen_manager,
                player=jukebox_mediaplayer,
                album_db=album_db,
                subsonic_service=subsonic_service,
                event_bus=mock_event_bus
            )
            
            # Step 7: Update cross-references
            hardware_manager.screen_manager = screen_manager
            hardware_manager.playback_service = playback_service
            
            # Verify the complete dependency graph is properly wired
            assert hardware_manager.screen_manager == screen_manager
            assert hardware_manager.playback_service == playback_service
            assert playback_service.screen_manager == screen_manager
            assert playback_service.player == jukebox_mediaplayer
            
            # All components should have their dependencies properly injected
            assert all([
                hardware_manager.config == mock_config,
                hardware_manager.event_bus == mock_event_bus,
                screen_manager.event_bus == mock_event_bus,
                jukebox_mediaplayer.event_bus == mock_event_bus,
                playback_service.event_bus == mock_event_bus,
                playback_service.album_db == album_db,
                playback_service.subsonic_service == subsonic_service
            ])
    
    def test_dependency_injection_prevents_circular_imports(self):
        """Verify that dependency injection prevents circular import issues"""
        # This test ensures that modules can be imported independently
        # without triggering circular imports
        
        # Test individual module imports
        from app.services.playback_service import PlaybackService
        from app.hardware.hardware import HardwareManager  
        from app.ui.screen_manager import ScreenManager
        from app.services.media_player_service import MediaPlayerService
        from app.services.subsonic_service import SubsonicService
        from app.database.album_db import AlbumDatabase
        
        # All imports should succeed without errors
        assert True  # If we get here, no circular imports occurred


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
