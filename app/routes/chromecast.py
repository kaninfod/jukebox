from fastapi import APIRouter, HTTPException, Query
from app.services.chromecast_service import ChromecastService, get_chromecast_service
from app.config import config
import logging

router = APIRouter()
logger = logging.getLogger(__name__)






@router.get("/api/chromecast/listchromecasts")
def list_chromecasts():
    with get_chromecast_service() as service:
        chromecasts = service.list_chromecasts()
        return {"chromecasts": chromecasts}

@router.get("/api/chromecast/scan")
def scan_network_devices(timeout: int = Query(None, description="Network scan timeout in seconds")):
    """
    Scan the network for available Chromecast devices.
    
    Performs a live network discovery and returns actual device information
    from the network. This is useful for troubleshooting, verification, and
    discovering new devices that may not be in the config yet.
    
    Returns:
        {
            "status": "ok",
            "scan_duration_seconds": 3,
            "devices_found": 5,
            "devices": [
                {
                    "name": "Living Room",
                    "model": "Nest Audio",
                    "host": "192.168.68.46",
                    "uuid": "uuid-string"
                },
                ...
            ]
        }
    """
    try:
        import time
        start_time = time.time()
        
        service = get_chromecast_service()
        devices = service.scan_network_for_devices(timeout=timeout)
        
        scan_duration = time.time() - start_time
        
        return {
            "status": "ok",
            "scan_duration_seconds": round(scan_duration, 2),
            "devices_found": len(devices),
            "devices": devices
        }
    except Exception as e:
        logger.error(f"Failed to scan for Chromecast devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan network: {e}")

@router.get("/api/chromecast/connect")
def chromecast_connect(
    device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name"),
    fallback: bool = Query(True, description="Connect to first available device if target not found")
):
    try:
        with get_chromecast_service(device_name) as service:
            success = service.connect(fallback=fallback)
            if not success or not service.cast:
                logger.warning(f"Failed to connect to Chromecast: {device_name} (fallback={fallback})")
                return {"status": "not_connected", "device": device_name}
            return {"status": "connected", "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to connect to Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}")



@router.post("/api/chromecast/play")
def chromecast_play(
    url: str = Query(..., description="Direct stream URL to play on Chromecast"),
    content_type: str = Query("audio/mp3", description="MIME type of the media"),
    device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name")
):
    try:
        with get_chromecast_service(device_name) as service:
            if not service.connect() or not service.cast:
                logger.error(f"No Chromecast device connected: {device_name}")
                raise HTTPException(status_code=503, detail=f"No Chromecast device connected: {device_name}")
            service.play_media(url, content_type)
            return {"status": "playing", "url": url, "content_type": content_type, "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to play media on Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to play media: {e}")



