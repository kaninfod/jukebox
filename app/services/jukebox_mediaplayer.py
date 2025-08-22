
import logging
from typing import List, Dict, Optional
from enum import Enum
from app.services.pytube_service import PytubeService


class PlayerStatus(Enum):
    PLAY = "playing"
    PAUSE = "paused"
    STOP = "idle"
    STANDBY = "unavailable"
    OFF = "off"

class JukeboxMediaPlayer:
    def __init__(self, playlist: List[Dict]):
        self.playlist = playlist
        self.current_index = 0
        self.status = PlayerStatus.STOP
        self.pytube_service = PytubeService()
        self.listeners = []  # List of observer callbacks
        self.current_volume = 20  # Default to 50%
        logging.info("JukeboxMediaPlayer initialized.")

    def add_listener(self, callback):
        """Register a callback to be notified on state changes."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def notify(self, event_type, data=None):
        for cb in self.listeners:
            try:
                cb(event_type, data)
            except Exception as e:
                logging.warning(f"Listener error: {e}")

    @property
    def image_url(self) -> Optional[str]:
        track = self.current_track
        return track.get('image_url') if track else None

    @property
    def track_number(self) -> Optional[int]:
        track = self.current_track
        return track.get('track_number') if track else None

    @property
    def year(self) -> Optional[str]:
        track = self.current_track
        return track.get('year') if track else None

    @property
    def video_id(self) -> Optional[str]:
        track = self.current_track
        return track.get('video_id') if track else None
    
    @property
    def current_track(self) -> Optional[Dict]:
        if not self.playlist:
            return None
        return self.playlist[self.current_index]

    @property
    def artist(self) -> Optional[str]:
        track = self.current_track
        return track.get('artist') if track else None
    
    @property
    def title(self) -> Optional[str]:
        track = self.current_track
        return track.get('title') if track else None

    @property
    def duration(self) -> Optional[str]:
        track = self.current_track
        return track.get('duration') if track else None

    @property
    def album(self) -> Optional[str]:
        track = self.current_track
        return track.get('album') if track else None

    @property
    def volume(self) -> int:
        """Return the current volume (0-100)."""
        return self.current_volume

    def sync_volume_from_ha(self, ha_volume):
        """Sync volume from Home Assistant (0.0-1.0) to 0-100 scale."""
        self.current_volume = int(ha_volume * 100)

    def play(self):
        """Start playback of the current track (cast and set state)."""
        if not self.playlist:
            logging.warning("No playlist loaded.")
            return
        self.status = PlayerStatus.PLAY
        self.notify('status_changed', self.status)
        self.cast_current_track()

    def play_pause(self):
        from app.services.homeassistant_service import HomeAssistantService
        ha_service = HomeAssistantService()
        self.notify('status_changed', self.status)
        ha_service.play_pause()

    def stop(self):
        from app.services.homeassistant_service import HomeAssistantService
        ha_service = HomeAssistantService()
        ha_service.stop()
        self.status = PlayerStatus.STOP
        self.notify('status_changed', self.status)

    def set_volume(self, volume):
        """Set volume (0-100) and sync with Home Assistant."""
        self.current_volume = max(0, min(100, int(volume)))
        ha_volume = self.current_volume / 100.0
        from app.services.homeassistant_service import HomeAssistantService
        self.notify('volume_changed', self.current_volume)
        ha_service = HomeAssistantService()
        ha_service.set_volume(ha_volume)

    def volume_up(self):
        self.set_volume(self.current_volume + 5)

    def volume_down(self):
        self.set_volume(self.current_volume - 5)

    def next_track(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.notify('track_changed', self.current_track)
            self.play()
        else:
            self.stop()

    def previous_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.notify('track_changed', self.current_track)
            self.play()

    def cast_current_track(self):
        from app.services.homeassistant_service import HomeAssistantService
        track = self.playlist[self.current_index]
        stream_url = track.get('stream_url')
        video_id = track.get('video_id')
        if not stream_url and video_id:
            try:
                stream_url = self.pytube_service.get_stream_url(video_id)
                track['stream_url'] = stream_url
                logging.info(f"Fetched stream_url for video_id {video_id}")
            except Exception as e:
                logging.error(f"Failed to fetch stream_url for video_id {video_id}: {e}")
                stream_url = None
        if stream_url:
            ha_service = HomeAssistantService()
            ha_service.cast_stream_url(stream_url)
            logging.info(f"Casting track {self.current_index+1}/{len(self.playlist)}: {track.get('title')}")
            self.status = PlayerStatus.PLAY
            self.notify('track_changed', track)
        else:
            logging.error("No stream_url for current track.")

    def get_status(self) -> Dict:
        return {
            'status': self.status.value,
            'current_index': self.current_index,
            'current_track': self.playlist[self.current_index] if self.playlist else None
        }
