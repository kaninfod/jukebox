
from importlib.metadata import metadata
import time

# Prometheus metric for play counts

# Import play_counter from metrics collector
from app.metrics.collector import play_counter

import logging
# from enum import Enum
from typing import List, Dict, Optional
from app.services.chromecast_service import ChromecastService
# from enum import Enum
from app.core import EventType, Event
from app.core import PlayerStatus

logger = logging.getLogger(__name__)

# class PlayerStatus(Enum):
#     PLAY = "playing"
#     PAUSE = "paused"
#     STOP = "idle"
#     STANDBY = "unavailable"
#     OFF = "off"

class JukeboxMediaPlayer:

    def __init__(self, playlist: List[Dict], event_bus, chromecast_service=None):
        """
        Initialize JukeboxMediaPlayer with dependency injection.
        
        Args:
            playlist: List of tracks to play
            event_bus: EventBus instance for event communication
            chromecast_service: PyChromecastService instance for playback control
        """
        self.playlist = playlist
        self.current_index = 0
        self.status = PlayerStatus.STOP
        
        # Inject dependencies - no more direct imports/creation
        self.event_bus = event_bus
        if chromecast_service:
            self.cc_service = chromecast_service
        else:
            # Fallback for backward compatibility - this will be removed later
                from app.config import config
                self.cc_service = ChromecastService(config.DEFAULT_CHROMECAST_DEVICE)
            
        self.current_volume = 0  # Ensure attribute exists before any event/context
        self.track_timer = TrackTimer()
        self.sync_volume_from_chromecast()
        logger.info(f"JukeboxMediaPlayer initialized with dependency injection. Chromecast device={self.cc_service.device_name}")

    def cleanup(self):
        logger.info("JukeboxMediaPlayer cleanup called")
        # Add any additional cleanup logic here if needed


    def _emit_event(self, event_type, data=None):
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(type=event_type, payload=data))

    @property
    def album_cover(self) -> Optional[str]:
        track = self.current_track
        return track.get('album_cover_filename') if track else None

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
    
    @property
    def provider(self) -> str:
        """Return the current provider."""
        track = self.current_track
        return track.get('provider') if track else None

    def sync_volume_from_chromecast(self):
        """Sync volume from Chromecast (0.0-1.0) to 0-100 scale."""
        cc_volume = self.cc_service.get_volume()
        logger.debug(f"[sync_volume_from_chromecast] cc_volume from Chromecast: {cc_volume}")
        try:
            value = int(cc_volume * 100) if cc_volume is not None else 50
        except Exception as e:
            logger.error(f"[sync_volume_from_chromecast] Failed to set current_volume from cc_volume={cc_volume}: {e}")
            value = 50  # Default fallback volume
        self.current_volume = value
        
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.VOLUME_CHANGED,
            payload=self._get_context()
        ))
        
        return self.current_volume

    def play(self, event=None):
        """Start playback of the current track (cast and set state)."""
        if not self.playlist:
            logging.warning("No playlist loaded.")
            return
        self.status = PlayerStatus.PLAY
        self.cast_current_track()
        self.track_timer.start()
        return True

    def play_pause(self, event=None):
        # Toggle pause/resume timer based on current status
        if self.status == PlayerStatus.PLAY:
            self.track_timer.pause()
            self.status = PlayerStatus.PAUSE
            self.cc_service.pause()
        elif self.status == PlayerStatus.PAUSE:
            self.track_timer.resume()
            self.status = PlayerStatus.PLAY
            self.cc_service.resume()

        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.TRACK_CHANGED,
            payload=self._get_context()
        ))
        return True

    def stop(self, event=None):
        # Log actual vs expected duration before stopping
        elapsed = self.track_timer.get_elapsed()
        expected = self.current_track.get('duration') if self.current_track else None
        logging.info(f"[TrackTimer] Track '{self.title}' expected duration: {expected}, played: {elapsed:.2f} seconds (stop)")
        self.cc_service.stop()
        
        self.status = PlayerStatus.STOP
        self.track_timer.reset()
        
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.TRACK_CHANGED,
            payload=self._get_context()
        ))

        return True

    def set_volume(self, volume, event=None):
        """Set volume (0-100) and sync with Chromecast."""
        logger.debug(f"[set_volume] Requested volume: {volume}")
        try:
            self.current_volume = max(0, min(100, int(volume)))
        except Exception as e:
            logger.error(f"[set_volume] Failed to set current_volume from volume={volume}: {e}")
            self.current_volume = 0
        logger.debug(f"[set_volume] current_volume set to: {self.current_volume}")
        # Convert to Chromecast's 0.0-1.0 scale
        normalized_volume = self.current_volume / 100.0 if self.current_volume is not None else None

        if normalized_volume is not None:
            self.cc_service.set_volume(normalized_volume)

        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.VOLUME_CHANGED,
            payload=self._get_context()
        ))
        return normalized_volume

    def volume_up(self, event=None):
        self.set_volume(self.current_volume + 5)
        return True


    def volume_down(self, event=None):
        self.set_volume(self.current_volume - 5)
        return True

    def next_track(self, event=None, force=False):
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

        if force == False:
            expected_sec = duration_to_seconds(expected_str)
            debounce_threshold = 0.8  # 80%
            if expected_sec:
                min_play_time = expected_sec * debounce_threshold
            else:
                min_play_time = 0
            if elapsed < min_play_time:
                logger.info(f"[Debounce] Track '{self.title}' skipped after only {elapsed:.2f}s (<80% of {expected_sec}s). Debounce: not advancing.")
                # Do nothing: ignore the request to advance
                return
            logger.info(f"[Debounce] Track '{self.title}' played {elapsed:.2f}s (>=80% of {expected_sec}s). Advancing to next track.")

        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.play()
            return True
        else:
            self.stop()
            return False

    def previous_track(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.play()
            return True

    def get_track_elapsed(self):
        """Return the elapsed play time (seconds) for the current track."""
        return self.track_timer.get_elapsed()

    def get_stream_url_for_track(self, track: Dict) -> Optional[str]:
        """
        Provider-agnostic stream URL resolver for the current track.
        Returns the stream URL or None if not available.
        """
        provider = track.get('provider')
        stream_url = track.get('stream_url')
        if provider == 'subsonic':
            from app.services.subsonic_service import SubsonicService
            service = SubsonicService()
            return service.get_stream_url(track)
        else:
            logger.error(f"Unknown provider: {provider}")
            return None

    def get_cover_url_for_track(self, album_id: str) -> Optional[str]:
        """
        Cover URL resolver for the current track.
        Returns the cover URL or None if not available.
        """    

        from app.services.subsonic_service import SubsonicService
        service = SubsonicService()
        album_id = album_id
        if album_id:
            url = service.get_cover_url(album_id)
            logger.debug(f"Resolved cover URL for album_id {album_id}: {url}")  
            return url
        else:
            return None
    

    def get_subsonic_ids_for_track(self, track: Dict) -> Dict[str, str]:
        """
        Returns a dict with Subsonic IDs for artist, album, and track using SubsonicService.get_song_info.
        If not available, returns 'unknown'.
        """
        if track.get('provider') != 'subsonic':
            return {'artist': 'unknown', 'album': 'unknown', 'track': 'unknown'}
        track_id = track.get('video_id')
        if not track_id:
            return {'artist': 'unknown', 'album': 'unknown', 'track': 'unknown'}
        from app.services.subsonic_service import SubsonicService
        service = SubsonicService()
        song_info = service.get_song_info(track_id)
        if not song_info:
            return {'artist': 'unknown', 'album': 'unknown', 'track': video_id}
        return {
            'artist': song_info.get('artistId', 'unknown'),
            'album': song_info.get('albumId', 'unknown'),
            'track': song_info.get('id', track_id)
        }

    def cast_current_track(self):
        track = self.playlist[self.current_index]
        stream_url = self.get_stream_url_for_track(track)
        track['stream_url'] = stream_url
        # Use Subsonic IDs for Prometheus labels if available
        ids = self.get_subsonic_ids_for_track(track)
        play_counter.labels(
            artist=ids['artist'],
            album=ids['album'],
            song=ids['track']
        ).inc()
        if stream_url:
            logger.info(f"Casting stream URL for track {track.get('title')}, with url {stream_url}")
            self.cc_service.play_media(stream_url, media_info={
                "title": track.get("title"),
                "thumb": self.get_cover_url_for_track(ids['album']),
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
            self.track_timer.reset()
            self.track_timer.start()
            logger.info(f"Casting track {self.current_index+1}/{len(self.playlist)}: {track.get('title')}")
            self.status = PlayerStatus.PLAY
            # Use injected event_bus instead of importing
            self.event_bus.emit(Event(
                type=EventType.TRACK_CHANGED,
                payload=self._get_context()
            ))
        else:
            logger.error("No stream_url for current track.")

    def _get_context(self):
        return {
            'status': self.status.value,
            'volume': self.current_volume,
            'current_index': self.current_index,
            'current_track': self.current_track,
            'album_cover_filename': self.album_cover
        }

    def get_status(self) -> Dict:
        return {
            'status': self.status.value,
            'current_index': self.current_index,
            'current_track': self.playlist[self.current_index] if self.playlist else None
        }


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