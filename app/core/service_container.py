# Service Container for Jukebox Application

class ServiceContainer:
    """
    Service container for managing dependencies and their lifecycle
    """
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register_singleton(self, name: str, factory_func):
        self._services[name] = factory_func
        self._singletons[name] = True
    
    def register_transient(self, name: str, factory_func):
        self._services[name] = factory_func
        self._singletons[name] = False
    
    def get(self, name: str):
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        if self._singletons[name]:
            cache_key = f"_instance_{name}"
            if not hasattr(self, cache_key):
                setattr(self, cache_key, self._services[name](self))
            return getattr(self, cache_key)
        else:
            return self._services[name](self)


# --- Service factory functions ---
def create_app_state(container):
    from app.services.appstate import AppStateService
    return AppStateService()


def create_config(container):
    from app.config import config
    return config

def create_event_bus(container):
    from app.core.event_bus import event_bus
    return event_bus

def create_album_database(container):
    from app.database.album_db import AlbumDatabase
    config = container.get('config')
    return AlbumDatabase(config)

def create_subsonic_service(container):
    from app.services.subsonic_service import SubsonicService
    config = container.get('config')
    return SubsonicService(config)

def create_hardware_manager(container):
    from app.hardware import HardwareManager
    config = container.get('config')
    event_bus = container.get('event_bus')
    return HardwareManager(config, event_bus)

def create_screen_manager(container):
    from app.ui import ScreenManager
    hardware_manager = container.get('hardware_manager')
    event_bus = container.get('event_bus')
    display = hardware_manager.initialize_hardware()
    return ScreenManager(display, event_bus)

def create_jukebox_mediaplayer(container):
    from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
    event_bus = container.get('event_bus')
    return JukeboxMediaPlayer([], event_bus)

def create_playback_manager(container):
    from app.services.playback_manager import PlaybackManager
    return PlaybackManager(
        screen_manager=container.get('screen_manager'),
        player=container.get('jukebox_mediaplayer'),
        album_db=container.get('album_database'),
        subsonic_service=container.get('subsonic_service'),
        event_bus=container.get('event_bus')
    )

# --- Setup function ---
def setup_service_container():
    """Configure all services in the container"""
    global container
    container = ServiceContainer()
    # Register core services as singletons
    container.register_singleton('config', create_config)
    container.register_singleton('app_state', create_app_state)
    container.register_singleton('event_bus', create_event_bus)
    container.register_singleton('album_database', create_album_database)
    container.register_singleton('subsonic_service', create_subsonic_service)
    # Register hardware/UI services as singletons
    container.register_singleton('hardware_manager', create_hardware_manager)
    container.register_singleton('screen_manager', create_screen_manager)
    container.register_singleton('jukebox_mediaplayer', create_jukebox_mediaplayer)
    container.register_singleton('playback_manager', create_playback_manager)
    return container

# --- Global access helper ---
container = None
def get_service(name: str):
    """Global service accessor"""
    if container is None:
        raise RuntimeError("Service container not initialized")
    return container.get(name)
