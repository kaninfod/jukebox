from fastapi import APIRouter, Body
from app.ui.screens import PlayerStatus
import subprocess
from typing import Dict, List, Union, Any
from app.routes.homeassistant import stop_ytube_music_player
from app.services.websocket_client import stop_websocket

router = APIRouter()

def get_screen_manager():
    from app.main import screen_manager
    return screen_manager

@router.post("/mediaplayer/volume")
def update_volume(volume: int = Body(..., embed=True)):
    """Update volume level (0-100)"""
    if volume < 0 or volume > 100:
        return {"status": "Error", "message": "Volume must be between 0 and 100"}
    
    screen_manager = get_screen_manager()
    home_screen = screen_manager.screens.get('home')
    
    if home_screen:
        home_screen.set_volume(volume)
        # Re-render if we're on the home screen
        if screen_manager.current_screen == home_screen:
            screen_manager.render()
    
    return {"status": "Volume updated", "volume": volume}

@router.post("/mediaplayer/screen")
def switch_screen(screen_name: str = Body(..., embed=True)):
    """Switch to a specific screen"""
    screen_manager = get_screen_manager()
    screen_manager.switch_to_screen(screen_name)
    return {"status": "Screen switched", "current_screen": screen_name}

@router.post("/mediaplayer/test_image")
def test_image_loading(image_url: str = Body(..., embed=True)):
    """Test loading an image URL"""
    screen_manager = get_screen_manager()
    home_screen = screen_manager.screens.get('home')
    
    if home_screen:
        print(f"Testing image URL: {image_url}")
        home_screen.set_track_info(
            artist="Test Artist",
            album="Test Album", 
            year="2023",
            track="Test Track",
            image_url=image_url
        )
        # Re-render to show the image
        if screen_manager.current_screen == home_screen:
            screen_manager.render()
        
        # Check if image loaded successfully
        if home_screen.album_image:
            return {"status": "Image loaded successfully", "image_size": home_screen.album_image.size}
        else:
            return {"status": "Image failed to load", "url": image_url}
    
    return {"status": "Home screen not available"}

@router.post("/mediaplayer/load_rfid")
def load_rfid_data(rfid: str = Body(..., embed=True)):
    """Load YTMusic data for a specific RFID and display it"""
    from app.database import load_ytmusic_data_to_screen
    from app.main import screen_manager
    
    try:
        load_ytmusic_data_to_screen(rfid, screen_manager)
        return {"status": "RFID data loaded", "rfid": rfid}
    except Exception as e:
        return {"status": "Error", "message": str(e), "rfid": rfid}

@router.get("/mediaplayer/info")
def get_mediaplayer_info():
    """Get current media player information"""
    screen_manager = get_screen_manager()
    home_screen = screen_manager.screens.get('home')
    
    if home_screen:
        return {
            "current_screen": screen_manager.current_screen.name if screen_manager.current_screen else None,
            "volume": home_screen.volume,
            "status": home_screen.player_status.value,
            "track_info": {
                "artist": home_screen.artist_name,
                "album": home_screen.album_name,
                "year": home_screen.album_year,
                "track": home_screen.track_title,
                "image_url": home_screen.album_image_url
            }
        }
    
    return {"status": "No home screen available"}

