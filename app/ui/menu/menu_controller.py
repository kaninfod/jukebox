"""
Menu Controller - Handles menu navigation logic and state management.
Communicates with ScreenManager via EventBus for loose coupling.
"""

import logging
import threading
from app.ui.menu.menu_data_service import MenuDataService
from app.core import event_bus, EventType, Event
from app.config import config
from app.core import PlayerStatus
from app.metrics.decorators import track_event_handler

logger = logging.getLogger(__name__)

class MenuController:
    """
    Handles menu navigation logic and state management.
    Subscribes to hardware events and emits screen events.
    """
    
    def __init__(self):
        self.menu_data = MenuDataService()
        self.is_active = False
        self.selected_index = 0  # Which item is highlighted in current view
        self.page_size = 8  # Display shows 8 items at a time
        self._player_status = False
        
        self.auto_exit_timer = None
        self.auto_exit_timeout = config.MENU_AUTO_EXIT_TIMEOUT
        
        # Action type handlers (Strategy Pattern)
        from .menu_event_processor import ActionType
        self.action_handlers = {
            ActionType.NAVIGATE: self._action_navigate,
            ActionType.LOAD_DYNAMIC: self._action_load_dynamic,
            ActionType.SELECT_ALBUM: self._action_select_album,
            ActionType.SELECT_DEVICE: self._action_select_device,
            ActionType.RESTART_APP: self._action_restart_app,
            ActionType.REBOOT_SYSTEM: self._action_reboot_system,
            ActionType.SHUTDOWN_SYSTEM: self._action_shutdown_system,
        }
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        logger.info("MenuController initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to EventBus events"""
        # Hardware events (when in menu mode)
        event_bus.subscribe(EventType.ROTARY_ENCODER, self._handle_rotary_encoder)
        event_bus.subscribe(EventType.BUTTON_PRESSED, self._handle_button_press)
        event_bus.subscribe(EventType.STATUS_CHANGED, self._handle_player_changes)
        
        logger.info("MenuController subscribed to EventBus events")
    
    def enter_menu_mode(self):
        """Enter menu mode and show menu screen"""
        if self.is_active:
            logger.warning("Menu already active")
            return
            
        logger.info("Entering menu mode")
        self.is_active = True
        self.selected_index = 0
        
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
        
        # Reset menu to root and selection
        self.menu_data.reset_to_root()
        self.selected_index = 0
        
        # Determine which screen to return to based on playback state
        if self._player_status:
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
        """Handle up navigation (counter-clockwise)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        current_items = self.menu_data.get_current_menu_items()
        total = len(current_items)
        
        if total == 0:
            return
        
        # Wrap around if at top
        if self.selected_index > 0:
            self.selected_index -= 1
        else:
            self.selected_index = total - 1
        
        self._emit_menu_screen_update()
    
    def navigate_down(self):
        """Handle down navigation (clockwise)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        current_items = self.menu_data.get_current_menu_items()
        total = len(current_items)
        
        if total == 0:
            return
        
        # Wrap around if at bottom
        if self.selected_index < total - 1:
            self.selected_index += 1
        else:
            self.selected_index = 0
        
        self._emit_menu_screen_update()
    
    def activate_selected(self):
        """Handle selection activation (button press)"""
        if not self.is_active:
            return
            
        self._reset_auto_exit_timer()
        
        current_items = self.menu_data.get_current_menu_items()
        if self.selected_index < len(current_items):
            menu_node = current_items[self.selected_index]
            if menu_node:
                self._activate_menu_item(menu_node)
                self.selected_index = 0  # Reset selection for new menu level
    
    def _activate_menu_item(self, node):
        """Process menu item activation using Strategy Pattern dispatch
        
        Args:
            node: MenuNode object that was selected
        """
        from .menu_event_processor import MenuEventProcessor, ActionType
        processor = MenuEventProcessor()
        event = processor.process_node_selection(node)
        
        if not event:
            logger.warning(f"No event generated for node: {node.id}")
            return
        
        action_type = event.action_type
        payload = event.parameters
        
        logger.info(f"Activating menu item: {node.name} (action: {action_type.value})")
        
        # Dispatch to handler via strategy dict
        handler = self.action_handlers.get(action_type)
        if handler:
            handler(node, payload)
        else:
            logger.warning(f"Unknown action type: {action_type}")
    
    def _action_navigate(self, node, payload):
        """Handle NAVIGATE action - navigate to submenu"""
        if self.menu_data.navigate_to_node(node):
            self.selected_index = 0
            self._emit_menu_screen_update()
        else:
            logger.warning(f"Failed to navigate to: {node.id}")
    
    def _action_load_dynamic(self, node, payload):
        """Handle LOAD_DYNAMIC action - load dynamic content (artists/albums)"""
        dynamic_type = payload.get("dynamic_type")
        
        if dynamic_type == "artists_in_range":
            start_letter = payload.get("start_letter")
            end_letter = payload.get("end_letter")
            if start_letter and end_letter:
                self._load_dynamic_artists(node, start_letter, end_letter)
            else:
                logger.warning("Missing start_letter or end_letter for artists_in_range")
        
        elif dynamic_type == "artist_albums":
            artist_id = payload.get("artist_id")
            artist_name = payload.get("artist_name", "Unknown Artist")
            if artist_id:
                self._load_dynamic_albums(node, artist_id, artist_name)
            else:
                logger.warning("Missing artist_id for artist_albums")
        else:
            logger.warning(f"Unknown dynamic_type: {dynamic_type}")
    
    def _action_select_album(self, node, payload):
        """Handle SELECT_ALBUM action - play selected album"""
        album_id = payload.get("album_id")
        if album_id:
            logger.info(f"Playing album: {node.name} (ID: {album_id})")
            event_bus.emit(Event(
                type=EventType.PLAY_ALBUM,
                payload={"album_id": album_id, "album_name": node.name}
            ))
            self.exit_menu_mode()
        else:
            logger.warning("No album_id provided for select_album action")
    
    def _action_select_device(self, node, payload):
        """Handle SELECT_DEVICE action - switch Chromecast device"""
        device_name = payload.get("device_name")
        if device_name:
            logger.info(f"Selecting device: {device_name}")
            event_bus.emit(Event(
                type=EventType.CHROMECAST_DEVICE_CHANGED,
                payload={"device_name": device_name}
            ))
            event_bus.emit(Event(
                type=EventType.SHOW_MESSAGE,
                payload={"message": f"Switching to {device_name}...", "duration": 2, "type": "info"}
            ))
            self.exit_menu_mode()
        else:
            logger.warning("No device_name for select_device action")
    
    def _action_restart_app(self, node, payload):
        """Handle RESTART_APP action - restart the application"""
        logger.info("Restarting application as per menu selection")
        event_bus.emit(Event(
            type=EventType.SYSTEM_RESTART_REQUESTED,
            payload={}
        ))
        self.exit_menu_mode()

    def _action_reboot_system(self, node, payload):
        """Handle REBOOT_SYSTEM action - reboot the entire system"""
        logger.info("Rebooting system as per menu selection")
        event_bus.emit(Event(
            type=EventType.SYSTEM_REBOOT_REQUESTED,
            payload={}
        ))
        self.exit_menu_mode()

    def _action_shutdown_system(self, node, payload):
        """Handle SHUTDOWN_SYSTEM action - shutdown the entire system"""
        logger.info("Shutting down system as per menu selection")
        event_bus.emit(Event(
            type=EventType.SYSTEM_SHUTDOWN_REQUESTED,
            payload={}
        ))
        self.exit_menu_mode()

    def _load_dynamic_artists(self, parent_node, start_letter: str, end_letter: str):
        """Load artists in alphabetical range and inject into tree."""
        try:
            from .dynamic_loader import get_dynamic_loader
            
            loader = get_dynamic_loader()
            if not loader:
                logger.warning("DynamicLoader not initialized")
                return
            
            logger.info(f"Loading artists for range {start_letter}-{end_letter}")
            artist_nodes = loader.load_artists_in_range(start_letter, end_letter)
            
            if not artist_nodes:
                logger.warning(f"No artists found for range {start_letter}-{end_letter}")
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.SHOW_MESSAGE,
                    payload={"message": f"No artists found for {start_letter}-{end_letter}", "duration": 2, "type": "warning"}
                ))
                return
            
            # Inject artist nodes into the parent node
            for artist_node in artist_nodes:
                parent_node.add_child(artist_node)
                artist_node.parent = parent_node
            
            logger.info(f"Injected {len(artist_nodes)} artists as children of {parent_node.id}")
            
            # Navigate to this node to show artists
            if self.menu_data.navigate_to_node(parent_node):
                self.selected_index = 0
                self._emit_menu_screen_update()
                logger.info(f"Navigated to artist range {start_letter}-{end_letter}")
            else:
                logger.warning(f"Failed to navigate to artist range")
            
        except Exception as e:
            logger.error(f"Error loading artists: {e}")
            from app.core import event_bus, EventType, Event
            event_bus.emit(Event(
                type=EventType.SHOW_MESSAGE,
                payload={"message": "Error loading artists", "duration": 2, "type": "error"}
            ))
    
    def _load_dynamic_albums(self, artist_node, artist_id: str, artist_name: str):
        """Load albums for an artist and inject into tree."""
        try:
            from .dynamic_loader import get_dynamic_loader
            
            loader = get_dynamic_loader()
            if not loader:
                logger.warning("DynamicLoader not initialized")
                return
            
            logger.info(f"Loading albums for artist {artist_name} ({artist_id})")
            album_nodes = loader.load_artist_albums(artist_id, artist_name)
            
            if not album_nodes:
                logger.warning(f"No albums found for artist {artist_name}")
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.SHOW_MESSAGE,
                    payload={"message": f"No albums found for {artist_name}", "duration": 2, "type": "warning"}
                ))
                return
            
            # Inject album nodes into the artist node
            for album_node in album_nodes:
                artist_node.add_child(album_node)
                album_node.parent = artist_node
            
            logger.info(f"Injected {len(album_nodes)} albums as children of {artist_node.id}")
            
            # Navigate to this node to show albums
            if self.menu_data.navigate_to_node(artist_node):
                self.selected_index = 0
                self._emit_menu_screen_update()
                logger.info(f"Navigated to artist {artist_name}")
            else:
                logger.warning(f"Failed to navigate to artist {artist_name}")
            
        except Exception as e:
            logger.error(f"Error loading albums: {e}")
            from app.core import event_bus, EventType, Event
            event_bus.emit(Event(
                type=EventType.SHOW_MESSAGE,
                payload={"message": "Error loading albums", "duration": 2, "type": "error"}
            ))
    
    def _go_back(self):
        """Navigate to previous menu level"""
        self._reset_auto_exit_timer()
        
        if self.menu_data.go_back():
            self.selected_index = 0
            self._emit_menu_screen_update()
            logger.info("Navigated to previous menu level")
        else:
            # Already at root level - exit menu
            logger.info("Back press at root level - exiting menu")
            self.exit_menu_mode()
    
    def _emit_menu_screen_update(self):
        """Emit event to update menu screen with current state"""
        current_items = self.menu_data.get_current_menu_items()
        total_items = len(current_items)
        
        # Calculate current page (for pagination display purposes only)
        current_page = self.selected_index // self.page_size
        total_pages = (total_items - 1) // self.page_size + 1 if total_items > 0 else 1
        
        # Get items for current page
        page_start = current_page * self.page_size
        page_end = page_start + self.page_size
        page_items = current_items[page_start:page_end]
        
        # Adjust selected_index to be relative to current page
        selected_in_page = self.selected_index % self.page_size
        
        breadcrumb = self._get_breadcrumb()
        if total_items > self.page_size:
            breadcrumb += f" ({current_page + 1}/{total_pages})"
        
        context = {
            "menu_items": [item.to_dict() for item in page_items],
            "selected_index": selected_in_page,
            "breadcrumb": breadcrumb,
            "total_items": total_items,
            "current_page": current_page + 1,
            "total_pages": total_pages
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
            return f"MENU: {' > '.join(breadcrumb_path[1:])}"
    
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
    @track_event_handler("PLAYER_CHANGE")
    def _handle_player_changes(self, event):
        """Update internal player status on status change events"""
        self._player_status = PlayerStatus(event.payload.get('status'))

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
        """Central handler for button press events, including button 4 logic."""
        button = event.payload.get("button")

        if button == "rotary_encoder":
            if not self.is_active:
                self.enter_menu_mode()
            else:
                self.activate_selected()
        elif button == 4:
            if self.is_active:
                # Menu mode: Button 4 = Back button
                self._go_back()
            else:
                # Not in menu: emit STOP event for playback manager
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(type=EventType.STOP, payload={}))
                import logging
                logging.getLogger(__name__).info("Button 4 pressed outside menu: STOP event emitted")
    
