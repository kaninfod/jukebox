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

@router.get("/homeassistant/entity/{entity_id}")
def get_entity_state(entity_id: str):
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


@router.get("/homeassistant/ytube_music_player")
def get_ytube_music_player_state():
    """Get the state of the YouTube Music player entity"""
    return get_entity_state(config.MEDIA_PLAYER_ENTITY_ID)


@router.get("/homeassistant/ytube_music_player/volume")
def get_ytube_music_player_volume():
    """Get just the volume level of the YouTube Music player"""
    try:
        entity_data = get_entity_state(config.MEDIA_PLAYER_ENTITY_ID)
        volume_level = entity_data.get("attributes", {}).get("volume_level", 0)
        
        # Convert from 0-1 range to 0-100 percentage
        volume_percent = int(volume_level * 100)
        
        return {
            "volume_level": volume_level,
            "volume_percent": volume_percent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get volume: {str(e)}")


@router.get("/homeassistant/ytube_music_player/sync")
def sync_with_ytube_music_player():
    """Synchronize jukebox state with YouTube Music player"""
    try:
        from app.main import get_screen_manager
        from app.database import get_ytmusic_data_by_yt_id
        
        # Get screen manager
        screen_manager = get_screen_manager()
        
        entity_data = get_entity_state(config.MEDIA_PLAYER_ENTITY_ID)
        
        # Get current state and attributes
        state = entity_data.get("state", "idle")
        attributes = entity_data.get("attributes", {})
        
        # Extract media information from Home Assistant
        media_title = attributes.get("media_title", "Unknown Track")
        media_artist = attributes.get("media_artist", "Unknown Artist")
        media_album = attributes.get("media_album_name", "Unknown Album")
        media_image = attributes.get("entity_picture")
        media_id = attributes.get("_media_id", "")
        
        # Extract YouTube ID from media_content_id if available
        yt_id = media_id if media_id else ""
        
        # Extract volume and convert to percentage
        volume_level = attributes.get("volume_level", 0.75)
        volume_percent = int(volume_level * 100)
        
        # Try to get additional data from database using yt_id
        db_data = get_ytmusic_data_by_yt_id(yt_id) if yt_id else None
        
        # Use database data to fill in missing information, especially for album names
        if db_data:
            print(f"Sync: Found database entry for yt_id: {yt_id}")
            
            # Special handling for album name - YouTube Music HA integration rarely provides it
            # Use database album name if:
            # 1. HA doesn't provide album name, OR
            # 2. HA provides generic "Unknown Album", OR  
            # 3. Database has a more specific album name
            if (not media_album or 
                media_album == "Unknown Album" or 
                (db_data.get("album_name") and db_data.get("album_name") != "Unknown Album")):
                if db_data.get("album_name"):
                    print(f"Sync: Using database album name: {db_data.get('album_name')} (HA provided: {media_album})")
                    media_album = db_data.get("album_name")
            
            # Use database data for other fields if HA data is missing or generic
            if not media_artist or media_artist == "Unknown Artist":
                media_artist = db_data.get("artist_name") or media_artist
            
            # Always use database year and thumbnail if available (HA rarely provides these)
            media_year = str(db_data.get("year", "")) if db_data.get("year") else ""
            if db_data.get("thumbnail"):
                media_image = db_data.get("thumbnail")
            
            # Keep the track title from HA since it's the current playing track
        else:
            media_year = ""  # Year not typically available from HA media player
        

        context = {
                "artist": media_artist,
                "album": media_album,
                "year": media_year,
                "track": media_title,
                "image_url": media_image,
                "yt_id": yt_id,
                "volume": volume_percent,
                "state": state
            }

        return context
        if screen_manager:
            home_screen = screen_manager.screens.get('home')
            screen_manager.switch_to_screen("home")
            screen_manager.render(context=context, force=True)

        # if screen_manager:
        #     home_screen = screen_manager.screens.get('home')
        #     if home_screen:
        #         print(f"Sync: Updating display with: {media_artist} - {media_title} ({media_album})")
        #         # Update screen with current media info
        #         home_screen.set_track_info(
        #             artist=media_artist,
        #             album=media_album,
        #             year=media_year,
        #             track=media_title,
        #             image_url=media_image,
        #             yt_id=yt_id
        #         )
                
        #         # Update player status and volume on screen
        #         home_screen.set_player_status(jukebox_state)
        #         home_screen.volume = volume_percent
                
        #         # Switch to home screen and render
        #         screen_manager.switch_to_screen("home")
        #         screen_manager.render()  # Force render
        #         print(f"Sync: Display updated and rendered")
        #     else:
        #         print("Sync: No home screen found in screen manager")
        else:
            print("Sync: No screen manager available")
        
        return {
            "status": "synchronized",
            "ha_state": state,
            "jukebox_state": jukebox_state,
            "volume_percent": volume_percent,
            "display_updated": screen_manager is not None,
            "database_used": db_data is not None,
            "synced_media": {
                "title": media_title,
                "artist": media_artist,
                "album": media_album,
                "year": media_year,
                "yt_id": yt_id,
                "image_url": media_image
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync: {str(e)}")


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


@router.post("/homeassistant/ytube_music_player/play_media")
def play_media_on_ytube_music_player(media_content_id: str, media_content_type: str = "album"):
    """Play media on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID,
            "media_content_id": media_content_id,
            "media_content_type": media_content_type
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/play_media"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Media playback started",
            "media_content_id": media_content_id,
            "media_content_type": media_content_type,
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to play media: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ytube_music_player/volume_set")
def set_volume_on_ytube_music_player(volume_level: float):
    """Set volume on the YouTube Music player via Home Assistant"""
    try:
        # Validate volume level (should be 0.0 to 1.0)
        if not 0.0 <= volume_level <= 1.0:
            raise HTTPException(status_code=400, detail="Volume level must be between 0.0 and 1.0")
        
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID,
            "volume_level": volume_level
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/volume_set"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        # Convert to percentage for response
        volume_percent = int(volume_level * 100)
        
        return {
            "status": "success",
            "message": "Volume set successfully",
            "volume_level": volume_level,
            "volume_percent": volume_percent,
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to set volume: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ytube_music_player/volume_percent/{volume_percent}")
def set_volume_by_percent(volume_percent: int):
    """Set volume by percentage (0-100) on the YouTube Music player"""
    # Validate percentage
    if not 0 <= volume_percent <= 100:
        raise HTTPException(status_code=400, detail="Volume percent must be between 0 and 100")
    
    # Convert percentage to 0.0-1.0 range
    volume_level = volume_percent / 100.0
    
    return set_volume_on_ytube_music_player(volume_level)


@router.post("/homeassistant/ytube_music_player/play_album/{album_id}")
def play_album_by_id(album_id: str):
    """Play a specific album by YouTube Music album ID"""
    return play_media_on_ytube_music_player(album_id, "album")


@router.post("/homeassistant/ytube_music_player/play_track/{track_id}")
def play_track_by_id(track_id: str):
    """Play a specific track by YouTube Music track ID"""
    return play_media_on_ytube_music_player(track_id, "track")


@router.post("/homeassistant/ytube_music_player/next_track")
def next_track_on_ytube_music_player():
    """Skip to next track on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/media_next_track"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Skipped to next track",
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to skip to next track: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ytube_music_player/previous_track")
def previous_track_on_ytube_music_player():
    """Skip to previous track on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/media_previous_track"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Skipped to previous track",
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to skip to previous track: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ytube_music_player/play_pause")
def play_pause_ytube_music_player():
    """Toggle play/pause on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/media_play_pause"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Toggled play/pause",
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle play/pause: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/homeassistant/ytube_music_player/stop")
def stop_ytube_music_player():
    """Stop playback on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
        url = f"{config.HA_BASE_URL}/api/services/media_player/media_stop"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Stopped playback",
            "entity_id": config.MEDIA_PLAYER_ENTITY_ID
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop playback: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


