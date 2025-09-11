"""
Chromecast Device Manager

Handles Chromecast device switching and management centrally.
Subscribes to device change events and coordinates the switch process.
"""

import logging
from typing import Optional
from app.core.event_bus import EventBus, Event
from app.core.event_factory import EventType

logger = logging.getLogger(__name__)


class ChromecastDeviceManager:
    """
    Manages Chromecast device switching and coordination.
    
    This service:
    - Listens for CHROMECAST_DEVICE_CHANGED events
    - Coordinates device switching with proper flow
    - Provides feedback to the user
    - Manages the current active device state
    """
    
    def __init__(self, event_bus: EventBus, media_player=None):
        """
        Initialize the Chromecast Device Manager.
        
        Args:
            event_bus: Event bus for communication
            media_player: JukeboxMediaPlayer instance (for updating its chromecast service)
        """
        self.event_bus = event_bus
        self.media_player = media_player
        from app.config import config
        self.current_device = config.DEFAULT_CHROMECAST_DEVICE
        
        # Subscribe to device change events
        self.event_bus.subscribe(EventType.CHROMECAST_DEVICE_CHANGED, self._handle_device_change)
        
        logger.info(f"ChromecastDeviceManager initialized with default device: {self.current_device}")
    
    def _handle_device_change(self, event):
        """
        Handle Chromecast device change event.
        
        Args:
            event: Event with payload containing 'device_name'
        """
        new_device_name = event.payload.get("device_name")
        
        if not new_device_name:
            logger.warning("No device_name provided in CHROMECAST_DEVICE_CHANGED event")
            return
        
        if new_device_name == self.current_device:
            logger.info(f"Device '{new_device_name}' is already active")
            self._emit_message(f"📱 {new_device_name} is already connected", "info", 2)
            return
        
        logger.info(f"Switching Chromecast device from '{self.current_device}' to '{new_device_name}'")
        
        try:
            # Perform the device switch
            if self._switch_chromecast_device(new_device_name):
                # Switch successful
                old_device = self.current_device
                self.current_device = new_device_name
                
                logger.info(f"Successfully switched from '{old_device}' to '{new_device_name}'")
                self._emit_message(f"✅ Connected to {new_device_name}", "success", 3)
                
            else:
                # Switch failed
                logger.error(f"Failed to switch to '{new_device_name}'")
                self._emit_message(
                    f"❌ Failed to connect to {new_device_name}\\nPlease try another device", 
                    "error", 
                    4
                )
                
        except Exception as e:
            logger.error(f"Error during device switch to '{new_device_name}': {e}")
            self._emit_message(
                f"❌ Error connecting to {new_device_name}\\nDevice may be offline", 
                "error", 
                4
            )
    
    def _switch_chromecast_device(self, new_device_name: str) -> bool:
        """
        Perform the actual Chromecast device switch.
        
        Args:
            new_device_name: Name of the device to switch to
            
        Returns:
            True if switch successful, False otherwise
        """
        if not self.media_player or not self.media_player.cc_service:
            logger.error("No media player or chromecast service available")
            return False
        
        try:
            # Use the PyChromecastService's switch_device method
            return self.media_player.cc_service.switch_device(new_device_name)
            
        except Exception as e:
            logger.error(f"Error during device switch: {e}")
            return False
    
    def _emit_message(self, message: str, msg_type: str = "info", duration: int = 3):
        """
        Emit a message event to show user feedback.
        
        Args:
            message: Message text to display
            msg_type: Type of message (info, success, error)
            duration: Duration to show message in seconds
        """
        self.event_bus.emit(Event(
            type=EventType.SHOW_MESSAGE,
            payload={
                "message": message,
                "type": msg_type,
                "duration": duration
            }
        ))
    
    def get_current_device(self) -> str:
        """Get the name of the currently active Chromecast device."""
        return self.current_device
    
    def set_media_player(self, media_player):
        """
        Set or update the media player reference.
        
        Args:
            media_player: JukeboxMediaPlayer instance
        """
        self.media_player = media_player
        logger.info("Media player reference updated in ChromecastDeviceManager")
    
    def cleanup(self):
        """Clean up the device manager."""
        logger.info("ChromecastDeviceManager cleanup called")
        # No specific cleanup needed - event bus handles unsubscription
