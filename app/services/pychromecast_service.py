
import pychromecast
import zeroconf
from typing import Optional
import logging

logger = logging.getLogger(__name__)



from pychromecast.discovery import CastBrowser, SimpleCastListener
from zeroconf import Zeroconf
import threading
import time

class PyChromecastService:

    _instance = None
    _last_device_name = None
    # {uuid: mdns_name}
    _devices = {}
    _browser = None
    _zeroconf = None
    _listener = None
    _lock = threading.Lock()

    def __init__(self, device_name=None):
        """Initialize the Chromecast service singleton instance."""
        self.device_name = device_name
        self.cast = None
        self.mc = None
        self._connection_attempted = False
        # Start zeroconf, browser, and listener if not already started
        if not self._zeroconf:
            self._zeroconf = Zeroconf()
        if not self._listener:
            self._listener = self._Listener(self)
        if not self._browser:
            self._browser = CastBrowser(self._listener, self._zeroconf)
            self._browser.start_discovery()
            logger.info("Started Chromecast discovery - devices will be discovered in background")


    
    @classmethod
    def get_instance(cls, device_name: Optional[str] = None):
        if cls._instance is None:
            cls._instance = cls(device_name)
            cls._last_device_name = device_name
            # Don't connect immediately - let discovery run in background
            logger.info("PyChromecastService initialized with lazy connection strategy")
        else:
            # Only reconnect if a new device name is requested
            if device_name and cls._last_device_name != device_name:
                cls._instance.device_name = device_name
                cls._instance._connection_attempted = False  # Reset connection flag
                cls._last_device_name = device_name
        return cls._instance




    def list_chromecasts(self):
        """Return a list of discovered Chromecasts with friendly name, model, and host."""
        chromecasts = []
        with self._lock:
            for uuid, mdns_name in self._devices.items():
                friendly_name = None
                model_name = None
                host = None
                
                # Try to get info from CastBrowser services
                if self._browser and hasattr(self._browser, 'services'):
                    # Try different key formats
                    service_info = None
                    for key_candidate in [uuid, str(uuid)]:
                        service_info = self._browser.services.get(key_candidate)
                        if service_info:
                            break
                    
                    if service_info:
                        # service_info is already a CastInfo object - use directly
                        friendly_name = getattr(service_info, 'friendly_name', None)
                        model_name = getattr(service_info, 'model_name', None)
                        host = getattr(service_info, 'host', None)
                        
                        logger.debug(f"Extracted: friendly_name={friendly_name}, model_name={model_name}, host={host}")
                    else:
                        logger.debug(f"No service info found for UUID: {uuid}")
                
                chromecasts.append({
                    "uuid": str(uuid),
                    "mdns_name": mdns_name,
                    "friendly_name": friendly_name,
                    "model_name": model_name,
                    "host": host
                })
        return chromecasts

    def connect(self):
        """Select and connect to a Chromecast device based on device_name or fallback."""
        # If we already tried connecting recently and failed, don't retry immediately
        if self._connection_attempted and (self.cast is None or self.mc is None):
            with self._lock:
                uuid_list = list(self._devices.keys())
            if not uuid_list:
                logger.debug("No devices discovered yet for connection retry")
                return
        
        # Wait for discovery to find devices, but with retries
        max_retries = 3  # Reduced retries since discovery runs in background
        retry_delay = 1  # Shorter delay
        
        for attempt in range(max_retries):
            with self._lock:
                uuid_list = list(self._devices.keys())
            
            if uuid_list:
                break
                
            logger.info(f"Discovery attempt {attempt + 1}/{max_retries}: {len(uuid_list)} devices found, waiting {retry_delay}s...")
            time.sleep(retry_delay)
        
        with self._lock:
            uuid_list = list(self._devices.keys())
        logger.info(f"Discovered Chromecast devices: {[self._devices[uuid] for uuid in uuid_list]}")

        if not uuid_list:
            logger.warning("No Chromecast devices found after discovery attempts. Will retry when devices are found.")
            self._connection_attempted = True
            self.cast = None
            self.mc = None
            return

        # Use comprehensive discovery to find and connect to the specific device
        try:
            target_cast_info = None
            
            # First, get all available chromecasts to ensure we have complete discovery
            logger.info("Getting all available Chromecasts for device selection...")
            chromecasts, _ = pychromecast.get_chromecasts(zeroconf_instance=self._zeroconf)
            
            if not chromecasts:
                logger.error("No Chromecast devices found on the network. Chromecast features will be disabled.")
                self._connection_attempted = True
                self.cast = None
                self.mc = None
                return
            
            if self.device_name:
                # Search for the specific device by friendly name
                logger.info(f"Attempting to connect to specific device: {self.device_name}")
                for chromecast_device in chromecasts:
                    if chromecast_device.name == self.device_name:
                        self.cast = chromecast_device
                        logger.info(f'Found and selected target device: {self.cast.name}')
                        break
                
                if not self.cast:
                    logger.warning(f'No Chromecast with name "{self.device_name}" found. Available devices: {[cc.name for cc in chromecasts]}. Falling back to first available.')
            
            if not self.cast:
                # Fallback: use first available device
                self.cast = chromecasts[0]
                logger.info(f'Fallback: selected first available Chromecast: {self.cast.name}')
            
            # Wait for the cast device to be ready with a timeout
            logger.info(f"Attempting to connect to Chromecast: {self.cast.name}...")
            self.cast.wait(timeout=10)
            
            # Verify the connection is working
            if not self.cast.status:
                raise Exception("Cast device status is not available")
                
            self.mc = self.cast.media_controller
            self._connection_attempted = True
            logger.info(f"Successfully connected to Chromecast: {self.cast.name} (status: {self.cast.status.display_name})")
            
        except Exception as e:
            logger.error(f"Error connecting to Chromecast: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Clean up any partial connection
            if hasattr(self, 'cast') and self.cast:
                try:
                    self.cast.disconnect()
                except:
                    pass
            self.cast = None
            self.mc = None
            self._connection_attempted = True



    def play_media(self, url: str, media_info: dict = None, content_type: str = "audio/mp3"):
        # Implement lazy connection - connect only when actually needed
        if not self.mc or not self.cast:
            logger.info("Chromecast not connected. Attempting connection now...")
            self.connect()
            
            if not self.mc or not self.cast:
                # Try waiting a bit for discovery if this is the first attempt
                if not self._connection_attempted:
                    logger.info("First connection attempt failed. Waiting for device discovery...")
                    time.sleep(3)  # Give discovery more time
                    self.connect()
                
                if not self.mc or not self.cast:
                    raise Exception("Failed to connect to a Chromecast device. Please check that Chromecast devices are available on the network.")
        
        # Verify the cast is still responsive
        try:
            if not self.cast.status:
                logger.warning("Cast device appears disconnected. Attempting to reconnect...")
                self._connection_attempted = False  # Reset to allow retry
                self.connect()
                if not self.mc or not self.cast:
                    raise Exception("Chromecast device is no longer responsive and reconnection failed.")
        except Exception as e:
            logger.warning(f"Error checking cast status: {e}. Attempting to reconnect...")
            self._connection_attempted = False  # Reset to allow retry
            self.connect()
            if not self.mc or not self.cast:
                raise Exception("Chromecast connection lost and reconnection failed.")
                
        logger.info(f"Casting media: {url} (type: {content_type})")
        try:
            self.mc.play_media(url, content_type)
            self.mc.block_until_active()
            self.mc.play()
        except Exception as e:
            logger.error(f"Error playing media on Chromecast: {e}")
            raise Exception(f"Failed to play media on Chromecast: {e}")

    def pause(self):
        if self.mc:
            self.mc.pause()

    def stop(self):
        if self.mc:
            self.mc.stop()

    def resume(self):
        if self.mc:
            self.mc.play()

    def set_volume(self, volume: float):
        if self.cast:
            self.cast.set_volume(volume)

    def ensure_connection(self):
        """Ensure we have a working Chromecast connection. Connect if needed."""
        if not self.cast or not self.mc or not self._is_cast_responsive():
            logger.info("Ensuring Chromecast connection...")
            self.connect()
            return self.cast is not None and self.mc is not None
        return True
    
    def _is_cast_responsive(self):
        """Check if the current cast connection is still responsive."""
        if not self.cast:
            return False
        try:
            # Quick check if cast is responsive
            return self.cast.status is not None
        except:
            return False
    
    def has_devices_available(self):
        """Check if any Chromecast devices have been discovered."""
        with self._lock:
            return len(self._devices) > 0

    def disconnect(self):
        if self.cast:
            self.cast.disconnect()
            logger.info("Disconnected from Chromecast.")


    class _Listener(SimpleCastListener):
        def __init__(self, service):
            super().__init__()
            self.service = service

        def add_cast(self, uuid, mdns_name):
            # Called when a new Chromecast is discovered
            with self.service._lock:
                self.service._devices[uuid] = mdns_name
                logger.info(f"Discovered Chromecast: {mdns_name} (uuid: {uuid})")

        def remove_cast(self, uuid, mdns_name, service):
            # Called when a Chromecast disappears
            with self.service._lock:
                if uuid in self.service._devices:
                    del self.service._devices[uuid]
                    logger.info(f"Removed Chromecast: {mdns_name} (uuid: {uuid})")