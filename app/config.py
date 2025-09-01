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
    # YouTube Music API Credentials
    YTMUSIC_CLIENT_ID: str = os.getenv("YTMUSIC_CLIENT_ID", "194320065459-49q3ijtt8auu3oafbqu0bo9ajr9er40b.apps.googleusercontent.com")
    YTMUSIC_CLIENT_SECRET: str = os.getenv("YTMUSIC_CLIENT_SECRET", "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")
    # Font configuration: name, path, size
    FONT_DEFINITIONS = [
        {"name": "title", "path": "/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", "size": 20},
        {"name": "info", "path": "/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", "size": 18},
        {"name": "small", "path": "/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", "size": 12},
        {"name": "symbols", "path": "/home/pi/shared/jukebox/fonts/symbolfont/symbolfont.ttf", "size": 24},
        {"name": "oswald_semi_bold", "path": "/home/pi/shared/jukebox/fonts/Oswald-SemiBold.ttf", "size": 24}
    ]
    """Central configuration class for the jukebox application"""
    
    # Home Assistant Configuration
    HA_BASE_URL: str = os.getenv("HA_BASE_URL", "http://192.168.68.100:8123")
    HA_WS_URL: str = os.getenv("HA_WS_URL", "ws://192.168.68.100:8123/api/websocket")
    HA_TOKEN: str = os.getenv("HA_TOKEN", "")
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "192.168.68.102")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USERNAME: str = os.getenv("DB_USERNAME", "dbuser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "hingedb")

    STATIC_FILE_PATH: str = os.getenv("STATIC_FILE_PATH", "static_files")

    # YouTube Music OAuth
    YOUTUBE_ACCESS_TOKEN: str = os.getenv("YOUTUBE_ACCESS_TOKEN", "")
    YOUTUBE_REFRESH_TOKEN: str = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
    YOUTUBE_SCOPE: str = os.getenv("YOUTUBE_SCOPE", "https://www.googleapis.com/auth/youtube")
    
    # GPIO Pin Configuration
    DISPLAY_POWER_GPIO: int = int(os.getenv("DISPLAY_POWER_GPIO", "20"))
    DISPLAY_BACKLIGHT_GPIO: int = int(os.getenv("DISPLAY_BACKLIGHT_GPIO", "18"))
    ROTARY_ENCODER_PIN_A: int = int(os.getenv("ROTARY_ENCODER_PIN_A", "6"))
    ROTARY_ENCODER_PIN_B: int = int(os.getenv("ROTARY_ENCODER_PIN_B", "5"))
    RFID_CS_PIN: int = int(os.getenv("RFID_CS_PIN", "7"))
    NFC_CARD_SWITCH_GPIO: int = int(os.getenv("NFC_CARD_SWITCH_GPIO", "26"))
    #BUTTON_0_GPIO: int = int(os.getenv("BUTTON_0_GPIO", "26"))
    BUTTON_1_GPIO: int = int(os.getenv("BUTTON_1_GPIO", "14"))
    BUTTON_2_GPIO: int = int(os.getenv("BUTTON_2_GPIO", "15"))
    BUTTON_3_GPIO: int = int(os.getenv("BUTTON_3_GPIO", "12"))
    BUTTON_4_GPIO: int = int(os.getenv("BUTTON_4_GPIO", "19"))
    BUTTON_5_GPIO: int = int(os.getenv("BUTTON_5_GPIO", "17"))
    
    # Hardware Settings
    RFID_POLL_INTERVAL: float = float(os.getenv("RFID_POLL_INTERVAL", "1.0"))
    RFID_READ_TIMEOUT: float = float(os.getenv("RFID_READ_TIMEOUT", "5.0"))
    ENCODER_BOUNCETIME: int = int(os.getenv("ENCODER_BOUNCETIME", "2"))
    BUTTON_BOUNCETIME: int = int(os.getenv("BUTTON_BOUNCETIME", "200"))
    
    # Media Player Configuration
    MEDIA_PLAYER_ENTITY_ID: str = os.getenv("MEDIA_PLAYER_ENTITY_ID", "media_player.living_room")
    
    # Application Settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
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
        """Generate the database connection URL from environment variables"""
        return f"mysql+pymysql://{cls.DB_USERNAME}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            "HA_TOKEN",
            "DB_PASSWORD"
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
