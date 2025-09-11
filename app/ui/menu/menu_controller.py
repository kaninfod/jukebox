"""
Menu Controller - Handles menu navigation logic and state management.
Communicates with ScreenManager via EventBus for loose coupling.
"""

import logging
import threading
from app.ui.menu.menu_data_service import MenuDataService
from app.core import event_bus, EventType, Event
from app.config import config

logger = logging.getLogger(__name__)

class MenuController:
    """
    Handles menu navigation logic and state management.
    Subscribes to hardware events and emits screen events.
    """
    
    def __init__(self):
        self.menu_data = MenuDataService()
        self.is_active = False
        self.selected_index = 0
        self.in_bottom_bar = False
        self.bottom_bar_selection = "previous"  # "previous" or "exit"
        self.auto_exit_timer = None
        self.auto_exit_timeout = config.MENU_AUTO_EXIT_TIMEOUT
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        logger.info("MenuController initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to EventBus events"""
        # Hardware events (when in menu mode)
        event_bus.subscribe(EventType.ROTARY_ENCODER, self._handle_rotary_encoder)
        event_bus.subscribe(EventType.BUTTON_PRESSED, self._handle_button_press)
        
        logger.info("MenuController subscribed to EventBus events")
    
    def enter_menu_mode(self):
        """Enter menu mode and show menu screen"""
        if self.is_active:
            logger.warning("Menu already active")
            return
            
        logger.info("Entering menu mode")
        self.is_active = True
        self.selected_index = 0
        self.in_bottom_bar = False
        self.bottom_bar_selection = "previous"
        
        # Start auto-exit timer
        self._start_auto_exit_timer()
        
        # Emit event to show menu screen with initial context
        self._emit_menu_screen_update()
    
    def exit_menu_mode(self):
        """Exit menu mode and return to appropriate screen"""
        if not self.is_active:
            return
            
        logger.info("Exiting menu mode")
        self.is_active = False
        
        # Cancel auto-exit timer
        self._cancel_auto_exit_timer()
        
        # Reset menu to root
        self.menu_data.reset_to_root()
        
        # Determine which screen to return to
        # TODO: Check if music is playing to decide between HOME/IDLE
        # For now, default to HOME
        event_bus.emit(Event(
            type=EventType.SHOW_HOME,
            payload={}
        ))
    
    def navigate_up(self):
        """Handle up navigation (counter-clockwise)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        menu_items = self.menu_data.get_current_menu_items()
        
        if self.in_bottom_bar:
            if self.bottom_bar_selection == "exit":
                self.bottom_bar_selection = "previous"
            else:
                # Move to last menu item
                self.in_bottom_bar = False
                self.selected_index = len(menu_items) - 1
        else:
            if self.selected_index > 0:
                self.selected_index -= 1
            else:
                # Move to bottom bar
                self.in_bottom_bar = True
                self.bottom_bar_selection = "exit"
        
        self._emit_menu_screen_update()
    
    def navigate_down(self):
        """Handle down navigation (clockwise)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        menu_items = self.menu_data.get_current_menu_items()
        
        if self.in_bottom_bar:
            if self.bottom_bar_selection == "previous":
                self.bottom_bar_selection = "exit"
            else:
                # Move to first menu item
                self.in_bottom_bar = False
                self.selected_index = 0
        else:
            if self.selected_index < len(menu_items) - 1:
                self.selected_index += 1
            else:
                # Move to bottom bar
                self.in_bottom_bar = True
                self.bottom_bar_selection = "previous"
        
        self._emit_menu_screen_update()
    
    def activate_selected(self):
        """Handle selection activation (button press)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        if self.in_bottom_bar:
            if self.bottom_bar_selection == "previous":
                self._go_back()
            else:  # exit
                self.exit_menu_mode()
        else:
            # Activate selected menu item
            menu_item = self.menu_data.get_menu_item_at_index(self.selected_index)
            if menu_item:
                self._activate_menu_item(menu_item)
    
    def _activate_menu_item(self, item):
        """Process menu item activation"""
        payload = item.get("payload", {})
        action = payload.get("action")
        
        logger.info(f"Activating menu item: {item['name']} (action: {action})")
        
        if action == "load_submenu":
            # Navigate to submenu
            submenu_name = payload.get("submenu")
            if submenu_name and self.menu_data.navigate_to_menu(submenu_name):
                self.selected_index = 0
                self.in_bottom_bar = False
                self._emit_menu_screen_update()
            else:
                logger.warning(f"Failed to navigate to submenu: {submenu_name}")
        elif action == "load_dynamic_menu":
            # Load dynamic menu
            menu_type = payload.get("menu_type")
            menu_params = {k: v for k, v in payload.items() if k not in ["action", "menu_type"]}
            
            if menu_type and self.menu_data.load_dynamic_menu(menu_type, **menu_params):
                self.selected_index = 0
                self.in_bottom_bar = False
                self._emit_menu_screen_update()
            else:
                logger.warning(f"Failed to load dynamic menu: {menu_type}")
        elif action == "browse_artists_in_range":
            # Browse artists in alphabetical range
            start_letter = payload.get("start_letter")
            end_letter = payload.get("end_letter")
            
            if start_letter and end_letter:
                if self.menu_data.load_dynamic_menu("artists_in_range", 
                                                   start_letter=start_letter, 
                                                   end_letter=end_letter):
                    self.selected_index = 0
                    self.in_bottom_bar = False
                    self._emit_menu_screen_update()
                else:
                    logger.warning(f"Failed to load artists in range {start_letter}-{end_letter}")
        elif action == "browse_artist_albums":
            # Browse albums for specific artist
            artist_id = payload.get("artist_id")
            
            if artist_id:
                if self.menu_data.load_dynamic_menu("artist_albums", artist_id=artist_id):
                    self.selected_index = 0
                    self.in_bottom_bar = False
                    self._emit_menu_screen_update()
                else:
                    logger.warning(f"Failed to load albums for artist {artist_id}")
        elif action == "play_album":
            # Play album - emit PLAY_ALBUM event for playback manager
            album_id = payload.get("album_id")
            album_name = payload.get("album_name")
            
            if album_id:
                logger.info(f"Playing album: {album_name} (ID: {album_id})")
                
                # Emit PLAY_ALBUM event to be handled by playback manager
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.PLAY_ALBUM,
                    payload={
                        "audioPlaylistId": album_id,
                        "album_name": album_name
                    }
                ))
                
                # Exit menu after triggering playback
                self.exit_menu_mode()
            else:
                logger.warning("No album_id provided for play_album action")
        elif action == "select_chromecast_device":
            # Handle Chromecast device selection
            device_name = payload.get("device_name")
            
            if device_name:
                logger.info(f"Selecting Chromecast device: {device_name}")
                
                # Emit CHROMECAST_DEVICE_CHANGED event
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.CHROMECAST_DEVICE_CHANGED,
                    payload={
                        "device_name": device_name
                    }
                ))
                
                # Show confirmation message and exit menu
                event_bus.emit(Event(
                    type=EventType.SHOW_MESSAGE,
                    payload={
                        "message": f"Switching to {device_name}...",
                        "duration": 2,
                        "type": "info"
                    }
                ))
                self.exit_menu_mode()
            else:
                logger.warning("No device_name provided for select_chromecast_device action")
        elif action == "chromecast_status":
            # Show current Chromecast status
            from app.core import event_bus, EventType, Event
            event_bus.emit(Event(
                type=EventType.SHOW_MESSAGE,
                payload={
                    "message": "📊 Getting Chromecast status...",
                    "duration": 2,
                    "type": "info"
                }
            ))
            # TODO: Add detailed status handler
            self.exit_menu_mode()
        elif action == "chromecast_volume_control":
            # Show volume control info
            from app.core import event_bus, EventType, Event
            event_bus.emit(Event(
                type=EventType.SHOW_MESSAGE,
                payload={
                    "message": "🔊 Use rotary encoder for volume",
                    "duration": 3,
                    "type": "info"
                }
            ))
            self.exit_menu_mode()
        elif action == "separator":
            # Separators are not selectable - ignore
            pass
        elif action == "go_back":
            self._go_back()
        elif action == "exit_menu":
            self.exit_menu_mode()
        else:
            # Unknown action - log warning
            logger.warning(f"Unknown menu action: {action} for item: {item['name']}")
    
    def _go_back(self):
        """Navigate to previous menu level"""
        if self.menu_data.go_back():
            self.selected_index = 0
            self.in_bottom_bar = False
            self._emit_menu_screen_update()
            logger.info("Navigated to previous menu level")
        else:
            # Already at root, exit menu
            self.exit_menu_mode()
    
    def _emit_menu_screen_update(self):
        """Emit event to update menu screen with current state"""
        menu_items = self.menu_data.get_current_menu_items()
        breadcrumb = self._get_breadcrumb()
        
        context = {
            "menu_items": menu_items,
            "selected_index": self.selected_index,
            "in_bottom_bar": self.in_bottom_bar,
            "bottom_bar_selection": self.bottom_bar_selection,
            "breadcrumb": breadcrumb
        }
        
        event_bus.emit(Event(
            type=EventType.SHOW_MENU,
            payload=context
        ))
    
    def _get_breadcrumb(self):
        """Generate breadcrumb text for current menu level"""
        breadcrumb_path = self.menu_data.get_breadcrumb_path()
        if len(breadcrumb_path) <= 1:
            return "MENU"
        else:
            return f"MENU: {' → '.join(breadcrumb_path[1:])}"
    
    def _start_auto_exit_timer(self):
        """Start the auto-exit timer"""
        self._cancel_auto_exit_timer()
        self.auto_exit_timer = threading.Timer(self.auto_exit_timeout, self._auto_exit)
        self.auto_exit_timer.start()
        logger.debug(f"Auto-exit timer started ({self.auto_exit_timeout}s)")
    
    def _reset_auto_exit_timer(self):
        """Reset the auto-exit timer"""
        if self.is_active:
            self._start_auto_exit_timer()
    
    def _cancel_auto_exit_timer(self):
        """Cancel the auto-exit timer"""
        if self.auto_exit_timer:
            self.auto_exit_timer.cancel()
            self.auto_exit_timer = None
    
    def _auto_exit(self):
        """Auto-exit menu after timeout"""
        logger.info("Menu auto-exit triggered")
        self.exit_menu_mode()
    
    # Event handlers
    def _handle_rotary_encoder(self, event):
        """Handle rotary encoder events when menu is active"""
        
        # Only handle if menu is active
        if not self.is_active:
            return  # Let PlaybackManager handle volume control
            
        direction = event.payload.get("direction")
        if direction == "CW":
            self.navigate_down()
        elif direction == "CCW":
            self.navigate_up()
    
    def _handle_button_press(self, event):
        """Handle button press events when in menu mode"""
        button = event.payload.get("button")
        
        if button == "rotary_encoder":
            if not self.is_active:
                # Enter menu mode
                self.enter_menu_mode()
            else:
                # Activate selected item
                self.activate_selected()
