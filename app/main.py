import RPi.GPIO as GPIO
#GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

from fastapi import FastAPI
from app.routes.ytmusic import router as ytmusic_router
from app.routes.mediaplayer import router as mediaplayer_router
from app.routes.homeassistant import router as homeassistant_router, start_websocket_background, sync_with_ytube_music_player
from app.ui.screens import ScreenManager
from app.hardware import HardwareManager

# Initialize FastAPI app
app = FastAPI()

# Include routers
app.include_router(ytmusic_router)
app.include_router(mediaplayer_router)
app.include_router(homeassistant_router)

# Initialize screen manager (will be populated when hardware is initialized)
screen_manager = None
hardware_manager = None
display = None


def get_screen_manager():
    """Get the global screen manager instance"""
    return screen_manager


def get_hardware_manager():
    """Get the global hardware manager instance"""
    return hardware_manager


@app.on_event("startup")
def startup_event():
    """Initialize all systems on startup"""
    global screen_manager, hardware_manager, display
    
    # Initialize hardware manager
    hardware_manager = HardwareManager(screen_manager)
    
    # Initialize display first
    display = hardware_manager.initialize_hardware()
    
    # Initialize screen manager with display
    screen_manager = ScreenManager(display)
    
    # Update hardware manager with screen manager
    hardware_manager.screen_manager = screen_manager
    
    # Start WebSocket connection to Home Assistant
    start_websocket_background()
    print("Started WebSocket connection to Home Assistant")
    
    # Sync with current YouTube Music player state
    try:
        sync_result = sync_with_ytube_music_player()
        print(f"Initial sync with YouTube Music player: {sync_result.get('status', 'unknown')}")
    except Exception as e:
        print(f"Failed to sync with YouTube Music player on startup: {e}")
    
    # Render the initial screen
    screen_manager.render()


@app.on_event("shutdown")
def shutdown_event():
    """Clean up resources on shutdown"""
    # Stop WebSocket connection
    try:
        from app.routes.homeassistant import stop_websocket
        stop_websocket()
        print("Stopped WebSocket connection to Home Assistant")
    except Exception as e:
        print(f"Error stopping WebSocket: {e}")
    
    # Clean up hardware
    if hardware_manager:
        hardware_manager.cleanup()


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}
