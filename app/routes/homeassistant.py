from app.services.homeassistant_service import HomeAssistantService
"""
Home Assistant integration routes for the jukebox.
Handles fetching state from Home Assistant entities and media player control.
"""
from fastapi import APIRouter, HTTPException
import requests
from app.config import config

# Import WebSocket functionality from service
from app.services.websocket_client import (
    start_websocket_background, 
    start_websocket, 
    websocket_status, 
    stop_websocket
)

router = APIRouter()

@router.get("/homeassistant/ha_player/entity_state/{entity_id}")
def get_ha_player_entity_state(entity_id: str):
    """Get the state of a Home Assistant entity"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        url = f"{config.HA_BASE_URL}/api/states/{entity_id}"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        entity_data = response.json()
        
        return {
            "entity_id": entity_data.get("entity_id"),
            "state": entity_data.get("state"),
            "attributes": entity_data.get("attributes", {}),
            "last_changed": entity_data.get("last_changed"),
            "last_updated": entity_data.get("last_updated")
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch entity state: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/homeassistant/ha_player/state")
def get_ha_player_state():
    """Get the state of the Home Assistant media player entity"""
    return get_ha_player_entity_state(config.MEDIA_PLAYER_ENTITY_ID)


@router.get("/homeassistant/ha_player/volume")
def get_ha_player_volume():
    """Get just the volume level of the Home Assistant media player"""
    try:
        ha_service = HomeAssistantService()
        volume_level = ha_service.get_volume()
        volume_percent = int(volume_level * 100)
        return {
            "volume_level": volume_level,
            "volume_percent": volume_percent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get volume: {str(e)}")
    

@router.post("/homeassistant/ha_player/volume_set")
def set_ha_player_volume(volume_level: float):
    """Set volume on the Home Assistant player via Home Assistant"""
    try:
        if not 0.0 <= volume_level <= 1.0:
            raise HTTPException(status_code=400, detail="Volume level must be between 0.0 and 1.0")
        ha_service = HomeAssistantService()
        ok = ha_service.set_volume(volume_level)
        volume_percent = int(volume_level * 100)
        if ok:
            return {
                "status": "success",
                "message": "Volume set successfully",
                "volume_level": volume_level,
                "volume_percent": volume_percent,
                "entity_id": config.MEDIA_PLAYER_ENTITY_ID
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set volume via Home Assistant service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ha_player/set_volume_percent/{volume_percent}")
def set_ha_player_volume_percent(volume_percent: int):
    """Set volume by percentage (0-100) on the Home Assistant player"""
    if not 0 <= volume_percent <= 100:
        raise HTTPException(status_code=400, detail="Volume percent must be between 0 and 100")
    volume_level = volume_percent / 100.0
    return set_ha_player_volume(volume_level)


@router.post("/homeassistant/ha_player/play_pause")
def ha_player_play_pause():
    """Toggle play/pause on the Home Assistant player via Home Assistant"""
    try:
        ha_service = HomeAssistantService()
        ok = ha_service.play_pause()
        if ok:
            return {
                "status": "success",
                "message": "Toggled play/pause",
                "entity_id": config.MEDIA_PLAYER_ENTITY_ID
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to toggle play/pause via Home Assistant service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ha_player/stop")
def ha_player_stop():
    """Stop playback on the Home Assistant player via Home Assistant"""
    try:
        ha_service = HomeAssistantService()
        ok = ha_service.stop()
        if ok:
            return {
                "status": "success",
                "message": "Stopped playback",
                "entity_id": config.MEDIA_PLAYER_ENTITY_ID
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to stop playback via Home Assistant service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# WebSocket management endpoints
@router.get("/homeassistant/websocket/start")
def start_websocket_endpoint():
    """Start WebSocket connection to Home Assistant"""
    try:
        return start_websocket()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start WebSocket: {str(e)}")


@router.get("/homeassistant/websocket/status")
def websocket_status_endpoint():
    """Get WebSocket connection status"""
    return websocket_status()


@router.get("/homeassistant/websocket/stop")
def stop_websocket_endpoint():
    """Stop WebSocket connection"""
    return stop_websocket()