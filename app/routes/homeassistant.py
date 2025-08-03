"""
Home Assistant integration routes for the jukebox.
Handles fetching state from Home Assistant entities.
"""
from fastapi import APIRouter, HTTPException
import requests
import json
import asyncio
import websockets
import threading

router = APIRouter()

# Home Assistant configuration
HA_BASE_URL = "http://192.168.68.100:8123"
HA_WS_URL = "ws://192.168.68.100:8123/api/websocket"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1OGUxMjRkNjNkODU0ZGRmODVmNmY4YjVmYWNiMWRjMCIsImlhdCI6MTc1NDA2Nzk0MCwiZXhwIjoyMDY5NDI3OTQwfQ.UMME9LQrS2NzEkscVi-ZTneCJ_pJ3DXK6sD-3BEo7g4"

# WebSocket connection state
websocket_connection = None
websocket_task = None
is_websocket_running = False


@router.get("/homeassistant/entity/{entity_id}")
def get_entity_state(entity_id: str):
    """Get the state of a Home Assistant entity"""
    try:
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        url = f"{HA_BASE_URL}/api/states/{entity_id}"
        
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
    return get_entity_state("media_player.ytube_music_player")


@router.get("/homeassistant/ytube_music_player/volume")
def get_ytube_music_player_volume():
    """Get just the volume level of the YouTube Music player"""
    try:
        entity_data = get_entity_state("media_player.ytube_music_player")
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
        from app.devices.mqtt import (
            publish_volume, publish_status, publish_artist, 
            publish_album, publish_track, publish_year, publish_yt_id
        )
        from app.main import screen_manager
        from app.database import get_ytmusic_data_by_yt_id
        
        entity_data = get_entity_state("media_player.ytube_music_player")
        
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
        
        # Use database data to fill in missing information
        if db_data:
            print(f"Found database entry for yt_id: {yt_id}")
            # Prefer database data for album, artist, year, and image if available
            media_album = db_data.get("album_name") or media_album
            media_artist = db_data.get("artist_name") or media_artist
            media_year = str(db_data.get("year", "")) if db_data.get("year") else ""
            media_image = db_data.get("thumbnail") or media_image
            # Keep the track title from HA since it's current playing track
        else:
            media_year = ""  # Year not typically available from HA media player
        
        # Map Home Assistant media player states to jukebox PlayerStatus enum values
        state_mapping = {
            "playing": "play",      # HA "playing" -> PlayerStatus.PLAY
            "paused": "pause",      # HA "paused" -> PlayerStatus.PAUSE  
            "idle": "standby",      # HA "idle" -> PlayerStatus.STANDBY
            "off": "standby",       # HA "off" -> PlayerStatus.STANDBY
            "unavailable": "standby" # HA "unavailable" -> PlayerStatus.STANDBY
        }
        
        jukebox_state = state_mapping.get(state, "standby")
        
        # Update the display if screen manager is available
        if screen_manager:
            home_screen = screen_manager.screens.get('home')
            if home_screen:
                # Update screen with current media info
                home_screen.set_track_info(
                    artist=media_artist,
                    album=media_album,
                    year=media_year,
                    track=media_title,
                    image_url=media_image,
                    yt_id=yt_id
                )
                
                # Update player status and volume on screen
                home_screen.set_player_status(jukebox_state)
                home_screen.volume = volume_percent
                
                # Switch to home screen and render
                screen_manager.switch_to_screen("home")
        
        # Publish all information to MQTT
        publish_artist(media_artist)
        publish_album(media_album) 
        publish_track(media_title)
        publish_status(jukebox_state)
        publish_volume(str(volume_percent))
        publish_year(media_year)
        publish_yt_id(yt_id)
        
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


