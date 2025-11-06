"""
Menu Data Service - Pure data layer for menu hierarchy and navigation.
Handles menu data access without UI state or event management.

Uses the new MenuBuilder + MenuNode tree architecture:
- MenuBuilder: Loads JSON config and builds MenuNode tree
- MenuNode: Hierarchical menu structure
- MenuEventProcessor: Extracts actions from nodes
"""

import logging
from typing import Optional, List
from .menu_builder import initialize_menu_tree
from .menu_node import MenuNode

logger = logging.getLogger(__name__)


class MenuDataService:
    """
    Pure data service for menu hierarchy management.
    Handles menu navigation and data access without UI state.
    
    Uses MenuNode tree from MenuBuilder instead of dicts.
    All menu structure (static + dynamic) represented as MenuNode instances.
    """
    
    def __init__(self):
        """Initialize the menu data service."""
        self.root_node = initialize_menu_tree()
        self.current_node = self.root_node
        self.node_history = []  # Stack for back navigation
        
        logger.info("MenuDataService initialized")
        
    def get_current_menu_items(self) -> List[MenuNode]:
        """
        Get items (children) of the current menu as MenuNode objects.
        
        Returns:
            List of MenuNode instances that are children of current node.
        """
        if not self.current_node:
            return []
        
        return self.current_node.children
    
    def navigate_to_node(self, node: MenuNode) -> bool:
        """
        Navigate to a specific MenuNode.
        
        Args:
            node: The MenuNode to navigate to.
            
        Returns:
            True if navigation was successful.
        """
        if not node:
            logger.warning("Cannot navigate to None node")
            return False
        
        self.node_history.append(self.current_node)
        self.current_node = node
        logger.info(f"Navigated to node: {node.id}")
        return True
    
    def go_back(self) -> bool:
        """
        Go back to the previous menu node.
        
        Returns:
            True if we went back, False if already at root.
        """
        if self.node_history:
            self.current_node = self.node_history.pop()
            logger.info(f"Went back to node: {self.current_node.id}")
            return True
        else:
            logger.info("Already at root level, cannot go back")
            return False
    
    def reset_to_root(self):
        """Reset menu navigation to root level."""
        self.current_node = self.root_node
        self.node_history.clear()
        logger.info("Reset to root menu level")
    
    def get_current_node(self) -> Optional[MenuNode]:
        """
        Get the current MenuNode.
        
        Returns:
            The current MenuNode.
        """
        return self.current_node
    
    def get_breadcrumb_path(self) -> List[str]:
        """
        Get the breadcrumb path for the current menu location.
        
        Returns:
            List of menu names from root to current.
        """
        # Start from root, follow history, end with current
        path = ["Root"]
        
        # Add history items
        for node in self.node_history:
            if node and node.id != "root":
                path.append(node.name)
        
        # Add current if not root
        if self.current_node and self.current_node.id != "root":
            path.append(self.current_node.name)
        
        return path
    
    def get_menu_count(self) -> int:
        """Get the number of items (children) in the current menu."""
        return len(self.current_node.children) if self.current_node else 0
