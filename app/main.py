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
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.config import config
from app.core.security import APIKeyMiddleware
from app.core.security_headers import SecurityHeadersMiddleware


from app.routes.albums import router as album_router
from app.routes.mediaplayer import router as mediaplayer_router
from app.routes.system import router as system_router
from app.routes.subsonic import router as subsonic_router
from app.routes.chromecast import router as chromecast_router
from app.routes.output import router as output_router
from app.routes.nfc_encoding import router as nfc_encoding_router
from app.routes.display import router as display_router

# Import services to ensure event subscriptions are active
from app.services import system_service  # Ensures SystemService event handlers are registered
from app.web.routes import router as web_router

#from app.services.playback_service import PlaybackManager

#from app.ui import ScreenManager
#from app.hardware import HardwareManager

import logging, os
from app.core.logging_config import setup_logging

setup_logging(level=logging.DEBUG)

# Initialize FastAPI app

# Enable interactive API docs when DEBUG_MODE=true or ENABLE_DOCS=true
enable_docs = getattr(config, "ENABLE_DOCS", False) or config.DEBUG_MODE
app = FastAPI(
    docs_url=(config.DOCS_URL if enable_docs else None),
    redoc_url=None,
    openapi_url=(config.OPENAPI_URL if enable_docs else None),
)

# Trusted hosts (Host header) to reduce host header attacks
allowed_hosts = [h.strip() for h in config.ALLOWED_HOSTS.split(",") if h.strip()]
if allowed_hosts and allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Optional HTTP -> HTTPS redirect
if config.ENABLE_HTTPS_REDIRECT:
    app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS middleware
cors_origins = [o.strip() for o in config.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security: API key protection for /api/*
app.add_middleware(APIKeyMiddleware)

# Add common security headers
app.add_middleware(SecurityHeadersMiddleware)

# Mount static directories for web access
album_cover_dir = config.STATIC_FILE_PATH
if not os.path.isabs(album_cover_dir):
    album_cover_dir = os.path.join(os.path.dirname(__file__), "..", album_cover_dir)
app.mount("/album_covers", StaticFiles(directory=album_cover_dir), name="album_covers")
app.mount("/assets", StaticFiles(directory=album_cover_dir), name="assets")


# Include routers
app.include_router(album_router)
app.include_router(mediaplayer_router)
app.include_router(display_router)
app.include_router(system_router)
app.include_router(subsonic_router)
app.include_router(chromecast_router)
app.include_router(output_router)
app.include_router(nfc_encoding_router)
app.include_router(web_router)

# Mount web static files (JS, CSS) - serve from app/web/static with proper MIME types
# MUST be mounted AFTER routers to avoid route conflicts
web_static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
if os.path.isdir(web_static_dir):
    app.mount("/static", StaticFiles(directory=web_static_dir), name="web_static")
else:
    logger.warning(f"Web static directory not found: {web_static_dir}")

# Service container import and eager initialization
# from app.core.service_container import setup_service_container, container as global_container
# if global_container is None:
#     global_container = setup_service_container()



@app.on_event("startup")
def startup_event():
    """Initialize all systems using the service container"""
    # Step 0: Validate configuration
    if not config.validate_config():
        logging.error("❌ Configuration validation failed. Please check your .env file.")
        return
    # Step 1: Setup service container
    from app.core.service_container import setup_service_container
    global_container = setup_service_container()
    # Step 2: Resolve all main services (hardware_manager auto-initializes in factory)
    playback_service = global_container.get('playback_service')
    #screen_manager = global_container.get('screen_manager')
    hardware_manager = global_container.get('hardware_manager')
    subsonic_service = global_container.get('subsonic_service')
    # Step 3: Update hardware manager with references (cross-dependencies)
    #hardware_manager.screen_manager = screen_manager
    hardware_manager.playback_service = playback_service
    # Step 4: Initialize DynamicLoader for menu system
    #from app.ui.menu.dynamic_loader import initialize_dynamic_loader
    #initialize_dynamic_loader(subsonic_service)
    #logging.info("✅ DynamicLoader initialized for menu system")
    # Step 5: Start the system
    #from app.ui.screens import IdleScreen
    #IdleScreen.show()

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
            pass
            #screen_manager = global_container.get('screen_manager')
            #if screen_manager:
            #    screen_manager.cleanup()
        except Exception:
            pass
    logging.info("Jukebox FastAPI app shutdown complete")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}
