"""
Menu configuration loader for JSON-based menu definitions.
"""

import json
import os
from typing import Dict, Any, Optional
from .menu_node import MenuNode
import logging

logger = logging.getLogger(__name__)


class MenuConfig:
    """Loads and manages menu configuration from JSON files."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize menu config loader.
        
        Args:
            config_file: Path to JSON config file. If None, uses default.
        """
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "menu_config.json")
        
        self.config_file = config_file
        self.menu_data: Dict[str, Any] = {}
        self.root_menu: Optional[MenuNode] = None
        
    def load_config(self) -> bool:
        """Load menu configuration from JSON file."""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Menu config file not found: {self.config_file}")
                self._create_default_config()
                
            with open(self.config_file, 'r') as f:
                self.menu_data = json.load(f)
                
            self.root_menu = self._build_menu_tree()
            logger.info(f"Menu configuration loaded successfully from {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load menu config: {e}")
            self._create_fallback_menu()
            return False
            
    def _build_menu_tree(self) -> MenuNode:
        """Build the menu tree from loaded configuration."""
        # Create root menu container
        root = MenuNode("root", "Main Menu")
        
        # Build menus recursively
        if "root" in self.menu_data:
            self._build_menu_level(root, self.menu_data["root"])
            
        return root
        
    def _build_menu_level(self, parent: MenuNode, menu_config: Dict[str, Any]):
        """Recursively build menu levels."""
        if "items" not in menu_config:
            return
            
        for item_config in menu_config["items"]:
            # Create menu item
            menu_item = MenuNode(
                id=item_config.get("id", ""),
                name=item_config.get("name", "Unknown"),
                payload=item_config.get("payload", {}),
                parent=parent
            )
            parent.add_child(menu_item)
            
            # If this item references a submenu, build it
            payload = item_config.get("payload", {})
            if payload.get("action") == "load_submenu":
                submenu_id = payload.get("submenu")
                if submenu_id and submenu_id in self.menu_data:
                    self._build_menu_level(menu_item, self.menu_data[submenu_id])
                    
    def _create_default_config(self):
        """Create a default menu configuration file."""
        default_config = {
            "root": {
                "items": [
                    {
                        "id": "music",
                        "name": "Music Library",
                        "payload": {"action": "load_submenu", "submenu": "music_menu"}
                    },
                    {
                        "id": "settings", 
                        "name": "Settings",
                        "payload": {"action": "load_submenu", "submenu": "settings_menu"}
                    },
                    {
                        "id": "chromecast",
                        "name": "Chromecast",
                        "payload": {"action": "chromecast_info"}
                    },
                    {
                        "id": "system",
                        "name": "System Info",
                        "payload": {"action": "system_info"}
                    }
                ]
            },
            "music_menu": {
                "items": [
                    {
                        "id": "random_album",
                        "name": "Random Album",
                        "payload": {"action": "play_random_album"}
                    },
                    {
                        "id": "browse_artists",
                        "name": "Browse Artists", 
                        "payload": {"action": "browse_artists"}
                    }
                ]
            },
            "settings_menu": {
                "items": [
                    {
                        "id": "volume",
                        "name": "Volume Settings",
                        "payload": {"action": "volume_settings"}
                    },
                    {
                        "id": "display",
                        "name": "Display Settings",
                        "payload": {"action": "display_settings"}
                    }
                ]
            }
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default menu config at {self.config_file}")
            self.menu_data = default_config
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            
    def _create_fallback_menu(self):
        """Create a minimal fallback menu in case of config errors."""
        self.root_menu = MenuNode("root", "Main Menu")
        self.root_menu.add_child(MenuNode("error", "Config Error", {"action": "config_error"}))
        logger.info("Created fallback menu due to config error")
        
    def get_root_menu(self) -> Optional[MenuNode]:
        """Get the root menu node."""
        return self.root_menu
        
    def reload_config(self) -> bool:
        """Reload the configuration from file."""
        return self.load_config()
