"""
Menu Data Service - Pure data layer for menu hierarchy and navigation.
Handles menu data access without UI state or event management.
"""

import logging
from typing import Optional, List, Dict, Any
from .json_menu_adapter import JsonMenuAdapter
from .subsonic_config_adapter import SubsonicConfigAdapter
from app.services.subsonic_service import SubsonicService

logger = logging.getLogger(__name__)


class MenuDataService:
    """
    Pure data service for menu hierarchy management.
    Handles menu navigation and data access without UI state.
    Supports both static JSON menus and dynamic Subsonic-based menus.
    """
    
    def __init__(self):
        """Initialize the menu data service."""
        self.json_config = JsonMenuAdapter()
        self.current_menu_level = "root"
        self.menu_history = []  # Stack for back navigation
        
        # Initialize SubsonicService and SubsonicConfigAdapter for dynamic menus
        try:
            self.subsonic_service = SubsonicService()
            self.subsonic_config = SubsonicConfigAdapter(self.subsonic_service)
            
            # Cache artists data on initialization for better performance
            self.subsonic_service.cache_artists_data()
            logger.info("MenuDataService initialized with dynamic menu support")
        except Exception as e:
            logger.error(f"Failed to initialize SubsonicService: {e}")
            self.subsonic_service = None
            self.subsonic_config = None
        
        # Dynamic menu storage (for caching dynamic menu results)
        self._dynamic_menus = {}
        
        # Load configuration
        self.json_config.load_config()
        
    def get_current_menu(self) -> Dict[str, Any]:
        """Get the current menu level data."""
        # Check if this is a dynamic menu
        if self.current_menu_level.startswith("dynamic_"):
            return self._dynamic_menus.get(self.current_menu_level, {"items": []})
        
        # Otherwise, get from static config
        return self.json_config.get_menu_data(self.current_menu_level)
    
    def get_current_menu_items(self) -> List[Dict[str, Any]]:
        """Get items for the current menu level."""
        current_menu = self.get_current_menu()
        items = current_menu.get("items", [])
        
        # Convert MenuNode objects to dict format if needed
        if items and hasattr(items[0], 'to_dict'):
            items = [item.to_dict() for item in items]
        
        return items

    def load_dynamic_menu(self, menu_type: str, **kwargs) -> bool:
        """
        Load a dynamic menu using the SubsonicConfigAdapter.
        
        Args:
            menu_type: Type of dynamic menu to load
            **kwargs: Additional parameters for menu generation
            
        Returns:
            True if menu was loaded successfully, False otherwise
        """
        if not self.subsonic_config:
            logger.error("SubsonicConfigAdapter not available for dynamic menu loading")
            return False
        
        try:
            # Generate unique menu identifier
            menu_id = f"dynamic_{menu_type}"
            if kwargs:
                # Add parameters to make unique identifier
                param_str = "_".join(f"{k}_{v}" for k, v in kwargs.items())
                menu_id += f"_{param_str}"
            
            # Get dynamic menu nodes
            menu_nodes = self.subsonic_config.get_dynamic_menu_nodes(menu_type, **kwargs)
            
            # Store in dynamic menus cache
            self._dynamic_menus[menu_id] = {"items": menu_nodes}
            
            # Navigate to the dynamic menu
            self.menu_history.append(self.current_menu_level)
            self.current_menu_level = menu_id
            
            logger.info(f"Loaded dynamic menu: {menu_id} with {len(menu_nodes)} items")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load dynamic menu {menu_type}: {e}")
            return False
    
    def navigate_to_menu(self, menu_level: str) -> bool:
        """
        Navigate to a specific menu level.
        
        Args:
            menu_level: The menu level identifier to navigate to
            
        Returns:
            True if navigation was successful, False otherwise
        """
        if self.json_config.menu_exists(menu_level):
            # Save current level to history for back navigation
            self.menu_history.append(self.current_menu_level)
            self.current_menu_level = menu_level
            logger.info(f"Navigated to menu level: {menu_level}")
            return True
        else:
            logger.warning(f"Menu level not found: {menu_level}")
            return False
    
    def go_back(self) -> bool:
        """
        Go back to the previous menu level.
        
        Returns:
            True if we went back, False if already at root
        """
        if self.menu_history:
            self.current_menu_level = self.menu_history.pop()
            logger.info(f"Went back to menu level: {self.current_menu_level}")
            return True
        else:
            logger.info("Already at root level, cannot go back")
            return False
    
    def reset_to_root(self):
        """Reset menu navigation to root level."""
        self.current_menu_level = "root"
        self.menu_history.clear()
        logger.info("Reset to root menu level")
    
    def get_breadcrumb_path(self) -> List[str]:
        """
        Get the breadcrumb path for the current menu location.
        
        Returns:
            List of menu level names from root to current
        """
        path = ["Root"]
        
        # Add history items to path
        for level in self.menu_history:
            menu_data = self.json_config.get_menu_data(level)
            name = menu_data.get("name", level.replace("_", " ").title())
            path.append(name)
        
        # Add current level if not root
        if self.current_menu_level != "root":
            menu_data = self.json_config.get_menu_data(self.current_menu_level)
            name = menu_data.get("name", self.current_menu_level.replace("_", " ").title())
            path.append(name)
        
        return path
    
    def find_menu_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a menu item by its ID in the current menu.
        
        Args:
            item_id: The ID of the menu item to find
            
        Returns:
            The menu item data if found, None otherwise
        """
        items = self.get_current_menu_items()
        for item in items:
            if item.get("id") == item_id:
                return item
        return None
    
    def get_menu_item_at_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get the menu item at the specified index.
        
        Args:
            index: The index of the menu item
            
        Returns:
            The menu item data if index is valid, None otherwise
        """
        items = self.get_current_menu_items()
        if 0 <= index < len(items):
            return items[index]
        return None
    
    def get_menu_count(self) -> int:
        """Get the number of items in the current menu."""
        return len(self.get_current_menu_items())
    
    def is_valid_index(self, index: int) -> bool:
        """Check if the given index is valid for the current menu."""
        return 0 <= index < self.get_menu_count()
