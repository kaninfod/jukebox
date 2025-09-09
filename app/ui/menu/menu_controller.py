"""
Menu Controller - Handles menu navigation logic and state management.
Communicates with ScreenManager via EventBus for loose coupling.
"""

import logging
import threading
from app.ui.menu.menu_data_service import MenuDataService
from app.core import event_bus, EventType, Event

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
        self.auto_exit_timeout = 10  # seconds
        
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
