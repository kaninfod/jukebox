import logging
from PIL import Image, ImageDraw, ImageFont
from app.ui.theme import UITheme
from app.ui.factory import screen_factory
from enum import Enum
from app.services.jukebox_mediaplayer import PlayerStatus
#from app.core.event_bus import event_bus, Event
from app.core import event_bus, EventType
logger = logging.getLogger(__name__)

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
        event_bus.subscribe(EventType.SHOW_IDLE, self._show_idle_screen)
        event_bus.subscribe(EventType.SHOW_MESSAGE, self._show_message_screen)
        event_bus.subscribe(EventType.SHOW_HOME, self._handle_player_changes)
        event_bus.subscribe(EventType.TRACK_CHANGED, self._handle_player_changes)
        event_bus.subscribe(EventType.VOLUME_CHANGED, self._handle_player_changes)
        event_bus.subscribe(EventType.STATUS_CHANGED, self._handle_player_changes)
        #event_bus.subscribe(EventType.CLEAR_ERROR, )

        #event_bus.subscribe(self.handle_event)
        logger.info(f"ScreenManager subscribed to EventBus with {id(event_bus)}")

    def _handle_player_changes(self, event):
        if event.payload['status'] in [PlayerStatus.PLAY.value, PlayerStatus.PAUSE.value]:
            self._show_home_screen(event)
        else:
            self._show_idle_screen(event)

    def _handle_error_event(self, event):
        if event.type == 'clear_error':
            logger.info("Received clear_error event, clearing error state.")
            self.error_active = False
            self._show_idle_screen()

    # def handle_event(self, event: Event):
    #     if self.error_active and event.type != 'clear_error':
    #         logger.info(f"Error screen active, ignoring event: {event.type}")
    #         return
    #     if event.type == 'clear_error':
    #         logger.info("Received clear_error event, clearing error state.")
    #         self.error_active = False
    #         self._show_idle_screen()
    #         return
    #     if event.type in ['show_home', 'track_changed', 'volume_changed', 'status_changed']:
    #         if event.payload['status'] in [PlayerStatus.PLAY.value, PlayerStatus.PAUSE.value]:
    #             self._show_home_screen(event.payload)
    #         else:
    #             self._show_idle_screen(event.payload)
    #     elif event.type == 'show_idle':
    #         self._show_idle_screen()
    #     elif event.type == 'show_message_screen':
    #         self._show_message_screen(event.payload)
    #     else:
    #         logger.info(f"Event not handled here: {event.type}")

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
        if 'idle' in self.screens:
            self.current_screen = self.screens['idle']
        elif self.screens:
            self.current_screen = next(iter(self.screens.values()))

    def add_screen(self, name, screen):
        self.screens[name] = screen

    def _show_home_screen(self, event):
        self.switch_to_screen("home")
        if self.current_screen.is_dirty():
            self.render(context=event.payload)
        else:
            logger.debug("HomeScreen not dirty, skipping render.")

    def _show_idle_screen(self, event):
        self.switch_to_screen("idle")
        self.render(context=event.payload)

    def _show_message_screen(self, event):
        self.switch_to_screen("message_screen")
        self.render(context=event.payload)

    def switch_to_screen(self, screen_name):
        old_screen = self.current_screen.name if self.current_screen else "None"
        self.current_screen = self.screens[screen_name]
        logger.info(f"Switching to screen: {self.current_screen.name}")

    def render(self, context=None, force=True):
        if self.current_screen and (self.current_screen.dirty or force):
            from PIL import Image, ImageDraw
            image = Image.new('RGB', (self.display.device.width, self.display.device.height), 'black')
            draw = ImageDraw.Draw(image)
            try:
                self.current_screen.draw(draw, self.fonts, context=context, image=image)
                self.display.device.display(image)
                self.current_screen.dirty = False
                logger.info(f"🖥️  SCREEN CHANGED SUCCESSFULLY: {self.current_screen.name}")
            except Exception as e:
                logger.error(f"Failed to draw {self.current_screen.name}: {e}")
                
                from app.config import config
                file_name = config.get_icon_path("error")
                context = {
                    "title": f"Error.",
                    "icon_name": file_name,
                    "message": f"Error drawing {self.current_screen.name}: {e}",
                    "background": "#DA0F0F",
                }
                from app.ui.screens.message import MessageScreen
                MessageScreen.show(context)
            image.save(f"tests/display_{self.current_screen.name}.png")


    def cleanup(self):
        logger.info("ScreenManager cleanup called")