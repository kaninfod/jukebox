"""
Menu system package with clean architecture.

Components:
- MenuController: Main controller for menu navigation and state
- MenuDataService: Pure data service for menu hierarchy management  
- JsonMenuAdapter: JSON menu loader for static menus
- SubsonicConfigAdapter: Dynamic menu generator from Subsonic API
- MenuNode: Data structure for menu items
"""

from .menu_controller import MenuController
from .menu_data_service import MenuDataService
from .json_menu_adapter import JsonMenuAdapter
from .subsonic_config_adapter import SubsonicConfigAdapter
from .menu_node import MenuNode

__all__ = [
    'MenuController',
    'MenuDataService', 
    'JsonMenuAdapter',
    'SubsonicConfigAdapter',
    'MenuNode'
]
