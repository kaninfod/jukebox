# Example Factory Pattern for Jukebox Application

import logging
from typing import Protocol, Dict, Any

class ServiceFactory:
    """
    Factory pattern for creating services with their dependencies
    """
    
    def __init__(self):
        self._config = None
        self._event_bus = None
        self._created_services: Dict[str, Any] = {}
        
    def initialize(self, config, event_bus):
        """Initialize factory with core dependencies"""
        self._config = config
        self._event_bus = event_bus
        
    def create_hardware_manager(self):
        """Create HardwareManager with injected dependencies"""
        if 'hardware_manager' not in self._created_services:
            from app.hardware import HardwareManager
            self._created_services['hardware_manager'] = HardwareManager(
                config=self._config,
                event_bus=self._event_bus
            )
        return self._created_services['hardware_manager']
    
    def create_screen_manager(self):
        """Create ScreenManager with injected dependencies"""
        if 'screen_manager' not in self._created_services:
            from app.ui import ScreenManager
            hardware_manager = self.create_hardware_manager()
            display = hardware_manager.initialize_hardware()
            self._created_services['screen_manager'] = ScreenManager(
                display=display,
                event_bus=self._event_bus
            )
        return self._created_services['screen_manager']
    
    def create_album_database(self):
        """Create AlbumDatabase with injected dependencies"""
        if 'album_database' not in self._created_services:
            from app.database.album_db_old import AlbumDatabase
            self._created_services['album_database'] = AlbumDatabase(
                config=self._config
            )
        return self._created_services['album_database']
    
    def create_subsonic_service(self):
        """Create SubsonicService with injected dependencies"""
        if 'subsonic_service' not in self._created_services:
            from app.services.subsonic_service import SubsonicService
            self._created_services['subsonic_service'] = SubsonicService(
                config=self._config
            )
        return self._created_services['subsonic_service']
    
    def create_jukebox_mediaplayer(self):
        """Create JukeboxMediaPlayer with injected dependencies"""
        if 'jukebox_mediaplayer' not in self._created_services:
            from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
            self._created_services['jukebox_mediaplayer'] = JukeboxMediaPlayer(
                tracks=[],
                event_bus=self._event_bus
            )
        return self._created_services['jukebox_mediaplayer']
    
    def create_playback_manager(self):
        """Create PlaybackManager with all dependencies injected"""
        if 'playback_manager' not in self._created_services:
            from app.services.playback_manager import PlaybackManager
            self._created_services['playback_manager'] = PlaybackManager(
                screen_manager=self.create_screen_manager(),
                player=self.create_jukebox_mediaplayer(),
                album_db=self.create_album_database(),
                subsonic_service=self.create_subsonic_service(),
                event_bus=self._event_bus
            )
        return self._created_services['playback_manager']
    
    def get_service(self, service_name: str):
        """Generic service getter"""
        method_name = f"create_{service_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        else:
            raise ValueError(f"Unknown service: {service_name}")


# Usage in main.py with factory pattern
def startup_event():
    """Initialize all systems using factory pattern"""
    global service_factory
    
    # Create factory and initialize with core dependencies
    from app.core.event_bus import event_bus
    from app.config import config
    
    service_factory = ServiceFactory()
    service_factory.initialize(config, event_bus)
    
    # Create services through factory (dependencies automatically injected)
    playback_manager = service_factory.create_playback_manager()
    screen_manager = service_factory.create_screen_manager()
    hardware_manager = service_factory.create_hardware_manager()
    
    # Update hardware manager with references (cross-dependencies)
    hardware_manager.screen_manager = screen_manager
    hardware_manager.playback_manager = playback_manager
    
    # Start the system
    from app.ui.screens import IdleScreen
    IdleScreen.show()
    logging.info("🚀 Jukebox app startup complete")


# Global factory instance
service_factory = None

def get_service_factory():
    """Get the global service factory"""
    if service_factory is None:
        raise RuntimeError("Service factory not initialized")
    return service_factory

# Usage in other modules:
# factory = get_service_factory()
# playback_manager = factory.get_service('playback_manager')