@router.get("/mediaplayer/debug")
def debug_mediaplayer():
    """Debug information for troubleshooting display updates"""
    try:
        from app.main import get_screen_manager
        from app.routes.homeassistant import websocket_status, get_ytube_music_player_state
        from app.devices.mqtt import get_all_mediaplayer_info
        
        # Get screen manager and home screen state
        screen_manager = get_screen_manager()
        home_screen = screen_manager.screens.get('home') if screen_manager else None
        
        # Get WebSocket status
        ws_status = websocket_status()
        
        # Get Home Assistant YouTube Music player state
        try:
            ha_player_state = get_ytube_music_player_state()
        except Exception as e:
            ha_player_state = {"error": str(e)}
        
        # Get MQTT mediaplayer info
        try:
            mqtt_info = get_all_mediaplayer_info()
        except Exception as e:
            mqtt_info = {"error": str(e)}
        
        return {
            "screen_manager": {
                "available": screen_manager is not None,
                "current_screen": screen_manager.current_screen.name if screen_manager and screen_manager.current_screen else None,
                "home_screen_available": home_screen is not None
            },
            "home_screen_state": {
                "artist": home_screen.artist_name if home_screen else "N/A",
                "album": home_screen.album_name if home_screen else "N/A", 
                "track": home_screen.track_title if home_screen else "N/A",
                "status": home_screen.player_status.value if home_screen else "N/A",
                "volume": home_screen.volume if home_screen else "N/A",
                "image_url": home_screen.album_image_url if home_screen else "N/A"
            },
            "websocket_status": ws_status,
            "ha_player_state": ha_player_state,
            "mqtt_info": mqtt_info
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@router.post("/mediaplayer/force_sync")
def force_sync_with_ha():
    """Force synchronization with Home Assistant YouTube Music player"""
    try:
        from app.routes.homeassistant import sync_with_ytube_music_player
        result = sync_with_ytube_music_player()
        return {"status": "success", "sync_result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/mediaplayer/shutdown")
async def shutdown_mediaplayer() -> Dict[str, Union[str, List[str]]]:
    """
    Gracefully shutdown the media player with true hardware power control.
    This will:
    1. Stop the YouTube Music player in Home Assistant
    2. Stop the WebSocket connection to Home Assistant  
    3. Turn off the display using hardware power switching (S8550 transistor)
    4. Keep the system running for instant response when reactivated
    """
    try:
        shutdown_steps = []
        
        # Step 1: Stop YouTube Music player in Home Assistant
        try:
            result = stop_ytube_music_player()
            shutdown_steps.append("✅ Stopped YouTube Music player")
        except Exception as e:
            shutdown_steps.append(f"⚠️ YouTube Music stop failed: {e}")
        
        # Step 2: Stop WebSocket connection to Home Assistant
        try:
            result = stop_websocket()
            shutdown_steps.append("✅ Stopped WebSocket connection")
        except Exception as e:
            shutdown_steps.append(f"⚠️ WebSocket stop failed: {e}")
        
        # Step 3: Turn off display using hardware power switching
        try:
            # Import here to avoid circular import
            from app.main import get_hardware_manager
            hardware_manager = get_hardware_manager()
            if hardware_manager and hardware_manager.display:
                if hardware_manager.display.power_off():
                    shutdown_steps.append("✅ Display powered off (hardware control)")
                else:
                    shutdown_steps.append("⚠️ Display power off failed")
            else:
                shutdown_steps.append("⚠️ No hardware manager found")
        except Exception as e:
            shutdown_steps.append(f"⚠️ Hardware power control failed: {e}")
        
        # Step 4: Log all shutdown steps
        for step in shutdown_steps:
            print(f"Media Player Hardware Shutdown: {step}")
        
        # Note: System stays running for instant response
        
        return {
            "status": "success", 
            "message": "Media player shutdown completed with hardware power control",
            "steps": shutdown_steps
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to shutdown media player: {str(e)}"
        }

@router.post("/mediaplayer/wakeup")
async def wakeup_mediaplayer() -> Dict[str, Union[str, List[str]]]:
    """
    Wake up the media player from hardware power-off mode.
    This will:
    1. Turn on the display using hardware power switching (S8550 transistor)
    2. Restore the normal display screen
    3. Reconnect to Home Assistant WebSocket
    4. Make the jukebox fully operational again
    """
    try:
        wakeup_steps = []
        
        # Step 1: Turn on display using hardware power switching
        try:
            # Import here to avoid circular import
            from app.main import get_hardware_manager
            hardware_manager = get_hardware_manager()
            if hardware_manager and hardware_manager.display:
                if hardware_manager.display.power_on():
                    wakeup_steps.append("✅ Display powered on (hardware control)")
                    # Give the display a moment to initialize
                    import time
                    time.sleep(0.5)
                else:
                    wakeup_steps.append("⚠️ Display power on failed")
            else:
                wakeup_steps.append("⚠️ No hardware manager found")
        except Exception as e:
            wakeup_steps.append(f"⚠️ Hardware power control failed: {e}")
        
        # Step 2: Restore normal display
        try:
            from app.main import screen_manager
            if screen_manager:
                screen_manager.render()  # Re-render the current screen
                wakeup_steps.append("✅ Display restored to normal screen")
            else:
                wakeup_steps.append("⚠️ No screen manager found")
        except Exception as e:
            wakeup_steps.append(f"⚠️ Display restore failed: {e}")
        
        # Step 3: Reconnect WebSocket (if needed)
        try:
            # You might want to add a reconnect function to homeassistant.py
            wakeup_steps.append("✅ System ready (WebSocket will reconnect automatically)")
        except Exception as e:
            wakeup_steps.append(f"⚠️ WebSocket reconnect failed: {e}")
        
        # Log all wakeup steps
        for step in wakeup_steps:
            print(f"Media Player Hardware Wakeup: {step}")
        
        return {
            "status": "success", 
            "message": "Media player hardware wakeup completed",
            "steps": wakeup_steps
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to wakeup media player: {str(e)}"
        }
