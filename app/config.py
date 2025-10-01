import logging
logger = logging.getLogger(__name__)

"""
Configuration management for the jukebox application.
Loads environment variables and provides centralized access to configuration settings.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    # === NETWORK CONFIGURATION ===
    # Subsonic/Navidrome Configuration
    SUBSONIC_URL: str = os.getenv("SUBSONIC_URL", "http://localhost:4747")
    SUBSONIC_USER: str = os.getenv("SUBSONIC_USER", "")  # Required from .env
    SUBSONIC_PASS: str = os.getenv("SUBSONIC_PASS", "")  # Required from .env
    SUBSONIC_CLIENT: str = os.getenv("SUBSONIC_CLIENT", "jukebox")
    SUBSONIC_API_VERSION: str = os.getenv("SUBSONIC_API_VERSION", "1.15.0")
    
    # === TIMEOUT CONFIGURATION ===
    # Chromecast Operation Timeouts (seconds)
    CHROMECAST_CONNECT_TIMEOUT: int = int(os.getenv("CHROMECAST_CONNECT_TIMEOUT", "10"))     # Time to wait for device connection
    CHROMECAST_DISCOVERY_TIMEOUT: int = int(os.getenv("CHROMECAST_DISCOVERY_TIMEOUT", "3"))  # Time to discover devices on network
    CHROMECAST_WAIT_TIMEOUT: int = int(os.getenv("CHROMECAST_WAIT_TIMEOUT", "10"))           # Time to wait for device to be ready
    
    # User Interface Timeouts (seconds)  
    MENU_AUTO_EXIT_TIMEOUT: int = int(os.getenv("MENU_AUTO_EXIT_TIMEOUT", "10"))             # Auto-exit menu after inactivity
    
    # Network Request Timeouts (seconds)
    HTTP_REQUEST_TIMEOUT: int = int(os.getenv("HTTP_REQUEST_TIMEOUT", "10"))                 # HTTP requests (album covers, API calls)
    SYSTEM_OPERATION_TIMEOUT: int = int(os.getenv("SYSTEM_OPERATION_TIMEOUT", "5"))          # System operations (restart, shutdown)
    
    # RFID Hardware Timeouts
    RFID_POLL_INTERVAL: float = float(os.getenv("RFID_POLL_INTERVAL", "1.0"))              # Seconds between RFID reads
    RFID_READ_TIMEOUT: float = float(os.getenv("RFID_READ_TIMEOUT", "5.0"))                # Timeout for RFID card read
    RFID_THREAD_JOIN_TIMEOUT: int = int(os.getenv("RFID_THREAD_JOIN_TIMEOUT", "1"))        # Time to wait for RFID thread cleanup
    
    # === DEVICE CONFIGURATION ===
    # Hardware Mode - Set to false for headless/development mode without physical hardware
    HARDWARE_MODE: bool = os.getenv("HARDWARE_MODE", "true").lower() == "true"
    
    # Default Chromecast Device
    DEFAULT_CHROMECAST_DEVICE: str = os.getenv("DEFAULT_CHROMECAST_DEVICE", "Living Room")
    
    # Display Configuration  
    DISPLAY_WIDTH: int = int(os.getenv("DISPLAY_WIDTH", "480"))
    DISPLAY_HEIGHT: int = int(os.getenv("DISPLAY_HEIGHT", "320"))
    DISPLAY_ROTATION: int = int(os.getenv("DISPLAY_ROTATION", "0"))
    
    # === FONT CONFIGURATION ===
    # Font base directory (relative to project root)
    FONT_BASE_PATH: str = os.getenv("FONT_BASE_PATH", "fonts")
    
    @classmethod
    def get_font_definitions(cls):
        """Get font definitions with relative paths from font base directory"""
        import os
        base_path = cls.FONT_BASE_PATH
        return [
            {"name": "title", "path": os.path.join(base_path, "opensans", "OpenSans-Regular.ttf"), "size": 20},
            {"name": "info", "path": os.path.join(base_path, "opensans", "OpenSans-Regular.ttf"), "size": 18},
            {"name": "small", "path": os.path.join(base_path, "opensans", "OpenSans-Regular.ttf"), "size": 12},
            {"name": "symbols", "path": os.path.join(base_path, "symbolfont", "symbolfont.ttf"), "size": 24},
            {"name": "oswald_semi_bold", "path": os.path.join(base_path, "Oswald-SemiBold.ttf"), "size": 24}
        ]
    
    # Legacy FONT_DEFINITIONS for backward compatibility - will be deprecated
    @property
    def FONT_DEFINITIONS(self):
        return self.get_font_definitions()
    
    # === DATABASE CONFIGURATION ===
    # SQLite database - no additional config needed, uses app/database/album.db

    # === LOGGING CONFIGURATION ===
    LOG_SERVER_HOST: str = os.getenv("LOG_SERVER_HOST", "localhost")
    LOG_SERVER_PORT: int = int(os.getenv("LOG_SERVER_PORT", "514"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"

    # === GPIO CONFIGURATION ===
    # Display pins
    DISPLAY_POWER_GPIO: int = int(os.getenv("DISPLAY_POWER_GPIO", "20"))
    DISPLAY_BACKLIGHT_GPIO: int = int(os.getenv("DISPLAY_BACKLIGHT_GPIO", "18"))

    # ILI9488 SPI GPIOs (configurable)
    DISPLAY_GPIO_CS: int = int(os.getenv("DISPLAY_GPIO_CS", "8"))
    DISPLAY_GPIO_DC: int = int(os.getenv("DISPLAY_GPIO_DC", "6"))
    DISPLAY_GPIO_RST: int = int(os.getenv("DISPLAY_GPIO_RST", "5"))
    
    # Rotary encoder pins
    ROTARY_ENCODER_PIN_A: int = int(os.getenv("ROTARY_ENCODER_PIN_A", "27"))
    ROTARY_ENCODER_PIN_B: int = int(os.getenv("ROTARY_ENCODER_PIN_B", "22"))
    
    # RFID reader pins
    RFID_CS_PIN: int = int(os.getenv("RFID_CS_PIN", "7"))
    NFC_CARD_SWITCH_GPIO: int = int(os.getenv("NFC_CARD_SWITCH_GPIO", "4"))
    
    # Button pins
    BUTTON_1_GPIO: int = int(os.getenv("BUTTON_1_GPIO", "14"))
    BUTTON_2_GPIO: int = int(os.getenv("BUTTON_2_GPIO", "15"))
    BUTTON_3_GPIO: int = int(os.getenv("BUTTON_3_GPIO", "12"))
    BUTTON_4_GPIO: int = int(os.getenv("BUTTON_4_GPIO", "19"))
    BUTTON_5_GPIO: int = int(os.getenv("BUTTON_5_GPIO", "17"))

    # === HARDWARE SETTINGS ===
    # Input debounce times (milliseconds)
    # KY-040 rotary encoder: Optimized for detent-based counting
    ENCODER_BOUNCETIME: int = int(os.getenv("ENCODER_BOUNCETIME", "10"))
    BUTTON_BOUNCETIME: int = int(os.getenv("BUTTON_BOUNCETIME", "200"))

    # === MEDIA PLAYER CONFIGURATION ===
    # TODO: Remove hardcoded "living_room" - make configurable
    MEDIA_PLAYER_ENTITY_ID: str = os.getenv("MEDIA_PLAYER_ENTITY_ID", "media_player.living_room")

    # === PATH CONFIGURATION ===
    STATIC_FILE_PATH: str = os.getenv("STATIC_FILE_PATH", "static_files")
    
    # Icon definitions for use throughout the app
    ICON_DEFINITIONS = [
        {"name": "contactless", "path": "contactless.png", "width": 80, "height": 80},
        {"name": "library_music", "path": "library_music.png", "width": 80, "height": 80},
        {"name": "add_circle", "path": "add_circle.png", "width": 80, "height": 80},
        {"name": "error", "path": "error.png", "width": 80, "height": 80},
        {"name": "play_circle", "path": "play_circle.png", "width": 80, "height": 80},
        {"name": "pause_circle", "path": "pause_circle.png", "width": 80, "height": 80},
        {"name": "stop_circle", "path": "stop_circle.png", "width": 80, "height": 80},
        {"name": "standby_settings", "path": "power_settings.png", "width": 80, "height": 80},
        {"name": "klangmeister", "path": "klangmeister.png", "width": 480, "height": 320},
    ]


    @classmethod
    def get_image_path(cls, file_name: str) -> str:
        local_path = os.path.join(cls.STATIC_FILE_PATH, file_name)
        return local_path

    @classmethod
    def get_icon_path(cls, icon_name: str) -> str:
        icon_def = next((icon for icon in cls.ICON_DEFINITIONS if icon["name"] == icon_name), None)
        if icon_def:
            return cls.get_image_path(icon_def["path"])
        return False

    @classmethod
    def get_database_url(cls) -> str:
        """Generate the database connection URL - using SQLite"""
        import os
        # Get the absolute path to the database file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "app", "database", "album.db")
        return f"sqlite:///{db_path}"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            "SUBSONIC_USER", 
            "SUBSONIC_PASS"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        logger.info("✅ All required configuration variables are present")
        return True

# Create a global config instance
config = Config()
