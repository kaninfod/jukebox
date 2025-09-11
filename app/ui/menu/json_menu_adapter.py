"""
JSON menu adapter for loading static menu structures from JSON files.
"""

import json
import os
from typing import Dict, Any, Optional
from .menu_node import MenuNode
import logging

logger = logging.getLogger(__name__)


class JsonMenuAdapter:
    """Loads and manages menu configuration from JSON files."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize JSON menu adapter.
        
        Args:
            config_file: Path to JSON config file. If None, uses default.
        """
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "menu_config.json")
        
        self.config_file = config_file
        self.menu_data: Dict[str, Any] = {}
        self.root_menu: Optional[MenuNode] = None
        
    def load_config(self) -> bool:
        """
        Load menu configuration from JSON file.
        
        Returns:
            True if config was loaded successfully, False otherwise
        """
        try:
            with open(self.config_file, 'r') as f:
                self.menu_data = json.load(f)
            
            logger.info(f"Menu configuration loaded successfully from {self.config_file}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Menu config file not found: {self.config_file}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self.config_file}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading menu config: {e}")
            return False
    
    def get_menu_data(self, menu_key: str) -> Dict[str, Any]:
        """
        Get menu data for a specific menu key.
        
        Args:
            menu_key: The key identifying the menu level
            
        Returns:
            Dictionary containing menu data
        """
        return self.menu_data.get(menu_key, {})
    
    def get_menu_items(self, menu_key: str) -> list:
        """
        Get menu items for a specific menu key.
        
        Args:
            menu_key: The key identifying the menu level
            
        Returns:
            List of menu item dictionaries
        """
        menu_data = self.get_menu_data(menu_key)
        return menu_data.get("items", [])
    
    def validate_config(self) -> bool:
        """
        Validate the loaded configuration structure.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.menu_data:
            logger.error("No menu data loaded")
            return False
        
        if "root" not in self.menu_data:
            logger.error("No root menu found in configuration")
            return False
        
        root_items = self.get_menu_items("root")
        if not root_items:
            logger.error("No items found in root menu")
            return False
        
        logger.info("Menu configuration validation passed")
        return True
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload was successful, False otherwise
        """
        logger.info("Reloading menu configuration...")
        return self.load_config()
    
    def save_config(self, output_file: str = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            output_file: File to save to. If None, uses current config file.
            
        Returns:
            True if save was successful, False otherwise
        """
        target_file = output_file or self.config_file
        
        try:
            with open(target_file, 'w') as f:
                json.dump(self.menu_data, f, indent=2)
            
            logger.info(f"Menu configuration saved to {target_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving menu config to {target_file}: {e}")
            return False
    
    def get_all_menu_keys(self) -> list:
        """
        Get all available menu keys.
        
        Returns:
            List of menu key strings
        """
        return list(self.menu_data.keys())
    
    def menu_exists(self, menu_key: str) -> bool:
        """
        Check if a menu key exists in the configuration.
        
        Args:
            menu_key: The menu key to check
            
        Returns:
            True if menu exists, False otherwise
        """
        return menu_key in self.menu_data
    
    def get_config_file_path(self) -> str:
        """Get the path to the configuration file being used."""
        return self.config_file
    
    def is_config_loaded(self) -> bool:
        """Check if configuration has been loaded."""
        return bool(self.menu_data)
