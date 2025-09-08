from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MusicProviderService(ABC):
    @abstractmethod
    def get_stream_url(self, track: dict) -> str:
        """Return a stream URL for the given track dict."""
        pass
    @abstractmethod
    def add_or_update_album_entry(self, rfid: str, audioPlaylistId: str):
        pass

    @abstractmethod
    def search_song(self, query: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_album_tracks(self, audioPlaylistId: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_album_info(self, audioPlaylistId: str) -> Dict[str, Any]:
        pass
