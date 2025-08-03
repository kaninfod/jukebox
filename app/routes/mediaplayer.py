from fastapi import APIRouter, Body
from app.ui.screens import PlayerStatus
from app.devices.mqtt import (
    publish_artist, publish_album, publish_year, 
    publish_track, publish_status, publish_volume, 
    get_all_mediaplayer_info, publish_yt_id
)

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
        
        # Publish to MQTT for audio system integration
        try:
            publish_volume(volume)
        except Exception as e:
            print(f"Failed to publish volume to MQTT: {e}")
    
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
