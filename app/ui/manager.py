import logging
import os
logger = logging.getLogger(__name__)
from app.ui.screens.idle import IdleScreen
from app.ui.screens.home import HomeScreen
from app.ui.screens.rfid_loading import RfidReadingScreen, RfidLoadingScreen, RfidNewRfidScreen, RfidErrorScreen
from app.ui.screens.error import ErrorScreen
from PIL import Image, ImageDraw, ImageFont
from app.ui.theme import UITheme
from app.ui.context import UIContext
from app.ui.factory import screen_factory
from enum import Enum
from app.services.jukebox_mediaplayer import PlayerStatus
from app.ui.event_bus import ui_event_bus, UIEvent

class RfidLoadingStatus(Enum):
    READING = "reading"
    LOADING_ALBUM = "loading_album"
    NEW_RFID = "new_rfid"
    ERROR = "error"


class ScreenManager:
    """Manages different screens and screen switching"""
    def __init__(self, display):
        self.display = display
        self.screens = {}
        self.current_screen = None
        self.fonts = self._load_fonts()
        self.theme = UITheme(self.fonts)
        self.error_active = False  # Block screen changes while error is active
        logger.info("ScreenManager initialized")
        self._init_screens()
        ui_event_bus.subscribe(self.handle_event)

    def handle_event(self, event: UIEvent):
        # All screen changes should be triggered via events and handled here.
        # If error is active, only allow clear_error event
        if self.error_active and event.type != 'clear_error':
            logger.info(f"Error screen active, ignoring event: {event.type}")
            return
        if event.type == 'clear_error':
            logger.info("Received clear_error event, clearing error state.")
            self.error_active = False
            # After clearing error, show idle screen (or last requested screen)
            self._show_idle_screen()
            return
        if event.type in ['show_home', 'track_changed', 'volume_changed', 'status_changed']:
            if event.payload['status'] in [PlayerStatus.PLAY.value, PlayerStatus.PAUSE.value]:
                self._show_home_screen(event.payload)
            else:
                self._show_idle_screen(event.payload)
        elif event.type == 'show_idle':
            self._show_idle_screen()
        elif event.type == 'show_error':
            self.error_active = True
            self._show_error_screen(event.payload)
        elif event.type == 'show_rfid_reading':
            self._show_rfid_reading_screen(event.payload)
        elif event.type == 'show_rfid_loading':
            self._show_rfid_loading_screen(event.payload)
        elif event.type == 'show_rfid_new':
            self._show_rfid_new_screen(event.payload)
        elif event.type == 'show_rfid_error':
            self._show_rfid_error_screen(event.payload)
        else:
            logger.warning(f"Unhandled event type: {event.type}")
        # Add more event types as needed

    def cleanup(self):
        logger.info("ScreenManager cleanup called")
        # Add any additional cleanup logic here if needed
    
    @staticmethod
    def get_icon_png(icon_path):
        from PIL import Image
        if icon_path.startswith("http://") or icon_path.startswith("https://"):
            import requests
            from io import BytesIO
            r = requests.get(icon_path)
            icon_img = Image.open(BytesIO(r.content)).convert("RGBA")
        else:
            icon_img = Image.open(icon_path).convert("RGBA")
        return icon_img

    def _load_fonts(self):
        from app.config import config
        fonts = {}
        for font_def in config.FONT_DEFINITIONS:
            try:
                fonts[font_def["name"]] = ImageFont.truetype(font_def["path"], font_def["size"])
            except (OSError, ImportError) as e:
                logger.warning(f"Font loading failed for {font_def['name']}: {e}, using default font")
        return fonts

    def _init_screens(self):
        screen_dict = screen_factory(self.theme)
        for name, screen in screen_dict.items():
            self.add_screen(name, screen)
            logger.debug(f"Screen initialized: {name}")
        # Set the first screen as the current screen (default to 'idle' if present, else first key)
        if 'idle' in self.screens:
            self.current_screen = self.screens['idle']
        elif self.screens:
            self.current_screen = next(iter(self.screens.values()))

    def add_screen(self, name, screen):
        self.screens[name] = screen

    def _show_home_screen(self, context=None):
        self.switch_to_screen("home")
        logger.debug(f"Checking if screen should be rendered {self.current_screen}")
        if self.current_screen.is_dirty():
            self.render(context=context)
            logger.debug("HomeScreen rendered")
        else:
            logger.debug("HomeScreen not dirty, skipping render.")

    def _show_idle_screen(self, context=None):
        self.switch_to_screen("idle")
        self.render(context=context)

    def _show_rfid_reading_screen(self, context=None):
        self.switch_to_screen("rfid_reading")
        self.render(context=context)

    def _show_rfid_new_screen(self, context=None):
        self.switch_to_screen("rfid_new_rfid")
        self.render(context=context)

    def _show_rfid_loading_screen(self, context=None):
        self.switch_to_screen("rfid_loading")
        self.render(context=context)

    def _show_rfid_error_screen(self, context=None):
        self.switch_to_screen("rfid_error")
        self.render(context=context)

    def _show_error_screen(self, context=None):
        error_screen = self.screens.get("error")
        if error_screen:
            self.switch_to_screen("error")
            self.render(context)

    def switch_to_screen(self, screen_name):
        old_screen = self.current_screen.name if self.current_screen else "None"
        self.current_screen = self.screens[screen_name]
        logger.info(f"🖥️  SCREEN CHANGE: {old_screen} → {self.current_screen.name}")

    def render(self, context=None, force=True):
        if self.current_screen and (self.current_screen.dirty or force):
            from PIL import Image, ImageDraw
            image = Image.new('RGB', (self.display.device.width, self.display.device.height), 'black')
            draw = ImageDraw.Draw(image)
            try:
                self.current_screen.draw(draw, self.fonts, context=context, image=image)
                self.display.device.display(image)
                self.current_screen.dirty = False
            except Exception as e:
                logger.error(f"Failed to draw {self.current_screen.name}: {e}")
                from app.ui.screens.error import ErrorScreen
                ErrorScreen.show({"error_message": f"Error drawing {self.current_screen.name}: {e}"})
            image.save(f"tests/display_{self.current_screen.name}.png")