import RPi.GPIO as GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

from fastapi import FastAPI
from app.config import config
from app.routes.ytmusic import router as ytmusic_router
from app.routes.mediaplayer import router as mediaplayer_router
from app.routes.homeassistant import router as homeassistant_router, sync_with_ytube_music_player
from app.services.websocket_client import start_websocket_background, stop_websocket
from app.routes.system import router as system_router
from app.ui.screens import ScreenManager
from app.hardware import HardwareManager
import logging


# Initialize FastAPI app
app = FastAPI()

# Include routers
app.include_router(ytmusic_router)
app.include_router(mediaplayer_router)
app.include_router(homeassistant_router)
app.include_router(system_router)

# Initialize screen manager (will be populated when hardware is initialized)
screen_manager = None
hardware_manager = None
display = None

logging.basicConfig(
    level=logging.DEBUG,  # or DEBUG for more verbosity
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
        logging.StreamHandler(),                # Console
        logging.FileHandler("jukebox.log")      # File
    ]
)
# Suppress noisy logs from third-party libraries
for lib in ["requests", "PIL", "urllib3", "websockets"]:
    logging.getLogger(lib).setLevel(logging.WARNING)


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
    
    # Step 0: Validate configuration
    if not config.validate_config():
        logging.error("❌ Configuration validation failed. Please check your .env file.")
        return
    
    # Step 1: Ensure display is powered on BEFORE any hardware initialization
    try:
        logging.info("🔋 Powering on display before hardware initialization...")
        # Set GPIO as output LOW to turn ON display (S8550 transistor)
        GPIO.setup(config.DISPLAY_POWER_GPIO, GPIO.OUT)
        GPIO.output(config.DISPLAY_POWER_GPIO, GPIO.LOW)
        logging.info("✅ Display powered on at startup (before hardware init)")
    except Exception as e:
        logging.warning(f"⚠️ Error controlling display power at startup: {e}")
    
    # Step 2: Initialize hardware manager
    hardware_manager = HardwareManager(screen_manager)
    
    # Step 3: Initialize display hardware
    display = hardware_manager.initialize_hardware()
    
    # Step 4: Initialize screen manager with display
    screen_manager = ScreenManager(display)
    
    # Step 5: Update hardware manager with screen manager
    hardware_manager.screen_manager = screen_manager
    
    # Start WebSocket connection to Home Assistant
    start_websocket_background()
    logging.info("Started WebSocket connection to Home Assistant")
    
    # Sync with current YouTube Music player state
    # try:
    #     sync_result = sync_with_ytube_music_player()
    #     logging.info(f"Initial sync with YouTube Music player: {sync_result.get('status', 'unknown')}")
    # except Exception as e:
    #     logging.error(f"Failed to sync with YouTube Music player on startup: {e}")
            # Always sync with YouTube Music player before deciding which screen to show
    try:
        context = sync_with_ytube_music_player()
    except Exception as e:
        logging.error(f"Error syncing with YouTube Music player before screen selection: {e}")
        
        
    # Show appropriate screen based on current state (idle if no music)
    logging.info(f"🚀 STARTUP: Calling show_appropriate_screen with context: {context}")
    screen_manager.show_appropriate_screen(context)
    #screen_manager.render()


@app.on_event("shutdown")
def shutdown_event():
    """Clean up resources on shutdown"""
    # Stop WebSocket connection
    try:
        from app.routes.homeassistant import stop_websocket
        stop_websocket()
        logging.info("Stopped WebSocket connection to Home Assistant")
    except Exception as e:
        logging.error(f"Error stopping WebSocket: {e}")
    
    # Clean up hardware
    if hardware_manager:
        hardware_manager.cleanup()


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}
