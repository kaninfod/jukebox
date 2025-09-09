"""
Simplified on-demand Chromecast service based on official pychromecast examples.

"""

import pychromecast
from pychromecast.controllers.media import MediaController
from zeroconf import Zeroconf
from typing import Optional, List, Dict
import logging
import time

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
        """Called when media status changes on the Chromecast."""
        try:
            # Extract key status information
            player_state = getattr(status, 'player_state', 'UNKNOWN')
            current_time = getattr(status, 'current_time', 0)
            duration = getattr(status, 'duration', None)
            idle_reason = getattr(status, 'idle_reason', None)
            content_id = getattr(status, 'content_id', None)
            
            # Log state changes
            if player_state != self.last_player_state:
                logger.info(f"[{self.device_name}] Media state changed: {self.last_player_state} → {player_state}")
                
                # Log comprehensive status information on state changes
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
            
            # Log time progress every 10 seconds when playing
            if (player_state == 'PLAYING' and duration and 
                current_time and self.last_current_time and
                int(current_time / 10) != int(self.last_current_time / 10)):
                progress_pct = (current_time / duration) * 100 if duration > 0 else 0
                logger.debug(f"[{self.device_name}] Progress: {current_time:.1f}s / {duration:.1f}s ({progress_pct:.1f}%)")
                
            self.last_current_time = current_time
            
        except Exception as e:
            logger.error(f"[{self.device_name}] Error processing media status: {e}")
    
    def _log_full_status(self, status):
        """Log all available properties of the MediaStatus object."""
        try:
            logger.info(f"[{self.device_name}] 📊 FULL STATUS DUMP:")
            
            # Core playback info
            logger.info(f"  🎵 Playback: state={getattr(status, 'player_state', 'N/A')}, "
                       f"time={getattr(status, 'current_time', 'N/A')}s, "
                       f"duration={getattr(status, 'duration', 'N/A')}s")
            
            # Media info
            logger.info(f"  📀 Media: content_id={getattr(status, 'content_id', 'N/A')}, "
                       f"content_type={getattr(status, 'content_type', 'N/A')}")
            
            # Metadata
            logger.info(f"  📝 Metadata: title='{getattr(status, 'title', 'N/A')}', "
                       f"artist='{getattr(status, 'artist', 'N/A')}', "
                       f"album='{getattr(status, 'album_name', 'N/A')}'")
            
            # Session info
            logger.info(f"  🔗 Session: id={getattr(status, 'media_session_id', 'N/A')}, "
                       f"stream_type={getattr(status, 'stream_type', 'N/A')}")
            
            # Control capabilities
            supports = []
            if getattr(status, 'supports_pause', False): supports.append('pause')
            if getattr(status, 'supports_seek', False): supports.append('seek')
            if getattr(status, 'supports_stream_volume', False): supports.append('volume')
            if getattr(status, 'supports_skip_forward', False): supports.append('skip_forward')
            if getattr(status, 'supports_skip_backward', False): supports.append('skip_backward')
            logger.info(f"  🎛️  Supports: {', '.join(supports) if supports else 'none'}")
            
            # Volume info
            logger.info(f"  🔊 Volume: level={getattr(status, 'volume_level', 'N/A')}, "
                       f"muted={getattr(status, 'volume_muted', 'N/A')}")
            
            # Additional info
            idle_reason = getattr(status, 'idle_reason', None)
            playback_rate = getattr(status, 'playback_rate', None)
            images = getattr(status, 'images', [])
            
            logger.info(f"  ℹ️  Other: idle_reason={idle_reason}, "
                       f"playback_rate={playback_rate}, "
                       f"images_count={len(images) if images else 0}")
                       
            # All remaining attributes for complete info
            all_attrs = [attr for attr in dir(status) if not attr.startswith('_')]
            logger.debug(f"  🔍 All attributes: {all_attrs}")
            
        except Exception as e:
            logger.error(f"[{self.device_name}] Error logging full status: {e}")


