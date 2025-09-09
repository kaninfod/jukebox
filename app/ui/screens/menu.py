import logging
from app.ui.screens.base import Screen, RectElement, MenuItemElement, MenuHeaderElement, MenuBottomBarElement

logger = logging.getLogger(__name__)

class MenuScreen(Screen):
    """
    Pure presentation layer for menu system.
    Receives context from MenuController and renders UI elements.
    """
    
    def __init__(self, theme):
        super().__init__(width=480, height=320)  # Explicit screen dimensions
        self.name = "Menu"
        self.dirty = True
        self.theme = theme
        
    @staticmethod
    def show(context=None):
        """Emit an event to show the menu screen via the event bus."""
        from app.core import event_bus, EventType, Event
        event_bus.emit(Event(
            type=EventType.SHOW_MENU,
            payload=context
        ))
        logger.info(f"EventBus: Emitted 'show_menu' event from MenuScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        """
        Draw the menu screen based on provided context.
        
        Expected context structure:
        {
            "menu_items": [...],
            "selected_index": 2,
            "in_bottom_bar": False,
            "bottom_bar_selection": "previous",
            "breadcrumb": "MENU: Music → Albums"
        }
        """
        if not self.dirty and context is None:
            logger.debug("MenuScreen is not dirty and no context provided, skipping draw.")
            return {"dirty": self.dirty}

        logger.debug(f"MenuScreen.draw() called with context: {context}")
        
        # Use context or defaults
        if context:
            menu_items = context.get("menu_items", [])
            selected_index = context.get("selected_index", 0)
            in_bottom_bar = context.get("in_bottom_bar", False)
            bottom_bar_selection = context.get("bottom_bar_selection", "previous")
            breadcrumb = context.get("breadcrumb", "MENU")
        else:
            # Fallback defaults for testing
            menu_items = []
            selected_index = 0
            in_bottom_bar = False
            bottom_bar_selection = "previous"
            breadcrumb = "MENU"
        
        # Calculate layout
        header_height = 40
        bottom_bar_height = 40
        menu_area_height = self.height - header_height - bottom_bar_height
        item_height = 35
        
        # Draw white background
        background = RectElement(0, 0, self.width, self.height, "white")
        background.draw(draw_context)
        
        # Draw header with breadcrumb
        header = MenuHeaderElement(0, 0, self.width, header_height, breadcrumb, fonts["title"])
        header.draw(draw_context)
        
        # Draw menu items
        menu_start_y = header_height
        max_visible_items = menu_area_height // item_height
        
        for i, item in enumerate(menu_items[:max_visible_items]):
            y_pos = menu_start_y + (i * item_height)
            is_selected = (not in_bottom_bar) and (i == selected_index)
            
            menu_item = MenuItemElement(
                0, y_pos, self.width, item_height,
                item.get("name", "Unknown"), fonts["info"], is_selected
            )
            menu_item.draw(draw_context)
        
        # Draw bottom bar
        bottom_bar_y = self.height - bottom_bar_height
        selected_button = None
        if in_bottom_bar:
            selected_button = bottom_bar_selection
            
        bottom_bar = MenuBottomBarElement(
            0, bottom_bar_y, self.width, bottom_bar_height,
            fonts["info"], selected_button
        )
        bottom_bar.draw(draw_context)
        
        self.dirty = False
        return {"dirty": True}  # Always return dirty=True to force refresh
