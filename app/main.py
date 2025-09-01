import RPi.GPIO as GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import config

from app.routes.albums import router as album_router
from app.routes.mediaplayer import router as mediaplayer_router
from app.routes.pngs import router as pngs_router
from app.routes.system import router as system_router
from app.web.routes import router as web_router

from app.services.websocket_service import websocket_service
from app.services.playback_manager import PlaybackManager

from app.ui import ScreenManager
from app.hardware import HardwareManager

import logging, os
from app.core.logging_config import setup_logging

setup_logging(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI()

# Mount static folders
app.mount("/pngs-static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "tests")), name="pngs-static")

# Mount album cover cache directory for web access
album_cover_dir = config.STATIC_FILE_PATH
if not os.path.isabs(album_cover_dir):
    album_cover_dir = os.path.join(os.path.dirname(__file__), "..", album_cover_dir)
app.mount("/album_covers", StaticFiles(directory=album_cover_dir), name="album_covers")

# Include routers
app.include_router(album_router)
app.include_router(mediaplayer_router)
app.include_router(system_router)
app.include_router(pngs_router, prefix="/pngs")
app.include_router(web_router)


# Global instances for shared access
screen_manager = None
hardware_manager = None
display = None
playback_manager = None

jukebox_mediaplayer = None

def get_jukebox_mediaplayer():
    """Get the global JukeboxMediaPlayer instance"""
    return jukebox_mediaplayer

def get_screen_manager():
    """Get the global screen manager instance"""
    return screen_manager


def get_hardware_manager():
    """Get the global hardware manager instance"""
    return hardware_manager


@app.on_event("startup")
def startup_event():
    """Initialize all systems on startup"""
    global screen_manager, hardware_manager, display, playback_manager, jukebox_mediaplayer
    
    # Step 0: Validate configuration
    if not config.validate_config():
        logging.error("❌ Configuration validation failed. Please check your .env file.")
        return
    
    # Step 2: Initialize hardware manager
    hardware_manager = HardwareManager()

    # Step 3: Initialize display hardware
    display = hardware_manager.initialize_hardware()

    # Step 4: Initialize screen manager with display
    screen_manager = ScreenManager(display)

    # Step 5: Initialize global PlaybackManager and JukeboxMediaPlayer
    from app.services.jukebox_mediaplayer import JukeboxMediaPlayer
    if not jukebox_mediaplayer:
        jukebox_mediaplayer = JukeboxMediaPlayer([])
    playback_manager = PlaybackManager(screen_manager=screen_manager, player=jukebox_mediaplayer)

    # Step 6: Update hardware manager with screen manager and playback manager
    hardware_manager.screen_manager = screen_manager
    hardware_manager.playback_manager = playback_manager

    # Start WebSocket connection to Home Assistant
    websocket_service.start()
    logging.info("Started WebSocket connection to Home Assistant")
    
    from app.ui.screens import IdleScreen
    IdleScreen.show()
    logging.info("🚀Jukebox app startup complete")


@app.on_event("shutdown")
def shutdown_event():
    """Clean up resources on shutdown"""
    # Stop WebSocket connection
    try:
        websocket_service.stop()
        logging.info("Stopped WebSocket connection to Home Assistant")
    except Exception as e:
        logging.error(f"Error stopping WebSocket: {e}")
    # Clean up hardware
    if hardware_manager:
        hardware_manager.cleanup()
    if screen_manager:
        screen_manager.cleanup()
    logging.info("Jukebox FastAPI app shutdown complete")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}
