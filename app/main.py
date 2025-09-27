# Conditional GPIO import for hardware mode
try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BCM)
    _gpio_available = True
except ImportError:
    _gpio_available = False
    import logging
    logging.getLogger(__name__).warning("⚠️  RPi.GPIO not available - hardware features disabled")

import getpass
from venv import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import config

from app.routes.albums import router as album_router
from app.routes.mediaplayer import router as mediaplayer_router
#from app.routes.pngs import router as pngs_router
from app.routes.system import router as system_router
from app.routes.subsonic import router as subsonic_router
from app.routes.chromecast import router as chromecast_router

from app.services.playback_manager import PlaybackManager

from app.ui import ScreenManager
from app.hardware import HardwareManager

import logging, os
from app.core.logging_config import setup_logging

setup_logging(level=logging.DEBUG)

# Initialize FastAPI app

app = FastAPI()

# Add CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (including all local network clients)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders
# app.mount("/pngs-static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "tests")), name="pngs-static")

# Mount album cover cache directory for web access
album_cover_dir = config.STATIC_FILE_PATH
if not os.path.isabs(album_cover_dir):
    album_cover_dir = os.path.join(os.path.dirname(__file__), "..", album_cover_dir)
app.mount("/album_covers", StaticFiles(directory=album_cover_dir), name="album_covers")

# Include routers
app.include_router(album_router)
app.include_router(mediaplayer_router)
app.include_router(system_router)
# app.include_router(pngs_router, prefix="/pngs")
app.include_router(subsonic_router)
app.include_router(chromecast_router)





# Service container import and eager initialization
from app.core.service_container import setup_service_container, container as global_container
if global_container is None:
    global_container = setup_service_container()



@app.on_event("startup")
def startup_event():
    """Initialize all systems using the service container"""
    # Step 0: Validate configuration
    if not config.validate_config():
        logging.error("❌ Configuration validation failed. Please check your .env file.")
        return
    # Step 1: Setup service container
    global_container = setup_service_container()
    # Step 2: Resolve all main services
    playback_manager = global_container.get('playback_manager')
    screen_manager = global_container.get('screen_manager')
    hardware_manager = global_container.get('hardware_manager')
    # Step 3: Update hardware manager with references (cross-dependencies)
    hardware_manager.screen_manager = screen_manager
    hardware_manager.playback_manager = playback_manager
    # Step 4: Start the system
    from app.ui.screens import IdleScreen
    IdleScreen.show()

    import getpass, os
    logger.info(f"Running as user: {getpass.getuser()}")
    logger.info(f"PATH: {os.environ.get('PATH')}")
    logging.info("🚀Jukebox app startup complete")



@app.on_event("shutdown")
def shutdown_event():
    """Clean up resources on shutdown"""
    from app.core.service_container import container as global_container
    if global_container:
        try:
            hardware_manager = global_container.get('hardware_manager')
            if hardware_manager:
                hardware_manager.cleanup()
        except Exception:
            pass
        try:
            screen_manager = global_container.get('screen_manager')
            if screen_manager:
                screen_manager.cleanup()
        except Exception:
            pass
    logging.info("Jukebox FastAPI app shutdown complete")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}
