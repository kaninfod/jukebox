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
        
        # Pagination properties
        self.page_size = 8  # Increased from 7 to 8 due to removing bottom bar (40px more space)
        self.current_page = 0
        self.all_menu_items = []  # Cache of all items for current menu
        
        # Remove bottom bar properties - using Button 4 for back navigation
        # self.in_bottom_bar = False  # REMOVED
        # self.bottom_bar_selection = "previous"  # REMOVED
        
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
        
        # Initialize pagination
        self.current_page = 0
        self._load_current_menu_items()
        
        # Start auto-exit timer
        self._start_auto_exit_timer()
        
        # Emit event to show menu screen with initial context
        self._emit_menu_screen_update()
    
    def exit_menu_mode(self):
        """Exit menu mode and return to appropriate screen based on playback state"""
        if not self.is_active:
            return
            
        logger.info("Exiting menu mode")
        self.is_active = False
        
        # Cancel auto-exit timer
        self._cancel_auto_exit_timer()
        
        # Reset menu to root and pagination
        self.menu_data.reset_to_root()
        self.current_page = 0
        self.all_menu_items = []
        
        # Determine which screen to return to based on playback state
        if self._is_music_playing():
            event_bus.emit(Event(
                type=EventType.SHOW_HOME,
                payload={}
            ))
            logger.info("Returned to HOME screen (music playing)")
        else:
            event_bus.emit(Event(
                type=EventType.SHOW_IDLE,
                payload={}
            ))
            logger.info("Returned to IDLE screen (no music playing)")
    
    def navigate_up(self):
        """Handle up navigation (counter-clockwise) with pagination support"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        # Try to move up in current page
        if self.selected_index > 0:
            self.selected_index -= 1
        else:
            # At first item of current page, try to go to previous page
            if self.current_page > 0:
                # There's a previous page available
                self.current_page -= 1
                current_page_items = self.get_current_page_items()
                self.selected_index = len(current_page_items) - 1  # Go to last item of previous page
                logger.info(f"Went back to page {self.current_page + 1}")
            else:
                # Already at top of first page, wrap to bottom of last page
                self.current_page = (len(self.all_menu_items) - 1) // self.page_size
                current_page_items = self.get_current_page_items()
                self.selected_index = len(current_page_items) - 1
                logger.info("Wrapped to last page")
        
        self._emit_menu_screen_update()
    
    def navigate_down(self):
        """Handle down navigation (clockwise) with pagination support"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        current_page_items = self.get_current_page_items()
        
        # Try to move down in current page
        if self.selected_index < len(current_page_items) - 1:
            self.selected_index += 1
        else:
            # At last item of current page, try to advance to next page
            total_items = len(self.all_menu_items)
            next_page_start = (self.current_page + 1) * self.page_size
            
            if next_page_start < total_items:
                # There's a next page available
                self.current_page += 1
                self.selected_index = 0  # Go to first item of next page
                logger.info(f"Advanced to page {self.current_page + 1}")
            else:
                # Already at bottom of last page, wrap to top of first page
                self.current_page = 0
                self.selected_index = 0
                logger.info("Wrapped to first page")
        
        self._emit_menu_screen_update()
    
    def activate_selected(self):
        """Handle selection activation (button press) - simplified without bottom bar"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        # Get the selected item from current page
        current_page_items = self.get_current_page_items()
        if self.selected_index < len(current_page_items):
            menu_item = current_page_items[self.selected_index]
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
                # Load new menu items with pagination reset
                self._load_current_menu_items()
                self._emit_menu_screen_update()
            else:
                logger.warning(f"Failed to navigate to submenu: {submenu_name}")
        elif action == "load_dynamic_menu":
            # Load dynamic menu
            menu_type = payload.get("menu_type")
            menu_params = {k: v for k, v in payload.items() if k not in ["action", "menu_type"]}
            
            if menu_type and self.menu_data.load_dynamic_menu(menu_type, **menu_params):
                self.selected_index = 0
                # Load new dynamic menu items with pagination reset
                self._load_current_menu_items()
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
                    # Load new dynamic menu items with pagination reset
                    self._load_current_menu_items()
                    self._emit_menu_screen_update()
                else:
                    logger.warning(f"Failed to load artists in range {start_letter}-{end_letter}")
        elif action == "browse_artist_albums":
            # Browse albums for specific artist
            artist_id = payload.get("artist_id")
            
            if artist_id:
                if self.menu_data.load_dynamic_menu("artist_albums", artist_id=artist_id):
                    self.selected_index = 0
                    # Load new dynamic menu items with pagination reset
                    self._load_current_menu_items()
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
        """Navigate to previous menu level and reset pagination"""
        self._reset_auto_exit_timer()  # Reset timer on back navigation
        
        if self.menu_data.go_back():
            self.selected_index = 0
            # Reset pagination for new menu level
            self._load_current_menu_items()
            self._emit_menu_screen_update()
            logger.info("Navigated to previous menu level")
        else:
            # Already at root level - exit menu immediately
            logger.info("Back press at root level - exiting menu")
            self.exit_menu_mode()
    
    def _emit_menu_screen_update(self):
        """Emit event to update menu screen with current paginated state"""
        current_page_items = self.get_current_page_items()
        breadcrumb = self._get_breadcrumb()
        
        # Add pagination info to breadcrumb
        total_items = len(self.all_menu_items)
        if total_items > self.page_size:
            total_pages = (total_items - 1) // self.page_size + 1
            breadcrumb += f" ({self.current_page + 1}/{total_pages})"
        
        context = {
            "menu_items": current_page_items,
            "selected_index": self.selected_index,
            "breadcrumb": breadcrumb,
            # Remove bottom bar properties since we're not using them
            "total_items": total_items,
            "current_page": self.current_page + 1,
            "total_pages": (total_items - 1) // self.page_size + 1 if total_items > 0 else 1
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
            return f"MENU: {' > '.join(breadcrumb_path[1:])}"  # Use ASCII > instead of Unicode →
    
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
        elif button == 4:  # Button 4 dual mode
            if self.is_active:
                # Menu mode: Button 4 = Back button
                self._go_back()
            # Note: Non-menu mode (playback stop) handled by PlaybackManager
    
    # === PAGINATION METHODS ===
    
    def _load_current_menu_items(self):
        """Load all menu items for current menu level and reset pagination"""
        self.all_menu_items = self.menu_data.get_current_menu_items()
        self.current_page = 0
        logger.info(f"Loaded {len(self.all_menu_items)} total items for current menu")
    
    def get_current_page_items(self):
        """Get the items for the current page"""
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        return self.all_menu_items[start_idx:end_idx]
    
    def _is_music_playing(self):
        """Check if music is currently playing by querying player status via EventBus"""
        try:
            # We need a way to get player status - for now use a simple approach
            # This could be improved by having the player emit status events
            # or by injecting the player reference
            
            # For now, emit a status request and assume we get a response
            # A more robust implementation would use a status cache or direct reference
            from app.main import app_state
            if hasattr(app_state, 'player') and app_state.player:
                from app.services.jukebox_mediaplayer import PlayerStatus
                return app_state.player.status in [PlayerStatus.PLAY, PlayerStatus.PAUSE]
            return False
        except Exception as e:
            logger.warning(f"Could not determine player status: {e}")
            # Default to HOME if we can't determine status
            return True
