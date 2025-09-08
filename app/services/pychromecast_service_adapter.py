"""
Drop-in replacement adapter for PyChromecastService.

This module provides a compatibility layer that allows the new on-demand
implementation to be used as a drop-in replacement for the existing
background discovery implementation.

Usage:
    # Replace this import:
    # from app.services.pychromecast_service import PyChromecastService
    
    # With this:
    from app.services.pychromecast_service_adapter import PyChromecastService
    
    # All existing code should continue to work unchanged
"""

from .pychromecast_service_ondemand import PyChromecastServiceOnDemand, get_chromecast_service
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class PyChromecastService:
    """
    Compatibility adapter that provides the same interface as the original
    PyChromecastService but uses the new on-demand implementation internally.
    """
    
    # Class variables for singleton pattern compatibility
    _instance = None
    _last_device_name = None
    
    def __init__(self, device_name: Optional[str] = None):
        """Initialize with compatibility for original constructor."""
        self._service = PyChromecastServiceOnDemand(device_name)
        self.device_name = device_name
        
        # Initialize zeroconf immediately to match original behavior
        if not self._service._zeroconf:
            from zeroconf import Zeroconf
            self._service._zeroconf = Zeroconf()
    
    @classmethod
    def get_instance(cls, device_name: Optional[str] = None):
        """Singleton pattern compatibility."""
        if cls._instance is None:
            cls._instance = cls(device_name)
            cls._last_device_name = device_name
            logger.info("PyChromecastService initialized with on-demand implementation")
        else:
            # Update device name if different
            if device_name and cls._last_device_name != device_name:
                cls._instance.device_name = device_name
                cls._instance._service.device_name = device_name
                cls._last_device_name = device_name
        
        return cls._instance
    
    def list_chromecasts(self) -> List[Dict[str, str]]:
        """
        List discovered Chromecasts - compatibility method.
        
        Returns same format as original implementation:
        [{"uuid": str, "mdns_name": str, "friendly_name": str, "model_name": str, "host": str}]
        """
        devices = self._service.list_chromecasts()
        
        # Convert to original format
        result = []
        for device in devices:
            result.append({
                "uuid": device['uuid'],
                "mdns_name": f"{device['name']}.local",  # Approximate original format
                "friendly_name": device['name'],
                "model_name": device['model'],
                "host": device['host']
            })
        
        return result
    
    def connect(self):
        """Connect to Chromecast - compatibility method."""
        return self._service.connect()
    
    def disconnect(self):
        """Disconnect from Chromecast - compatibility method."""
        self._service.disconnect()
    
    def play_media(self, url: str, media_info: dict = None, content_type: str = "audio/mp3"):
        """
        Play media - compatibility method.
        
        Note: media_info parameter is ignored in the new implementation
        as it's not used in the official pychromecast examples.
        """
        if not self._service.play_media(url, content_type):
            raise Exception(f"Failed to play media on Chromecast: {url}")
    
    def pause(self):
        """Pause media - compatibility method."""
        self._service.pause()
    
    def stop(self):
        """Stop media - compatibility method."""
        self._service.stop()
    
    def resume(self):
        """Resume media - compatibility method."""
        self._service.resume()
    
    def set_volume(self, volume: float):
        """Set volume - compatibility method."""
        self._service.set_volume(volume)
    
    def ensure_connection(self) -> bool:
        """Ensure connection - compatibility method."""
        return self._service.ensure_connected()
    
    def has_devices_available(self) -> bool:
        """Check if devices are available - compatibility method."""
        devices = self._service.list_chromecasts()
        return len(devices) > 0
    
    # Properties for compatibility with existing code that might access these directly
    @property
    def cast(self):
        """Access to underlying cast object."""
        return self._service.cast
    
    @property
    def mc(self):
        """Access to underlying media controller."""
        return self._service.mc
    
    def _is_cast_responsive(self) -> bool:
        """Private method compatibility."""
        return self._service.is_connected()


# For backward compatibility, also provide the exact same interface
# that existing code might be importing
def get_chromecast_service_singleton(device_name: Optional[str] = None):
    """Alternative singleton accessor for compatibility."""
    return PyChromecastService.get_instance(device_name)