async def handle_state_change(event_data):
    """Handle state change events from Home Assistant WebSocket"""
    try:
        from app.devices.mqtt import (
            publish_volume, publish_status, publish_artist, 
            publish_album, publish_track, publish_year, publish_yt_id
        )
        from app.main import screen_manager
        from app.database import get_ytmusic_data_by_yt_id
        
        # Check if this is the media player we're interested in
        entity_id = event_data.get("entity_id")
        if entity_id != "media_player.ytube_music_player":
            return
            
        new_state = event_data.get("new_state", {})
        state = new_state.get("state", "idle")
        attributes = new_state.get("attributes", {})
        
        print(f"WebSocket: Media player state changed to: {state}")
        
        # Extract media information from Home Assistant
        media_title = attributes.get("media_title", "Unknown Track")
        media_artist = attributes.get("media_artist", "Unknown Artist")
        media_album = attributes.get("media_album_name", "Unknown Album")
        media_image = attributes.get("entity_picture")
        media_id = attributes.get("_media_id", "")
        
        # Extract YouTube ID
        yt_id = media_id if media_id else ""
        
        # Extract volume and convert to percentage
        volume_level = attributes.get("volume_level", 0.75)
        volume_percent = int(volume_level * 100)
        
        # Try to get additional data from database using yt_id
        db_data = get_ytmusic_data_by_yt_id(yt_id) if yt_id else None
        
        # Use database data to fill in missing information
        if db_data:
            print(f"WebSocket: Found database entry for yt_id: {yt_id}")
            # Prefer database data for album, artist, year, and image if available
            media_album = db_data.get("album_name") or media_album
            media_artist = db_data.get("artist_name") or media_artist
            media_year = str(db_data.get("year", "")) if db_data.get("year") else ""
            media_image = db_data.get("thumbnail") or media_image
            # Keep the track title from HA since it's current playing track
        else:
            media_year = ""
        
        # Map Home Assistant media player states to jukebox PlayerStatus enum values
        state_mapping = {
            "playing": "play",      # HA "playing" -> PlayerStatus.PLAY
            "paused": "pause",      # HA "paused" -> PlayerStatus.PAUSE  
            "idle": "standby",      # HA "idle" -> PlayerStatus.STANDBY
            "off": "standby",       # HA "off" -> PlayerStatus.STANDBY
            "unavailable": "standby" # HA "unavailable" -> PlayerStatus.STANDBY
        }
        
        jukebox_state = state_mapping.get(state, "standby")
        
        # Update the display if screen manager is available
        if screen_manager:
            home_screen = screen_manager.screens.get('home')
            if home_screen:
                # Update screen with current media info
                home_screen.set_track_info(
                    artist=media_artist,
                    album=media_album,
                    year=media_year,
                    track=media_title,
                    image_url=media_image,
                    yt_id=yt_id
                )
                
                # Update player status and volume on screen
                home_screen.set_player_status(jukebox_state)
                home_screen.volume = volume_percent
                
                # Switch to home screen and render
                screen_manager.switch_to_screen("home")
        
        # Publish all information to MQTT
        publish_artist(media_artist)
        publish_album(media_album) 
        publish_track(media_title)
        publish_status(jukebox_state)
        publish_volume(str(volume_percent))
        publish_year(media_year)
        publish_yt_id(yt_id)
        
        print(f"WebSocket: Updated jukebox with: {media_artist} - {media_title} ({media_album})")
        
    except Exception as e:
        print(f"WebSocket: Error handling state change: {e}")


