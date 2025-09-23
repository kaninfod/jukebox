"""
ChromecastService: On-demand Chromecast service for device discovery, connection, and media control.
Refactored from PyChromecastServiceOnDemand.
"""

import pychromecast
from pychromecast.controllers.media import MediaController
from zeroconf import Zeroconf
from typing import Optional, List, Dict
import logging
import time
from app.config import config

logger = logging.getLogger(__name__)

class ChromecastMediaStatusListener:
    """
    Listener for Chromecast media status changes.
    Provides detailed logging of all status changes for debugging and integration.
    """
    def __init__(self, device_name: str):
        self.device_name = device_name
        self.last_player_state = None
        self.last_current_time = None
    def new_media_status(self, status):
        try:
            player_state = getattr(status, 'player_state', 'UNKNOWN')
            current_time = getattr(status, 'current_time', 0)
            duration = getattr(status, 'duration', None)
            idle_reason = getattr(status, 'idle_reason', None)
            content_id = getattr(status, 'content_id', None)
            if player_state != self.last_player_state:
                logger.info(f"[{self.device_name}] Media state changed: {self.last_player_state} → {player_state}")
                self._log_full_status(status)
                if player_state == 'IDLE':
                    if idle_reason:
                        logger.info(f"[{self.device_name}] IDLE reason: {idle_reason}")
                    if idle_reason == 'FINISHED':
                        from app.core import event_bus, EventType, Event
                        event_bus.emit(Event(
                            type=EventType.TRACK_FINISHED,
                            payload={"Reason": idle_reason}
                        ))
                        logger.info(f"[{self.device_name}] 🎵 TRACK FINISHED - Duration: {duration}s, Position: {current_time}s")
                elif player_state == 'PLAYING':
                    logger.info(f"[{self.device_name}] ▶️  Started playing - Duration: {duration}s")
                elif player_state == 'PAUSED':
                    from app.core import event_bus, EventType, Event
                    event_bus.emit(Event(
                        type=EventType.TRACK_PAUSED,
                        payload={}
                    ))
                    logger.info(f"[{self.device_name}] ⏸️  Paused at {current_time}s")
                elif player_state == 'BUFFERING':
                    logger.info(f"[{self.device_name}] ⏳ Buffering at {current_time}s")
                self.last_player_state = player_state
            if (player_state == 'PLAYING' and duration and 
                current_time and self.last_current_time and
                int(current_time / 10) != int(self.last_current_time / 10)):
                progress_pct = (current_time / duration) * 100 if duration > 0 else 0
                logger.debug(f"[{self.device_name}] Progress: {current_time:.1f}s / {duration:.1f}s ({progress_pct:.1f}%)")
            self.last_current_time = current_time
        except Exception as e:
            logger.error(f"[{self.device_name}] Error processing media status: {e}")
    def _log_full_status(self, status):
        try:
            logger.info(f"[{self.device_name}] 📊 FULL STATUS DUMP:")
            logger.info(f"  🎵 Playback: state={getattr(status, 'player_state', 'N/A')}, "
                       f"time={getattr(status, 'current_time', 'N/A')}s, "
                       f"duration={getattr(status, 'duration', 'N/A')}s")
            logger.info(f"  📀 Media: content_id={getattr(status, 'content_id', 'N/A')}, "
                       f"content_type={getattr(status, 'content_type', 'N/A')}")
            logger.info(f"  📝 Metadata: title='{getattr(status, 'title', 'N/A')}', "
                       f"artist='{getattr(status, 'artist', 'N/A')}', "
                       f"album='{getattr(status, 'album_name', 'N/A')}'")
            logger.info(f"  🔗 Session: id={getattr(status, 'media_session_id', 'N/A')}, "
                       f"stream_type={getattr(status, 'stream_type', 'N/A')}")
            supports = []
            if getattr(status, 'supports_pause', False): supports.append('pause')
            if getattr(status, 'supports_seek', False): supports.append('seek')
            if getattr(status, 'supports_stream_volume', False): supports.append('volume')
            if getattr(status, 'supports_skip_forward', False): supports.append('skip_forward')
            if getattr(status, 'supports_skip_backward', False): supports.append('skip_backward')
            logger.info(f"  🎛️  Supports: {', '.join(supports) if supports else 'none'}")
            logger.info(f"  🔊 Volume: level={getattr(status, 'volume_level', 'N/A')}, "
                       f"muted={getattr(status, 'volume_muted', 'N/A')}")
            idle_reason = getattr(status, 'idle_reason', None)
            playback_rate = getattr(status, 'playback_rate', None)
            images = getattr(status, 'images', [])
            logger.info(f"  ℹ️  Other: idle_reason={idle_reason}, "
                       f"playback_rate={playback_rate}, "
                       f"images_count={len(images) if images else 0}")
        except Exception as e:
            logger.error(f"[{self.device_name}] Error logging full status: {e}")

