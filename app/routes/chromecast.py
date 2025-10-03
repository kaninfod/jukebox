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