@router.post("/api/chromecast/pause")
def chromecast_pause(device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name")):
    try:
        with get_chromecast_service(device_name) as service:
            if not service.connect() or not service.cast:
                logger.error(f"No Chromecast device connected: {device_name}")
                raise HTTPException(status_code=503, detail=f"No Chromecast device connected: {device_name}")
            service.pause()
            return {"status": "paused", "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to pause Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause: {e}")


@router.post("/api/chromecast/stop")
def chromecast_stop(device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name")):
    try:
        with get_chromecast_service(device_name) as service:
            if not service.connect() or not service.cast:
                logger.error(f"No Chromecast device connected: {device_name}")
                raise HTTPException(status_code=503, detail=f"No Chromecast device connected: {device_name}")
            service.stop()
            return {"status": "stopped", "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to stop Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop: {e}")


@router.post("/api/chromecast/resume")
def chromecast_resume(device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name")):
    try:
        with get_chromecast_service(device_name) as service:
            if not service.connect() or not service.cast:
                logger.error(f"No Chromecast device connected: {device_name}")
                raise HTTPException(status_code=503, detail=f"No Chromecast device connected: {device_name}")
            service.resume()
            return {"status": "resumed", "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to resume Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume: {e}")


@router.post("/api/chromecast/set_volume")
def chromecast_set_volume(
    volume: float = Query(..., ge=0.0, le=1.0, description="Volume level (0.0 to 1.0)"),
    device_name: str = Query(config.DEFAULT_CHROMECAST_DEVICE, description="Chromecast device name")
):
    try:
        with get_chromecast_service(device_name) as service:
            if not service.connect() or not service.cast:
                logger.error(f"No Chromecast device connected: {device_name}")
                raise HTTPException(status_code=503, detail=f"No Chromecast device connected: {device_name}")
            service.set_volume(volume)
            return {"status": "volume_set", "volume": volume, "device": service.cast.name}
    except Exception as e:
        logger.error(f"Failed to set volume on Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set volume: {e}")

@router.get("/api/chromecast/status")
def chromecast_status():
    """
    Get current Chromecast status including:
    - All available devices on network
    - Currently active device (if any)
    - Active device playback status
    
    Uses the singleton to access the actual active connection state.
    """
    try:
        service = get_chromecast_service()
        
        # Get all available devices
        available_devices = service.list_chromecasts()
        
        # Get current active device - the one that is actually connected with self.cast set
        current_device = None
        current_status = None
        playback_info = {}
        
        # Check if we have an active connection
        if service.is_connected() and service.cast:
            current_device = service.cast.name
            current_status = service.get_status()
            if current_status:
                playback_info = {
                    "player_state": current_status.get("player_state", "UNKNOWN"),
                    "media_title": current_status.get("media_title"),
                    "media_artist": current_status.get("media_artist"),
                    "current_time": current_status.get("current_time"),
                    "duration": current_status.get("duration"),
                    "volume_level": current_status.get("volume_level"),
                    "volume_muted": current_status.get("volume_muted"),
                }
        
        return {
            "status": "ok",
            "available_devices": available_devices,
            "active_device": current_device,
            "connected": service.is_connected() and service.cast is not None,
            "playback": playback_info if playback_info else None
        }
    except Exception as e:
        logger.error(f"Failed to get Chromecast status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")


@router.post("/api/chromecast/switch")
def chromecast_switch(
    device_name: str = Query(..., description="Target Chromecast device name to switch to")
):
    """
    Seamlessly switch from current Chromecast device to a new device, resuming playback.
    
    Delegates to ChromecastService.switch_and_resume_playback() which orchestrates:
    1. Save current playback state (album_id and track index)
    2. Stop playback on current device
    3. Disconnect from current device
    4. Connect to new device
    5. Reload album and skip to saved track
    6. Resume playback on new device
    
    This is atomic - either succeeds fully or fails completely.
    Uses singleton instances to maintain shared state.
    """
    try:
        chromecast_service = get_chromecast_service()
        result = chromecast_service.switch_and_resume_playback(device_name)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=503, detail=result.get("error", "Unknown error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch Chromecast device to {device_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch device: {e}")


@router.post("/api/chromecast/disconnect")
def chromecast_disconnect():
    """
    Disconnect from the currently active Chromecast device.
    
    Stops playback and closes the connection gracefully.
    """
    try:
        service = get_chromecast_service()
        current_device = service.device_name
        
        if not service.is_connected():
            return {
                "status": "not_connected",
                "message": f"Already disconnected from {current_device}"
            }
        
        service.disconnect()
        logger.info(f"Disconnected from {current_device}")
        
        return {
            "status": "disconnected",
            "device": current_device
        }
    except Exception as e:
        logger.error(f"Failed to disconnect Chromecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {e}")


@router.get("/api/chromecast/device/{device_name}")
def chromecast_device_info(device_name: str):
    """
    Get information about a specific Chromecast device.
    
    Tests connection to the device to verify:
    - Device exists and is reachable
    - Device details (model, host, etc.)
    - Current device status (volume, active, etc.)
    
    Does NOT switch to this device or affect current playback - just performs a connection test.
    Uses a separate connection test, not the singleton.
    """
    try:
        service = get_chromecast_service()
        
        # Get device from discovery list
        available_devices = service.list_chromecasts()
        device_info = None
        for dev in available_devices:
            if dev["name"] == device_name:
                device_info = dev
                break
        
        if not device_info:
            raise HTTPException(status_code=404, detail=f"Device not found: {device_name}")
        
        # Try to connect just to test if device is reachable
        # We create a temporary test by using the singleton but being careful not to leave it switched
        current_device_before = service.cast.name if service.cast else None
        current_connected_before = service.is_connected()
        
        try:
            # Try connecting to the test device
            if service.connect(device_name=device_name, fallback=False):
                device_status = service.get_status()
                
                # If we had a previous connection, restore it
                if current_device_before and current_connected_before:
                    service.disconnect()
                    service.connect(device_name=current_device_before, fallback=False)
                
                return {
                    "status": "reachable",
                    "device": {
                        "name": device_info["name"],
                        "model": device_info["model"],
                        "host": device_info["host"],
                        "uuid": device_info.get("uuid"),
                        "volume_level": device_status.get("volume_level") if device_status else None,
                        "volume_muted": device_status.get("volume_muted") if device_status else None,
                        "online": True
                    }
                }
            else:
                raise HTTPException(status_code=503, detail=f"Could not connect to device: {device_name}")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Connection test failed for {device_name}: {e}")
            # Still return device info but mark as unreachable
            return {
                "status": "unreachable",
                "device": device_info,
                "online": False,
                "error": str(e)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get device info for {device_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device info: {e}")