class ChromecastService:
    """
    Simplified Chromecast service using on-demand discovery.
    """
    def __init__(self, device_name: Optional[str] = None):
        self.device_name = device_name
        self.cast = None
        self.mc = None
        self.status_listener = None
        self._zeroconf = None
        self._discovery_zeroconf = None
    def __enter__(self):
        if not self._zeroconf:
            self._zeroconf = Zeroconf()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        self._cleanup_zeroconf()
    def _cleanup_zeroconf(self):
        if self._zeroconf:
            try:
                logger.debug("Closing persistent zeroconf instance")
                self._zeroconf.close()
                logger.info("✅ Persistent zeroconf instance closed successfully")
            except Exception as e:
                logger.warning(f"Error closing persistent zeroconf: {e}")
            finally:
                self._zeroconf = None
        else:
            logger.debug("No persistent zeroconf instance to clean up")
    def list_chromecasts(self) -> List[Dict[str, str]]:
        logger.info("Discovering Chromecasts on network using CastBrowser...")
        discovery_zeroconf = Zeroconf()
        try:
            from pychromecast.discovery import CastBrowser, SimpleCastListener
            devices = []
            class DiscoveryListener(SimpleCastListener):
                def add_cast(self, uuid, mdns_name):
                    pass
            listener = DiscoveryListener()
            browser = CastBrowser(listener, discovery_zeroconf)
            browser.start_discovery()
            import time
            time.sleep(config.CHROMECAST_DISCOVERY_TIMEOUT)
            for uuid, cast_info in browser.services.items():
                if hasattr(cast_info, 'friendly_name'):
                    devices.append({
                        'name': cast_info.friendly_name,
                        'model': getattr(cast_info, 'model_name', 'Unknown'),
                        'host': getattr(cast_info, 'host', 'Unknown'),
                        'uuid': str(uuid)
                    })
                    logger.debug(f"Found Chromecast: {cast_info.friendly_name} ({getattr(cast_info, 'model_name', 'Unknown')}) at {getattr(cast_info, 'host', 'Unknown')}")
            browser.stop_discovery()
            logger.info(f"Discovery complete: found {len(devices)} Chromecast devices")
            return devices
        except Exception as e:
            logger.error(f"Error during Chromecast discovery: {e}")
            return []
        finally:
            try:
                discovery_zeroconf.close()
            except Exception as e:
                logger.warning(f"Error closing discovery zeroconf: {e}")
    def connect(self, device_name: Optional[str] = None, fallback: bool = True) -> bool:
        target_name = device_name or self.device_name
        if self.cast:
            self.disconnect()
        if not self._zeroconf:
            logger.debug("Creating persistent zeroconf instance for connection")
            self._zeroconf = Zeroconf()
        logger.debug("Creating temporary zeroconf instance for discovery")
        discovery_zeroconf = Zeroconf()
        try:
            from pychromecast.discovery import CastBrowser, SimpleCastListener
            logger.info(f"Attempting to connect to Chromecast: {target_name or 'any available device'}")
            class ConnectionListener(SimpleCastListener):
                def add_cast(self, uuid, mdns_name):
                    pass
            listener = ConnectionListener()
            browser = CastBrowser(listener, discovery_zeroconf)
            browser.start_discovery()
            import time
            time.sleep(config.CHROMECAST_DISCOVERY_TIMEOUT)
            target_cast_info = None
            if target_name:
                for uuid, cast_info in browser.services.items():
                    if hasattr(cast_info, 'friendly_name') and cast_info.friendly_name == target_name:
                        target_cast_info = cast_info
                        logger.info(f"Found target device: {cast_info.friendly_name}")
                        break
                if not target_cast_info:
                    logger.warning(f"Device '{target_name}' not found.")
                    if not fallback:
                        logger.info("Fallback is disabled. Not connecting to first available device.")
                        return False
            if not target_cast_info and fallback:
                for uuid, cast_info in browser.services.items():
                    if hasattr(cast_info, 'friendly_name'):
                        target_cast_info = cast_info
                        logger.info(f"Using first available device: {cast_info.friendly_name}")
                        break
            if not target_cast_info:
                logger.error("No Chromecast devices found on network")
                return False
            browser.stop_discovery()
            self.cast = pychromecast.get_chromecast_from_cast_info(
                target_cast_info, self._zeroconf
            )
            logger.info(f"Waiting for {self.cast.name} to be ready...")
            self.cast.wait(timeout=config.CHROMECAST_WAIT_TIMEOUT)
            browser.stop_discovery()
            if not self.cast.status:
                raise Exception("Device status not available after connection")
            self.mc = self.cast.media_controller
            self.status_listener = ChromecastMediaStatusListener(self.cast.name)
            self.mc.register_status_listener(self.status_listener)
            logger.info(f"Registered media status listener for {self.cast.name}")
            logger.info(f"Successfully connected to {self.cast.name}")
            logger.debug(f"Device status: {self.cast.status}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Chromecast: {e}")
            self.disconnect()
            return False
        finally:
            try:
                logger.debug("Closing temporary discovery zeroconf instance")
                discovery_zeroconf.close()
                logger.debug("✅ Discovery zeroconf instance closed successfully")
            except Exception as e:
                logger.warning(f"Error closing discovery zeroconf: {e}")
    def disconnect(self):
        if self.cast:
            try:
                logger.info(f"Disconnecting from {self.cast.name}")
                if self.mc and self.status_listener:
                    try:
                        if hasattr(self.mc, 'unregister_status_listener'):
                            self.mc.unregister_status_listener(self.status_listener)
                            logger.debug("Unregistered media status listener")
                        else:
                            if hasattr(self.mc, 'remove_status_listener'):
                                self.mc.remove_status_listener(self.status_listener)
                                logger.debug("Removed media status listener")
                            else:
                                logger.debug("No status listener removal method found")
                    except Exception as e:
                        logger.warning(f"Error unregistering status listener: {e}")
                self.cast.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.cast = None
                self.mc = None
                self.status_listener = None
    def cleanup(self):
        logger.info("Performing full cleanup of Chromecast service")
        self.disconnect()
        self._cleanup_zeroconf()
    def is_connected(self) -> bool:
        if not self.cast or not self.mc:
            return False
        try:
            return self.cast.status is not None
        except Exception:
            return False
    def ensure_connected(self) -> bool:
        if self.is_connected():
            return True
        logger.info("Connection lost, attempting to reconnect...")
        return self.connect()
    def play_media(self, url: str, media_info: dict = None, content_type: str = "audio/mp3") -> bool:
        if not self.ensure_connected():
            logger.error("Cannot play media: no Chromecast connection")
            return False
        try:
            logger.info(f"Playing media on {self.cast.name}: {url} with {media_info}")
            if media_info:
                title = media_info.get("title", "Unknown Title")
                thumb = media_info.get("thumb")
                nested_info = media_info.get("media_info", {})
                artist = nested_info.get("artist") or media_info.get("artist", "Unknown Artist")
                album = nested_info.get("album") or media_info.get("album", "Unknown Album")
                year = nested_info.get("year") or media_info.get("year")
                metadata_dict = media_info.get("metadata", {})
                metadata = {
                    "metadataType": metadata_dict.get("metadataType", 3),
                    "title": title,
                    "artist": artist,
                    "albumName": album,
                }
                if year:
                    metadata["releaseDate"] = str(year)
                if thumb:
                    metadata["images"] = [{"url": thumb}]
                logger.info(f"Playing with metadata: {title} by {artist} from {album}")
                logger.debug(f"Metadata being sent: {metadata}")
                self.mc.play_media(url, content_type, title=title, thumb=thumb, metadata=metadata)
            else:
                logger.info("Playing media without metadata")
                self.mc.play_media(url, content_type)
            self.mc.block_until_active(timeout=config.CHROMECAST_WAIT_TIMEOUT)
            logger.info("Media started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to play media: {e}")
            try:
                logger.info("Attempting fallback playback without metadata")
                self.mc.play_media(url, content_type)
                self.mc.block_until_active(timeout=config.CHROMECAST_WAIT_TIMEOUT)
                return True
            except Exception as fallback_e:
                logger.error(f"Fallback playback also failed: {fallback_e}")
                return False
    def pause(self) -> bool:
        if not self.ensure_connected():
            return False
        try:
            self.mc.pause()
            logger.info("Media paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause: {e}")
            return False
    def resume(self) -> bool:
        if not self.ensure_connected():
            return False
        try:
            self.mc.play()
            logger.info("Media resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume: {e}")
            return False
    def stop(self) -> bool:
        if not self.ensure_connected():
            return False
        try:
            self.mc.stop()
            logger.info("Media stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop: {e}")
            return False
    def set_volume(self, volume: float) -> bool:
        if not self.ensure_connected():
            return False
        try:
            volume = max(0.0, min(1.0, volume))
            self.cast.set_volume(volume)
            logger.info(f"Volume set to {volume:.1%}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    def get_volume(self) -> Optional[float]:
        if not self.is_connected():
            return None
        try:
            volume = self.cast.status.volume_level
            logger.debug(f"Current volume: {volume:.1%}")
            return volume
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return None
    def get_status(self) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            status = {
                'device_name': self.cast.name,
                'volume_level': self.cast.status.volume_level,
                'volume_muted': self.cast.status.volume_muted,
                'is_active_input': getattr(self.cast.status, 'is_active_input', None),
                'is_stand_by': getattr(self.cast.status, 'is_stand_by', None),
                'app_id': self.cast.status.app_id,
                'display_name': self.cast.status.display_name,
                'status_text': self.cast.status.status_text,
            }
            if self.mc and self.mc.status:
                status.update({
                    'media_session_id': self.mc.status.media_session_id,
                    'player_state': self.mc.status.player_state,
                    'current_time': getattr(self.mc.status, 'current_time', None),
                    'duration': getattr(self.mc.status, 'duration', None),
                    'media_title': getattr(self.mc.status, 'title', None),
                    'media_artist': getattr(self.mc.status, 'artist', None),
                })
            return status
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return None
    def switch_device(self, new_device_name: str) -> bool:
        logger.info(f"Switching Chromecast device to: {new_device_name}")
        old_device_name = self.device_name
        try:
            if self.is_connected():
                logger.info(f"Stopping current playback on {self.cast.name}")
                try:
                    self.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playback: {e}")
            logger.info(f"Disconnecting from current device: {old_device_name}")
            self.disconnect()
            self.device_name = new_device_name
            logger.info(f"Attempting to connect to new device: {new_device_name}")
            if self.connect(new_device_name):
                logger.info(f"Successfully switched from '{old_device_name}' to '{new_device_name}'")
                return True
            else:
                logger.error(f"Failed to connect to '{new_device_name}', reverting to '{old_device_name}'")
                self.device_name = old_device_name
                return False
        except Exception as e:
            logger.error(f"Error during device switch: {e}")
            self.device_name = old_device_name
            return False

_service_instance = None
def get_chromecast_service(device_name: Optional[str] = None) -> ChromecastService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ChromecastService(device_name)
        _service_instance._zeroconf = Zeroconf()
        logger.info("Initialized on-demand Chromecast service")
    if device_name and device_name != _service_instance.device_name:
        _service_instance.device_name = device_name
        logger.info(f"Updated target device to: {device_name}")
    return _service_instance
