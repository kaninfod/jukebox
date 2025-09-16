import logging
from PIL import Image, ImageDraw, ImageFont
from app.ui.theme import UITheme
from app.ui.factory import screen_factory
from enum import Enum
from app.services.jukebox_mediaplayer import PlayerStatus
from app.core import EventType
from app.ui.screen_queue import ScreenQueue
from app.metrics.decorators import track_event_handler
logger = logging.getLogger(__name__)

class ScreenManager:

    """Manages different screens and screen switching"""
    def __init__(self, display, event_bus, media_player=None):
        """
        Initialize ScreenManager with dependency injection.
        
        Args:
            display: Display device instance for rendering
            event_bus: EventBus instance for event communication
        """
        self.display = display
        self.event_bus = event_bus
        self.media_player = media_player
        # Initialize UI components
        self.screens = {}
        self.current_screen = None
        self.fonts = self._load_fonts()
        self.theme = UITheme(self.fonts)
        self.error_active = False  # Block screen changes while error is active
        self.screen_queue = ScreenQueue(self)
        # Initialize menu controller
        self.menu_controller = None
        
        logger.info("ScreenManager initialized with dependency injection")
        self._init_screens()
        self._init_menu_controller()
        
        # Setup event subscriptions using injected event_bus
        self._setup_event_subscriptions()
        logger.info(f"ScreenManager subscribed to EventBus with {id(self.event_bus)}")
        
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

    def _init_menu_controller(self):
        """Initialize the menu controller"""
        from app.ui.menu.menu_controller import MenuController
        self.menu_controller = MenuController()
        logger.info("MenuController initialized")

    def add_screen(self, name, screen):
        self.screens[name] = screen

    def _setup_event_subscriptions(self):
        """Setup all event subscriptions using injected event_bus"""
        self.event_bus.subscribe(EventType.SHOW_IDLE, lambda event: self.show_idle_screen(event.payload))
        self.event_bus.subscribe(EventType.SHOW_MESSAGE, lambda event: self.show_message_screen(event.payload))
        self.event_bus.subscribe(EventType.SHOW_HOME, lambda event: self.show_home_screen(event.payload))
        self.event_bus.subscribe(EventType.SHOW_MENU, lambda event: self.show_menu_screen(event.payload))
        self.event_bus.subscribe(EventType.TRACK_CHANGED, self._handle_player_changes)
        self.event_bus.subscribe(EventType.VOLUME_CHANGED, self._handle_player_changes)
        self.event_bus.subscribe(EventType.STATUS_CHANGED, self._handle_player_changes)
        self.event_bus.subscribe(EventType.SHOW_SCREEN_QUEUED, self._handle_queued_screen)

    def is_music_playing(self):
        if not self.media_player:
            return False
        from app.services.jukebox_mediaplayer import PlayerStatus
        return getattr(self.media_player, "status", None) == PlayerStatus.PLAY

    @track_event_handler("SHOW_SCREEN_QUEUED")
    def _handle_queued_screen(self, event):
        """Handle queued screen events (add to queue)"""
        payload = event.payload
        screen_type = payload.get('screen_type', 'message')
        context = payload.get('context', {})
        duration = payload.get('duration', 3.0)
        self.screen_queue.add_screen(screen_type, context, duration)

    @track_event_handler("PLAYER_CHANGE")
    def _handle_player_changes(self, event):
        status = event.payload.get('status')
        if status in [PlayerStatus.PLAY.value, PlayerStatus.PAUSE.value]:
            self.screen_queue.add_screen("home", event.payload, None)
            # self.show_home_screen(event.payload)
        else:
            self.screen_queue.add_screen("idle", event.payload, None)
            self.show_idle_screen(event.payload)

    def show_home_screen(self, context=None):
        self.switch_to_screen("home")
        self.render(context=context)

    def show_idle_screen(self, context=None):
        self.switch_to_screen("idle")
        self.render(context=context)

    def show_message_screen(self, context=None):
        if self.error_active:
            logger.info(f"Error screen active, ignoring message screen queue")
            return
        self.switch_to_screen("message_screen")
        self.render(context=context)

    def show_menu_screen(self, context=None):
        if self.error_active:
            logger.info(f"Error screen active, ignoring menu screen queue")
            return
        self.switch_to_screen("menu")
        self.render(context=context)

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
                self.current_screen.dirty = True
                logger.info(f"🖥️  SCREEN CHANGED SUCCESSFULLY: {self.current_screen.name}")
            except Exception as e:
                logger.error(f"Failed to draw {self.current_screen.name}: {e}")
                self.error_active = True
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
            # image.save(f"tests/display_{self.current_screen.name}.png")

    def cleanup(self):
        logger.info("ScreenManager cleanup called")