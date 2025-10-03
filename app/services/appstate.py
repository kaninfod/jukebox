import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AppState(Enum):
    IDLE = auto()
    PLAYBACK = auto()
    MENU = auto()
    NFC_ENCODING = auto()

class AppStateService:
    def __init__(self):
        self._is_music_playing = False
        self._is_menu_active = False
        self._is_nfc_encoding_active = False
        self._app_state = AppState.IDLE

    def set_app_state(self, state: AppState):
        logger.info(f"App state changed: {self._app_state.name} -> {state.name}")
        self._app_state = state

    def get_app_state(self) -> AppState:
        return self._app_state

    def is_encoding_mode_active(self) -> bool:
        return self._app_state == AppState.NFC_ENCODING

    def enable_encoding_mode(self):
        self.set_app_state(AppState.NFC_ENCODING)

    def disable_encoding_mode(self):
        self.set_app_state(AppState.IDLE)

    @property
    def is_music_playing(self) -> bool:
        return self._is_music_playing
    
    @is_music_playing.setter
    def is_music_playing(self, value: bool):
        self._is_music_playing = value
