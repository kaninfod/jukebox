
from importlib.metadata import metadata
import time
class TrackTimer:
    def __init__(self):
        self.start_time = None
        self.paused_time = 0
        self.is_paused = False
        self.pause_start = None

    def start(self):
        self.start_time = time.monotonic()
        self.paused_time = 0
        self.is_paused = False
        self.pause_start = None

    def pause(self):
        if not self.is_paused and self.start_time is not None:
            self.is_paused = True
            self.pause_start = time.monotonic()

    def resume(self):
        if self.is_paused and self.pause_start is not None:
            self.paused_time += time.monotonic() - self.pause_start
            self.is_paused = False
            self.pause_start = None

    def reset(self):
        self.__init__()

    def get_elapsed(self):
        if self.start_time is None:
            return 0
        if self.is_paused:
            return self.pause_start - self.start_time - self.paused_time
        else:
            return time.monotonic() - self.start_time - self.paused_time
import logging
from typing import List, Dict, Optional
from enum import Enum
from app.services.pytube_service import PytubeService
from app.services.homeassistant_service import HomeAssistantService


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
        self.ha_service = HomeAssistantService()
        self.current_volume = 0  # Ensure attribute exists before any event/context
        self.track_timer = TrackTimer()
        self.sync_volume_from_ha()
        logging.info(f"JukeboxMediaPlayer initialized. id={id(self)} current_volume={self.current_volume}")

    def cleanup(self):
        logging.info("JukeboxMediaPlayer cleanup called")
        # Add any additional cleanup logic here if needed


    def _emit_event(self, event_type, data=None):
        from app.ui.event_bus import ui_event_bus, UIEvent
        ui_event_bus.emit(UIEvent(type=event_type, payload=data))

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

    def sync_volume_from_ha(self):
        """Sync volume from Home Assistant (0.0-1.0) to 0-100 scale."""
        ha_volume = self.ha_service.get_volume()
        logging.debug(f"[sync_volume_from_ha] ha_volume from HA: {ha_volume}")
        try:
            value = int(ha_volume * 100)
        except Exception as e:
            logging.error(f"[sync_volume_from_ha] Failed to set current_volume from ha_volume={ha_volume}: {e}")
            value = None
        self.current_volume = value
        self._emit_event('volume_changed', self._get_context())
        return self.current_volume

    def play(self):
        """Start playback of the current track (cast and set state)."""
        if not self.playlist:
            logging.warning("No playlist loaded.")
            return
        self.status = PlayerStatus.PLAY
        self._emit_event('status_changed', self._get_context())
        self.cast_current_track()
        self.track_timer.start()

    def play_pause(self):
        # Toggle pause/resume timer based on current status
        if self.status == PlayerStatus.PLAY:
            self.track_timer.pause()
            self.status = PlayerStatus.PAUSE
        elif self.status == PlayerStatus.PAUSE:
            self.track_timer.resume()
            self.status = PlayerStatus.PLAY
        self._emit_event('status_changed', self._get_context())
        self.ha_service.play_pause()

    def stop(self):
        # Log actual vs expected duration before stopping
        elapsed = self.track_timer.get_elapsed()
        expected = self.current_track.get('duration') if self.current_track else None
        logging.info(f"[TrackTimer] Track '{self.title}' expected duration: {expected}, played: {elapsed:.2f} seconds (stop)")
        self.ha_service.stop()
        self.status = PlayerStatus.STOP
        self.track_timer.reset()
        self._emit_event('status_changed', self._get_context())

    def set_volume(self, volume):
        """Set volume (0-100) and sync with Home Assistant."""
        logging.debug(f"[set_volume] Requested volume: {volume}")
        try:
            self.current_volume = max(0, min(100, int(volume)))
        except Exception as e:
            logging.error(f"[set_volume] Failed to set current_volume from volume={volume}: {e}")
            self.current_volume = 0
        logging.debug(f"[set_volume] current_volume set to: {self.current_volume}")
        # Convert to Home Assistant's 0.0-1.0 scale
        ha_volume_normalized = self.current_volume / 100.0 if self.current_volume is not None else None
        self._emit_event('volume_changed', self._get_context())
        if ha_volume_normalized is not None:
            self.ha_service.set_volume(ha_volume_normalized)

    def volume_up(self):
        self.set_volume(self.current_volume + 5)

    def volume_down(self):
        self.set_volume(self.current_volume - 5)

    def next_track(self):
        # Log actual vs expected duration before advancing
        elapsed = self.track_timer.get_elapsed()
        expected_str = self.current_track.get('duration') if self.current_track else None
        # Convert expected duration (mm:ss or m:ss) to seconds
        def duration_to_seconds(dur):
            if not dur:
                return None
            try:
                parts = dur.split(":")
                if len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            except Exception:
                return None
            return None
        expected_sec = duration_to_seconds(expected_str)
        debounce_threshold = 0.8  # 80%
        if expected_sec:
            min_play_time = expected_sec * debounce_threshold
        else:
            min_play_time = 0
        if elapsed < min_play_time:
            logging.info(f"[Debounce] Track '{self.title}' skipped after only {elapsed:.2f}s (<80% of {expected_sec}s). Debounce: not advancing.")
            # Do nothing: ignore the request to advance
            return
        logging.info(f"[Debounce] Track '{self.title}' played {elapsed:.2f}s (>=80% of {expected_sec}s). Advancing to next track.")
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.track_timer.reset()
            self._emit_event('track_changed', self._get_context())
            self.play()
        else:
            self.stop()

    def previous_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.track_timer.reset()
            self._emit_event('track_changed', self._get_context())
            self.play()
    def get_track_elapsed(self):
        """Return the elapsed play time (seconds) for the current track."""
        return self.track_timer.get_elapsed()

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
            ha_service.cast_stream_url(stream_url, media_info={
                "title": track.get("title"),
                "thumb": track.get("image_url"),
                "media_info": {
                    "artist": track.get("artist"),
                    "album": track.get("album"),
                    "year": track.get("year"),
                },
                "metadata": {
                    "metadataType": 3,
                    "albumName": track.get("album"),
                    "artist": track.get("artist")
                }
            })
            logging.info(f"Casting track {self.current_index+1}/{len(self.playlist)}: {track.get('title')}")
            self.status = PlayerStatus.PLAY
            self._emit_event('track_changed', self._get_context())
        else:
            logging.error("No stream_url for current track.")

    def _get_context(self):
        # Add album cover filename from DB if yt_id is available
        from app.database import get_ytmusic_data_by_yt_id
        album_cover_filename = None
        if self.current_track and isinstance(self.current_track, dict):
            album_cover_filename = self.current_track.get('album_cover_filename')
        return {
            'status': self.status.value,
            'volume': self.current_volume,
            'current_index': self.current_index,
            'current_track': self.current_track,
            'album_cover_filename': album_cover_filename
        }

    def get_status(self) -> Dict:
        return {
            'status': self.status.value,
            'current_index': self.current_index,
            'current_track': self.playlist[self.current_index] if self.playlist else None
        }
