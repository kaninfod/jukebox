"""
MenuBuilder: Constructs the global MenuNode tree from static JSON configuration.

This class is responsible for:
1. Loading static menu structure from menu_config.json
2. Creating MenuNode instances for each menu item
3. Building the hierarchical tree structure
4. Integrating with dynamic content loaders (e.g., DynamicLoader for Subsonic data)

The result is a single global MenuNode tree that represents all available navigation paths,
both static (from JSON) and dynamic (from API calls).

Architecture:
- Static content (structure, groups) → JSON configuration file
- Dynamic content (artists, albums) → Loaded at runtime via DynamicLoader
- MenuBuilder → Orchestrates loading both into one tree
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any

from .menu_node import MenuNode


class MenuBuilder:
    """Builds the global MenuNode tree from configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MenuBuilder.

        Args:
            config_path: Path to menu_config.json. If None, uses default location.
        """
        if config_path is None:
            # Default location: app/config/menu_config.json
            config_path = Path(__file__).parent.parent.parent / "config" / "menu_config.json"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.root_node: Optional[MenuNode] = None
        self._nodes_by_id: Dict[str, MenuNode] = {}  # For fast lookup

    def load_config(self) -> Dict[str, Any]:
        """
        Load menu configuration from JSON file.

        Returns:
            Dictionary containing the menu configuration.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config JSON is invalid.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Menu config not found at {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        return self.config

    def build_tree(self) -> MenuNode:
        """
        Build the complete MenuNode tree.

        This method:
        1. Loads the JSON configuration
        2. Creates MenuNode instances from root items
        3. Recursively builds submenu items
        4. Ensures all referenced sections are populated
        5. Stores the tree globally

        Returns:
            The root MenuNode of the tree.

        Raises:
            ValueError: If configuration structure is invalid.
        """
        # Load configuration if not already loaded
        if not self.config:
            self.load_config()

        # Create root node
        self.root_node = MenuNode(
            id="root",
            name="Root",
            parent=None
        )
        self._nodes_by_id["root"] = self.root_node

        # Build tree from root config
        if "root" in self.config:
            self._build_menu_items(self.root_node, self.config["root"])

        # Final pass: Ensure all referenced sections are populated
        # Look for sections that are referenced but may not have been built
        for section_id, section_config in self.config.items():
            if section_id != "root" and isinstance(section_config, dict) and "items" in section_config:
                # Check if this section was referenced and built
                if section_id not in self._nodes_by_id:
                    # Section exists but was never created - create it now with no parent
                    # (it might be referenced dynamically)
                    section_node = MenuNode(
                        id=section_id,
                        name=section_config.get("name", section_id),
                        parent=None
                    )
                    self._nodes_by_id[section_id] = section_node
                    self._build_menu_items(section_node, section_config)

        return self.root_node

    def _build_menu_items(self, parent_node: MenuNode, config_section: Dict[str, Any]) -> None:
        """
        Recursively build menu items from configuration.

        Args:
            parent_node: The parent MenuNode to add items to.
            config_section: Dictionary containing menu configuration for this section.
        """
        for key, value in config_section.items():
            if key == "items" and isinstance(value, list):
                # Process items list
                for item_config in value:
                    self._create_node_from_config(item_config, parent_node)

    def _create_node_from_config(self, item_config: Dict[str, Any], parent_node: MenuNode) -> MenuNode:
        """
        Create a MenuNode from configuration dictionary.

        Args:
            item_config: Dictionary with 'id', 'name', optional 'payload'.
            parent_node: The parent MenuNode.

        Returns:
            The created MenuNode.

        Raises:
            ValueError: If item_config is missing required fields.
        """
        if not isinstance(item_config, dict):
            raise ValueError(f"Item config must be a dict, got {type(item_config)}")

        item_id = item_config.get("id")
        item_name = item_config.get("name")

        if not item_id or not item_name:
            raise ValueError(f"Item must have 'id' and 'name': {item_config}")

        # Check if this item references another menu section via "target"
        target = None
        if item_config.get("payload") and isinstance(item_config["payload"], dict):
            target = item_config["payload"].get("target")
        
        
        # Create the node
        node = MenuNode(
            id=item_id,
            name=item_name,
            parent=parent_node,
            payload=item_config.get("payload")
        )
        parent_node.add_child(node)
        self._nodes_by_id[item_id] = node
        
        # If this item references a submenu section, build its items into this node
        if target and target in self.config:
            target_config = self.config[target]
            self._build_menu_items(node, target_config)
        
        return node

    def get_node_by_id(self, node_id: str) -> Optional[MenuNode]:
        """
        Get a node by its ID for fast lookup.

        Args:
            node_id: The node ID to search for.

        Returns:
            The MenuNode if found, None otherwise.
        """
        return self._nodes_by_id.get(node_id)

    def add_dynamic_nodes(self, parent_id: str, dynamic_nodes: list) -> None:
        """
        Add dynamically-generated nodes to a parent node.

        This is used for content loaded from APIs (e.g., artists from Subsonic).

        Args:
            parent_id: ID of the parent node to add to.
            dynamic_nodes: List of MenuNode instances to add as children.

        Raises:
            ValueError: If parent node not found.
        """
        parent_node = self.get_node_by_id(parent_id)
        if not parent_node:
            raise ValueError(f"Parent node not found: {parent_id}")

        for node in dynamic_nodes:
            parent_node.add_child(node)
            self._nodes_by_id[node.id] = node

    def get_root(self) -> Optional[MenuNode]:
        """Get the root node of the tree."""
        return self.root_node

    def reset(self) -> None:
        """Reset the builder for rebuilding the tree."""
        self.root_node = None
        self._nodes_by_id = {}
        self.config = {}


# Global instance
_menu_builder_instance: Optional[MenuBuilder] = None


def get_menu_builder() -> MenuBuilder:
    """
    Get or create the global MenuBuilder instance.

    Returns:
        The singleton MenuBuilder instance.
    """
    global _menu_builder_instance
    if _menu_builder_instance is None:
        _menu_builder_instance = MenuBuilder()
    return _menu_builder_instance


def initialize_menu_tree() -> MenuNode:
    """
    Initialize the global menu tree.

    Call this once at application startup to build the menu structure.

    Returns:
        The root MenuNode of the tree.

    Raises:
        FileNotFoundError: If config file not found.
        json.JSONDecodeError: If config JSON is invalid.
        ValueError: If configuration structure is invalid.
    """
    builder = get_menu_builder()
    return builder.build_tree()


def get_menu_root() -> Optional[MenuNode]:
    """
    Get the root of the menu tree.

    Returns:
        The root MenuNode if tree has been initialized, None otherwise.
    """
    builder = get_menu_builder()
    return builder.get_root()


def find_menu_node(node_id: str) -> Optional[MenuNode]:
    """
    Find a menu node by ID in the global tree.

    Args:
        node_id: The node ID to search for.

    Returns:
        The MenuNode if found, None otherwise.
    """
    builder = get_menu_builder()
    return builder.get_node_by_id(node_id)