async def websocket_client():
    """WebSocket client to connect to Home Assistant"""
    global websocket_connection, is_websocket_running
    
    try:
        print("WebSocket: Connecting to Home Assistant...")
        
        async with websockets.connect(HA_WS_URL) as websocket:
            websocket_connection = websocket
            is_websocket_running = True
            
            # Step 1: Receive auth_required message
            auth_required = await websocket.recv()
            print(f"WebSocket: {auth_required}")
            
            # Step 2: Send authentication
            auth_message = {
                "type": "auth",
                "access_token": HA_TOKEN
            }
            await websocket.send(json.dumps(auth_message))
            
            # Step 3: Receive auth_ok
            auth_response = await websocket.recv()
            print(f"WebSocket: {auth_response}")
            
            # Step 4: Subscribe to state_changed events for our entity
            subscribe_message = {
                "id": 1,
                "type": "subscribe_events",
                "event_type": "state_changed"
            }
            await websocket.send(json.dumps(subscribe_message))
            
            # Step 5: Receive subscription confirmation
            subscribe_response = await websocket.recv()
            print(f"WebSocket: {subscribe_response}")
            
            print("WebSocket: Connected and subscribed to state changes")
            
            # Step 6: Listen for events
            async for message in websocket:
                # Check if we should stop (for graceful shutdown)
                if not is_websocket_running:
                    print("WebSocket: Shutdown requested, stopping message loop")
                    break
                    
                try:
                    data = json.loads(message)
                    
                    # Check if this is a state_changed event
                    if (data.get("type") == "event" and 
                        data.get("event", {}).get("event_type") == "state_changed"):
                        
                        event_data = data.get("event", {}).get("data", {})
                        await handle_state_change(event_data)
                        
                except json.JSONDecodeError:
                    print(f"WebSocket: Invalid JSON received: {message}")
                except Exception as e:
                    print(f"WebSocket: Error processing message: {e}")
                    
    except Exception as e:
        print(f"WebSocket: Connection error: {e}")
    finally:
        is_websocket_running = False
        websocket_connection = None
        print("WebSocket: Disconnected")


def start_websocket_background():
    """Start WebSocket client in background thread"""
    def run_websocket():
        asyncio.new_event_loop().run_until_complete(websocket_client())
    
    global websocket_task
    if not is_websocket_running:
        websocket_task = threading.Thread(target=run_websocket, daemon=True)
        websocket_task.start()
        return True
    return False


@router.get("/homeassistant/websocket/start")
def start_websocket():
    """Start WebSocket connection to Home Assistant"""
    try:
        if is_websocket_running:
            return {"status": "already_running", "message": "WebSocket is already connected"}
        
        success = start_websocket_background()
        if success:
            return {"status": "starting", "message": "WebSocket connection initiated"}
        else:
            return {"status": "failed", "message": "Failed to start WebSocket"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start WebSocket: {str(e)}")


@router.get("/homeassistant/websocket/status")
def websocket_status():
    """Get WebSocket connection status"""
    return {
        "is_running": is_websocket_running,
        "connection_active": websocket_connection is not None
    }


@router.get("/homeassistant/websocket/stop")
def stop_websocket():
    """Stop WebSocket connection"""
    global is_websocket_running, websocket_connection, websocket_task
    
    print("Stopping WebSocket connection...")
    is_websocket_running = False
    
    # Don't try to close the websocket during shutdown - just mark it as stopped
    # The connection will be closed when the process terminates
    websocket_connection = None
    
    # Wait a moment for the background thread to notice the flag change
    import time
    time.sleep(0.1)
    
    return {"status": "stopped", "message": "WebSocket connection terminated"}


@router.post("/homeassistant/ytube_music_player/play_media")
def play_media_on_ytube_music_player(media_content_id: str, media_content_type: str = "album"):
    """Play media on the YouTube Music player via Home Assistant"""
    try:
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": "media_player.ytube_music_player",
            "media_content_id": media_content_id,
            "media_content_type": media_content_type
        }
        
        url = f"{HA_BASE_URL}/api/services/media_player/play_media"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Media playback started",
            "media_content_id": media_content_id,
            "media_content_type": media_content_type,
            "entity_id": "media_player.ytube_music_player"
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
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare the service call payload
        payload = {
            "entity_id": "media_player.ytube_music_player",
            "volume_level": volume_level
        }
        
        url = f"{HA_BASE_URL}/api/services/media_player/volume_set"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        # Convert to percentage for response
        volume_percent = int(volume_level * 100)
        
        return {
            "status": "success",
            "message": "Volume set successfully",
            "volume_level": volume_level,
            "volume_percent": volume_percent,
            "entity_id": "media_player.ytube_music_player"
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



