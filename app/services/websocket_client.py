"""
WebSocket client for Home Assistant integration.
Handles real-time state updates from Home Assistant.
"""
import json
import asyncio
import websockets
import threading
from app.config import config

from app.config import config

# WebSocket connection state
websocket_connection = None
websocket_task = None
is_websocket_running = False


async def handle_state_change(event_data):
    """Handle state change events from Home Assistant WebSocket"""
    try:
        from app.main import get_screen_manager
        from app.database import get_ytmusic_data_by_yt_id
        
        # Get screen manager
        screen_manager = get_screen_manager()
        
        # Check if this is the media player we're interested in
        entity_id = event_data.get("entity_id")
        if entity_id != config.MEDIA_PLAYER_ENTITY_ID:
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
                print(f"WebSocket: Updating display with: {media_artist} - {media_title} ({media_album})")
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
                screen_manager.render()  # Force render
                print(f"WebSocket: Display updated and rendered")
            else:
                print("WebSocket: No home screen found in screen manager")
        else:
            print("WebSocket: No screen manager available")
        
        print(f"WebSocket: Updated jukebox with: {media_artist} - {media_title} ({media_album})")
        
    except Exception as e:
        print(f"WebSocket: Error handling state change: {e}")


async def websocket_client():
    """WebSocket client to connect to Home Assistant"""
    global websocket_connection, is_websocket_running
    
    try:
        print("WebSocket: Connecting to Home Assistant...")
        
        async with websockets.connect(config.HA_WS_URL) as websocket:
            websocket_connection = websocket
            is_websocket_running = True
            
            # Step 1: Receive auth_required message
            auth_required = await websocket.recv()
            print(f"WebSocket: {auth_required}")
            
            # Step 2: Send authentication
            auth_message = {
                "type": "auth",
                "access_token": config.HA_TOKEN
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
        return {"status": "error", "message": f"Failed to start WebSocket: {str(e)}"}


def websocket_status():
    """Get WebSocket connection status"""
    return {
        "is_running": is_websocket_running,
        "connection_active": websocket_connection is not None
    }


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
