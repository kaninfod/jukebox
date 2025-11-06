"""
Menu system package with clean architecture.

Components:
- MenuBuilder: Loads JSON config and builds MenuNode tree
- MenuNode: Data structure for menu items
- MenuEventProcessor: Routes menu actions
- MenuDataService: Navigation and hierarchy management
- MenuController: Main orchestrator for all interactions
- DynamicLoader: Fetches runtime content from Subsonic API
"""

from .menu_controller import MenuController
from .menu_data_service import MenuDataService
from .menu_node import MenuNode
from .menu_builder import MenuBuilder, get_menu_builder, initialize_menu_tree, find_menu_node
from .menu_event_processor import MenuEventProcessor, ActionType
from .dynamic_loader import DynamicLoader, get_dynamic_loader, initialize_dynamic_loader

__all__ = [
    'MenuController',
    'MenuDataService',
    'MenuNode',
    'MenuBuilder',
    'get_menu_builder',
    'initialize_menu_tree',
    'find_menu_node',
    'MenuEventProcessor',
    'ActionType',
    'DynamicLoader',
    'get_dynamic_loader',
    'initialize_dynamic_loader',
]
