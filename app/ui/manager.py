import logging
logger = logging.getLogger(__name__)
from app.ui.screens.idle import IdleScreen
from app.ui.screens.home import HomeScreen
from app.ui.screens.rfid_loading import RfidReadingScreen, RfidLoadingScreen, RfidNewRfidScreen, RfidErrorScreen
from app.ui.screens.error import ErrorScreen
from PIL import Image, ImageDraw, ImageFont
from app.ui.theme import UITheme
from app.ui.context import UIContext
from app.routes.homeassistant import sync_with_ytube_music_player
#from app.ui.factory import screen_factory
from enum import Enum
from app.services.jukebox_mediaplayer import PlayerStatus

# class PlayerStatus(Enum):
#     PLAY = "play"
#     PAUSE = "pause"
#     STOP = "stop"
#     STANDBY = "standby"
#     OFF = "off"

class RfidLoadingStatus(Enum):
    READING = "reading"
    LOADING_ALBUM = "loading_album"
    NEW_RFID = "new_rfid"
    ERROR = "error"


def screen_factory(theme):
    return {
        "idle": IdleScreen(theme),
        "home": HomeScreen(theme),
        "rfid_reading": RfidReadingScreen(theme),
        "rfid_loading": RfidLoadingScreen(theme),
        "rfid_new_rfid": RfidNewRfidScreen(theme),
        "rfid_error": RfidErrorScreen(theme),
        "error": ErrorScreen(theme),
    }

class ScreenManager:
    """Manages different screens and screen switching"""
    def __init__(self, display):
        self.display = display
        self.screens = {}
        self.current_screen = None
        self.current_screen_index = 0
        self.screen_order = []
        self.fonts = self._load_fonts()
        self.theme = UITheme(self.fonts)
        self._init_screens()
        self.last_player_status = None
        self.last_track_info = None
        self.last_rfid_id = None

    def register_player(self, player):
        """Register as a listener to the JukeboxMediaPlayer for event-driven updates."""
        self.jukebox_mediaplayer = player
        def on_player_event(event_type, data):
            if event_type in ['track_changed', 'volume_changed']:
                logger.info("ScreenManager: Track or volume changed event received; rendering home screen.")
                self.show_home_screen()
            elif event_type == 'status_changed':
                logger.info("ScreenManager: Status changed event received; rendering appropriate screen.")
                self.show_appropriate_screen()
        player.add_listener(on_player_event)
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
                #fonts[font_def["name"]] = ImageFont.load_default()
        return fonts

    def _init_screens(self):
        screen_dict = screen_factory(self.theme)
        for name, screen in screen_dict.items():
            self.add_screen(name, screen)
        if self.screen_order:
            self.current_screen = self.screens[self.screen_order[0]]

    def add_screen(self, name, screen):
        self.screens[name] = screen
        if name not in self.screen_order:
            self.screen_order.append(name)

    def update_player_status(self, new_status):
        if new_status != self.last_player_status:
            self.last_player_status = new_status
            logger.info(f"Player status changed to {new_status}; updating screen.")
            self.show_appropriate_screen()
        else:
            logger.debug("No change in player status; skipping update.")

    def update_track_info(self, new_track_info):
        if new_track_info != self.last_track_info:
            self.last_track_info = new_track_info
            logger.info("Track info changed; updating screen.")
            self.show_appropriate_screen()
        else:
            logger.debug("No change in track info; skipping update.")

    def update_rfid_id(self, new_rfid_id):
        if new_rfid_id != self.last_rfid_id:
            self.last_rfid_id = new_rfid_id
            logger.info(f"RFID ID changed to {new_rfid_id}; updating screen.")
        else:
            logger.debug("No change in RFID ID; skipping update.")

   
    def show_appropriate_screen(self):
        logger.debug("show_appropriate_screen called")
        # Use the player state directly, normalize to PlayerStatus        
        try:
            player_status = getattr(self.jukebox_mediaplayer, 'status', None)
            logger.debug(f"Current player status: {player_status}")
            #player_status = PlayerStatus(state)
        except (ValueError, TypeError):
            logger.warning(f"Invalid player status: {player_status}, defaulting to STOP")
            player_status = None
        if player_status in [PlayerStatus.PLAY, PlayerStatus.PAUSE]:
            logger.info("ScreenManager: Showing home screen - music is active")
            self.show_home_screen()
        elif player_status in [PlayerStatus.STOP, PlayerStatus.OFF]:
            logger.info("ScreenManager: Showing idle screen - music is inactive")
            self.show_idle_screen()

    def show_home_screen(self):
        """Show the home screen and render."""
        self.switch_to_screen("home")
        logger.debug("Checking if screen should be rendered")
        if self.current_screen.is_dirty():
            self.render(self.jukebox_mediaplayer)
            logger.debug("HomeScreen rendered")
        else:
            logger.debug("HomeScreen not dirty, skipping render.")

    def show_idle_screen(self):
        """Show the idle screen and render."""
        self.switch_to_screen("idle")
        self.render()

    def show_rfid_reading_screen(self, context=None):
        """Show the RFID reading screen."""
        self.switch_to_screen("rfid_reading")
        self.render(context=context)

    def show_rfid_new_screen(self, context=None):
        """Show the RFID new screen."""
        self.switch_to_screen("rfid_new_rfid")
        self.render(context=context)

    def show_rfid_loading_screen(self, context=None):
        """Show the RFID loading screen."""
        self.switch_to_screen("rfid_loading")
        self.render(context=context)

    def show_rfid_error_screen(self, context=None):
        """Show the RFID error screen."""
        self.switch_to_screen("rfid_error")
        self.render(context=context)

    def show_error_screen(self, context=None):
        error_screen = self.screens.get("error")
        if error_screen:
            self.switch_to_screen("error")
            self.render(context)

    def switch_to_screen(self, screen_name):
        if self.current_screen == self.screens[screen_name] :
            logger.debug(f"Screen already {screen_name}; skipping switch.")
            return
        old_screen = self.current_screen.name if self.current_screen else "None"
        self.current_screen = self.screens[screen_name]
        self.current_screen_index = self.screen_order.index(screen_name)
        logger.info(f"🖥️  SCREEN CHANGE: {old_screen} → {self.current_screen.name}")

    def render(self, context=None, force=False):
        if self.current_screen and (self.current_screen.dirty or force):
            from PIL import Image, ImageDraw
            image = Image.new('RGB', (self.display.device.width, self.display.device.height), 'black')
            draw = ImageDraw.Draw(image)
            self.current_screen.draw(draw, self.fonts, context=context, image=image)
            try:
                self.display.device.display(image)
                logger.info("Image sent to display successfully.")
            except Exception as e:
                logger.error(f"Failed to display image: {e}")
            self.current_screen.dirty = False