class PyChromecastServiceOnDemand:
    """
    Simplified Chromecast service using on-demand discovery.
    
    Based on official pychromecast examples with these principles:
    - Single responsibility: connect to and control one Chromecast
    - On-demand discovery: only discover when actually needed
    - Simple state management: connected or not connected
    - Error recovery: clean disconnect and retry on failures
    """
    
    def __init__(self, device_name: Optional[str] = None):
        """Initialize the service with optional target device name."""
        self.device_name = device_name
        self.cast = None
        self.mc = None
        self.status_listener = None
        self._zeroconf = None
        
    def __enter__(self):
        """Context manager entry - initialize zeroconf."""
        if not self._zeroconf:
            self._zeroconf = Zeroconf()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup connections."""
        self.disconnect()
        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None
    
    def list_chromecasts(self) -> List[Dict[str, str]]:
        """
        Discover and return all available Chromecasts on the network using CastBrowser.
        
        Returns:
            List of dicts with 'name', 'model', 'host', 'uuid' keys
        """
        logger.info("Discovering Chromecasts on network using CastBrowser...")
        
        # Ensure zeroconf is initialized
        if not self._zeroconf:
            self._zeroconf = Zeroconf()
        
        try:
            from pychromecast.discovery import CastBrowser, SimpleCastListener
            
            devices = []
            
            class DiscoveryListener(SimpleCastListener):
                def add_cast(self, uuid, mdns_name):
                    pass  # We'll get devices from browser.services instead
            
            # Create browser and start discovery
            listener = DiscoveryListener()
            browser = CastBrowser(listener, self._zeroconf)
            browser.start_discovery()
            
            # Wait for discovery to complete
            import time
            time.sleep(3)  # Give discovery time to find devices
            
            # Extract devices from browser services
            for uuid, cast_info in browser.services.items():
                if hasattr(cast_info, 'friendly_name'):
                    devices.append({
                        'name': cast_info.friendly_name,
                        'model': getattr(cast_info, 'model_name', 'Unknown'),
                        'host': getattr(cast_info, 'host', 'Unknown'),
                        'uuid': str(uuid)
                    })
                    logger.debug(f"Found Chromecast: {cast_info.friendly_name} ({getattr(cast_info, 'model_name', 'Unknown')}) at {getattr(cast_info, 'host', 'Unknown')}")
            
            # Clean up the browser
            browser.stop_discovery()
            
            logger.info(f"Discovery complete: found {len(devices)} Chromecast devices")
            return devices
            
        except Exception as e:
            logger.error(f"Error during Chromecast discovery: {e}")
            return []
    
    def connect(self, device_name: Optional[str] = None) -> bool:
        """
        Connect to a Chromecast device using CastBrowser.
        
        Args:
            device_name: Optional specific device name. Uses self.device_name if not provided.
            
        Returns:
            True if connection successful, False otherwise
        """
        # Use provided device name or fall back to instance device name
        target_name = device_name or self.device_name
        
        # Disconnect any existing connection first
        if self.cast:
            self.disconnect()
            
        # Ensure zeroconf is initialized
        if not self._zeroconf:
            self._zeroconf = Zeroconf()
        
        try:
            from pychromecast.discovery import CastBrowser, SimpleCastListener
            
            logger.info(f"Attempting to connect to Chromecast: {target_name or 'any available device'}")
            
            class ConnectionListener(SimpleCastListener):
                def add_cast(self, uuid, mdns_name):
                    pass  # We'll get devices from browser.services
            
            # Use CastBrowser for discovery
            listener = ConnectionListener()
            browser = CastBrowser(listener, self._zeroconf)
            browser.start_discovery()
            
            # Wait for discovery
            import time
            time.sleep(3)
            
            # Find target device in discovered services
            target_cast_info = None
            
            if target_name:
                # Look for specific device
                for uuid, cast_info in browser.services.items():
                    if hasattr(cast_info, 'friendly_name') and cast_info.friendly_name == target_name:
                        target_cast_info = cast_info
                        logger.info(f"Found target device: {cast_info.friendly_name}")
                        break
                
                if not target_cast_info:
                    logger.warning(f"Device '{target_name}' not found, trying first available device")
            
            if not target_cast_info:
                # Use first available device
                for uuid, cast_info in browser.services.items():
                    if hasattr(cast_info, 'friendly_name'):
                        target_cast_info = cast_info
                        logger.info(f"Using first available device: {cast_info.friendly_name}")
                        break
            
            if not target_cast_info:
                logger.error("No Chromecast devices found on network")
                browser.stop_discovery()
                return False
            
            # Create Chromecast object directly from CastInfo
            # Note: Keep browser alive during connection as get_chromecast_from_cast_info needs active services
            self.cast = pychromecast.get_chromecast_from_cast_info(
                target_cast_info, self._zeroconf
            )
            
            # Wait for device to be ready
            logger.info(f"Waiting for {self.cast.name} to be ready...")
            self.cast.wait(timeout=10)
            
            # Now we can safely clean up the browser
            browser.stop_discovery()
            
            # Verify connection is working
            if not self.cast.status:
                raise Exception("Device status not available after connection")
            
            # Get media controller
            self.mc = self.cast.media_controller
            
            # Register status listener for media events
            self.status_listener = ChromecastMediaStatusListener(self.cast.name)
            self.mc.register_status_listener(self.status_listener)
            logger.info(f"Registered media status listener for {self.cast.name}")
            
            logger.info(f"Successfully connected to {self.cast.name}")
            logger.debug(f"Device status: {self.cast.status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Chromecast: {e}")
            self.disconnect()  # Clean up partial connection
            return False
    
    def disconnect(self):
        """Disconnect from current Chromecast device."""
        if self.cast:
            try:
                logger.info(f"Disconnecting from {self.cast.name}")
                
                # Unregister status listener if it exists
                if self.mc and self.status_listener:
                    try:
                        self.mc.unregister_status_listener(self.status_listener)
                        logger.debug("Unregistered media status listener")
                    except Exception as e:
                        logger.warning(f"Error unregistering status listener: {e}")
                
                self.cast.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.cast = None
                self.mc = None
                self.status_listener = None
    
    def is_connected(self) -> bool:
        """Check if currently connected to a Chromecast device."""
        if not self.cast or not self.mc:
            return False
        
        try:
            # Quick responsiveness check
            return self.cast.status is not None
        except Exception:
            return False
    
    def ensure_connected(self) -> bool:
        """Ensure we have a working connection, reconnect if needed."""
        if self.is_connected():
            return True
        
        logger.info("Connection lost, attempting to reconnect...")
        return self.connect()

    def play_media(self, url: str, media_info: dict = None, content_type: str = "audio/mp3") -> bool:
        """
        Play media on the connected Chromecast with metadata.
        
        Args:
            url: Media URL to play
            media_info: Dictionary containing track metadata (title, artist, album, etc.)
            content_type: MIME type of the media
            
        Returns:
            True if successful, False otherwise
        """
        if not self.ensure_connected():
            logger.error("Cannot play media: no Chromecast connection")
            return False
        
        try:
            logger.info(f"Playing media on {self.cast.name}: {url}")
            
            if media_info:
                # Extract metadata from media_info
                title = media_info.get("title", "Unknown Title")
                thumb = media_info.get("thumb")
                
                # Get nested media_info if present
                nested_info = media_info.get("media_info", {})
                artist = nested_info.get("artist") or media_info.get("artist", "Unknown Artist")
                album = nested_info.get("album") or media_info.get("album", "Unknown Album")
                year = nested_info.get("year") or media_info.get("year")
                
                # Get metadata if present
                metadata_dict = media_info.get("metadata", {})
                
                # Create metadata dictionary for pychromecast
                metadata = {
                    "metadataType": metadata_dict.get("metadataType", 3),  # MUSIC_TRACK = 3
                    "title": title,
                    "artist": artist,
                    "albumName": album,
                }
                
                if year:
                    metadata["releaseDate"] = str(year)
                
                # Add album art if available
                if thumb:
                    metadata["images"] = [{"url": thumb}]
                
                # Play media with metadata
                logger.info(f"Playing with metadata: {title} by {artist} from {album}")
                logger.debug(f"Metadata being sent: {metadata}")
                
                self.mc.play_media(url, content_type, title=title, thumb=thumb, metadata=metadata)
                
            else:
                # Play media without metadata (fallback)
                logger.info("Playing media without metadata")
                self.mc.play_media(url, content_type)
            
            # Wait for media to start
            self.mc.block_until_active(timeout=10)
            
            logger.info("Media started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to play media: {e}")
            # Fallback to basic playback without metadata
            try:
                logger.info("Attempting fallback playback without metadata")
                self.mc.play_media(url, content_type)
                self.mc.block_until_active(timeout=10)
                return True
            except Exception as fallback_e:
                logger.error(f"Fallback playback also failed: {fallback_e}")
                return False
    
    def pause(self) -> bool:
        """Pause current media playback."""
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
        """Resume current media playback."""
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
        """Stop current media playback."""
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
        """
        Set Chromecast volume.
        
        Args:
            volume: Volume level between 0.0 and 1.0
            
        Returns:
            True if successful, False otherwise
        """
        if not self.ensure_connected():
            return False
        
        try:
            # Clamp volume to valid range
            volume = max(0.0, min(1.0, volume))
            self.cast.set_volume(volume)
            logger.info(f"Volume set to {volume:.1%}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    def get_volume(self) -> Optional[float]:
        """
        Get current Chromecast volume.
        
        Returns:
            Volume level between 0.0 and 1.0, or None if not connected
        """
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
        """Get current Chromecast status."""
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
            
            # Add media controller status if available
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


# Singleton instance for compatibility with existing code
_service_instance = None

def get_chromecast_service(device_name: Optional[str] = None) -> PyChromecastServiceOnDemand:
    """
    Get singleton instance of the on-demand Chromecast service.
    
    This function provides compatibility with the existing singleton pattern
    while using the new simplified implementation.
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = PyChromecastServiceOnDemand(device_name)
        # Initialize zeroconf immediately for singleton usage
        _service_instance._zeroconf = Zeroconf()
        logger.info("Initialized on-demand Chromecast service")
    
    # Update device name if different
    if device_name and device_name != _service_instance.device_name:
        _service_instance.device_name = device_name
        logger.info(f"Updated target device to: {device_name}")
    
    return _service_instance
