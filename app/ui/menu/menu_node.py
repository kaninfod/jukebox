"""
MenuNode represents a single menu item with hierarchical support.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MenuNode:
    """Represents a single menu item with support for nested menus."""
    
    def __init__(self, id: str, name: str, payload: Dict[str, Any] = None, parent: 'MenuNode' = None):
        """
        Initialize a menu node.
        
        Args:
            id: Unique identifier for this menu item
            name: Display name shown in the UI
            payload: Data associated with this menu item (action, parameters, etc.)
            parent: Parent menu node (None for root level)
        """
        self.id = id
        self.name = name
        self.payload = payload or {}
        self.parent = parent
        self.children: List['MenuNode'] = []
        
    def add_child(self, child: 'MenuNode') -> 'MenuNode':
        """Add a child menu item and set its parent."""
        child.parent = self
        self.children.append(child)
        return child
        
    def get_child_by_id(self, id: str) -> Optional['MenuNode']:
        """Find a child by its ID."""
        for child in self.children:
            if child.id == id:
                return child
        return None
        
    def is_root(self) -> bool:
        """Check if this is a root level menu item."""
        return self.parent is None
        
    def get_depth(self) -> int:
        """Get the depth of this node in the menu hierarchy."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
        
    def get_breadcrumb_path(self) -> List[str]:
        """Get the breadcrumb path from root to this node."""
        path = []
        current = self
        while current:
            path.append(current.name)
            current = current.parent
        return list(reversed(path))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MenuNode to dictionary format for compatibility."""
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload
        }
        
    def __repr__(self) -> str:
        return f"MenuNode(id='{self.id}', name='{self.name}', children={len(self.children)})"
