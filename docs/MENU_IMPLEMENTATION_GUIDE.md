# Menu Refactoring: Implementation Guide

## Overview

This guide provides step-by-step instructions to refactor the menu architecture from mixed dict/MenuNode to a unified MenuNode tree structure.

---

## Phase 1: Create New Components (No Breaking Changes)

### Step 1.1: Enhance MenuNode

Add helper methods to MenuNode to support tree operations better:

```python
# In app/ui/menu/menu_node.py

def find_by_id(self, node_id: str) -> Optional['MenuNode']:
    """Search entire subtree for node by ID."""
    if self.id == node_id:
        return self
    for child in self.children:
        result = child.find_by_id(node_id)
        if result:
            return result
    return None

def get_path_to_root(self) -> List['MenuNode']:
    """Get path from this node to root."""
    path = [self]
    current = self.parent
    while current:
        path.append(current)
        current = current.parent
    return list(reversed(path))

def get_all_descendants(self) -> List['MenuNode']:
    """Get all nodes in subtree."""
    descendants = []
    for child in self.children:
        descendants.append(child)
        descendants.extend(child.get_all_descendants())
    return descendants

def clear_children(self) -> None:
    """Remove all children."""
    self.children.clear()
```

### Step 1.2: Create MenuNodeNavigator

**File:** `app/ui/menu/menu_node_navigator.py`

**Key Change:** This is now much simpler because ALL structure comes from JSON!

```python
"""
MenuNodeNavigator - Navigate and query the MenuNode tree.
"""

from typing import Optional, List
from .menu_node import MenuNode
import logging

logger = logging.getLogger(__name__)


class MenuNodeNavigator:
    """Navigate a MenuNode tree and provide query capabilities."""
    
    def __init__(self, root: MenuNode):
        """
        Initialize the navigator with a root node.
        
        Args:
            root: The root MenuNode of the tree (built from JSON)
        """
        self.root = root
        self.current_node = root
        self.navigation_history: List[MenuNode] = []
    
    def navigate_to_child(self, child_id: str) -> bool:
        """
        Navigate to a child of the current node by ID.
        
        Args:
            child_id: The ID of the child to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        child = self.current_node.get_child_by_id(child_id)
        if child:
            return self.navigate_to_node(child)
        return False
    
    def navigate_to_node(self, node: MenuNode) -> bool:
        """
        Navigate directly to a specific node.
        
        Args:
            node: The MenuNode to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        if node not in self.current_node.children:
            logger.warning(f"Cannot navigate to {node.id}: not a child of current node")
            return False
        
        self.navigation_history.append(self.current_node)
        self.current_node = node
        logger.info(f"Navigated to: {self.current_node.id} ({self.current_node.name})")
        return True
    
    def go_back(self) -> bool:
        """
        Navigate back to the previous node.
        
        Returns:
            True if we went back, False if already at root
        """
        if self.navigation_history:
            self.current_node = self.navigation_history.pop()
            logger.info(f"Navigated back to: {self.current_node.id}")
            return True
        return False
    
    def reset_to_root(self) -> None:
        """Reset to the root node."""
        self.current_node = self.root
        self.navigation_history.clear()
        logger.info("Reset to root node")
    
    def get_current_node(self) -> MenuNode:
        """Get the current node."""
        return self.current_node
    
    def get_current_children(self) -> List[MenuNode]:
        """Get children of the current node."""
        return self.current_node.children.copy()
    
    def get_breadcrumb_path(self) -> List[MenuNode]:
        """Get path from root to current node."""
        path = [self.root]
        path.extend(self.navigation_history)
        return path
    
    def get_breadcrumb_names(self) -> List[str]:
        """Get breadcrumb path as display names."""
        return [node.name for node in self.get_breadcrumb_path()]
    
    def find_node_by_id(self, node_id: str) -> Optional[MenuNode]:
        """
        Find a node anywhere in the tree by ID.
        
        Args:
            node_id: The ID to search for
            
        Returns:
            The MenuNode if found, None otherwise
        """
        return self.root.find_by_id(node_id)
    
    def is_at_root(self) -> bool:
        """Check if currently at root."""
        return self.current_node == self.root
```

### Step 1.3: Create MenuBuilder

**File:** `app/ui/menu/menu_builder.py`

**Key Point:** NOW MUCH SIMPLER! Just load JSON and build tree. No special logic needed because ALL structure is in JSON!

```python
"""
MenuBuilder - Constructs the global MenuNode tree from JSON configuration.
"""

import json
import os
from typing import Dict, Any, Optional, List
from .menu_node import MenuNode
import logging

logger = logging.getLogger(__name__)


class MenuBuilder:
    """Builds the global MenuNode tree from JSON configuration."""
    
    def __init__(self):
        """Initialize the builder."""
        self.root = MenuNode(id="root", name="Root", payload={})
        self._config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "menu_config.json"
        )
    
    def load_static_menus(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load entire menu structure from JSON.
        
        This is the KEY insight: ALL structure (including artist groups,
        devices, etc.) is in JSON. No special logic needed!
        
        Args:
            config_data: Dict with menu structure. If None, loads from JSON file.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_data is None:
                with open(self._config_path, 'r') as f:
                    config_data = json.load(f)
            
            self.root.clear_children()
            
            # Simple recursive build from JSON
            self._build_from_json(self.root, config_data)
            
            logger.info(f"Loaded menu structure from JSON: {len(self.root.children)} items")
            return True
            
        except FileNotFoundError:
            logger.error(f"Menu config file not found: {self._config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading menus: {e}")
            return False
    
    def _build_from_json(self, parent: MenuNode, config_data: Dict) -> None:
        """
        Recursively build MenuNode tree from JSON.
        
        Looks for a section in config_data matching the parent's target reference.
        Simple and clean - no special cases!
        """
        if not parent.id:
            return
        
        # Try to find menu section for this node
        menu_section = config_data.get(parent.id)
        if not menu_section:
            return
        
        items = menu_section.get("items", [])
        for item_config in items:
            # Create node from config
            node = MenuNode(
                id=item_config.get("id"),
                name=item_config.get("name"),
                payload=item_config.get("payload", {}),
                parent=parent
            )
            parent.add_child(node)
            
            # Recursively build children
            # The JSON section name matches the node id
            self._build_from_json(node, config_data)
    
    def add_dynamic_children(self, parent_id: str, children: List[MenuNode]) -> bool:
        """
        Add dynamically-loaded children to a node.
        
        Called at runtime when user navigates to a node that has
        load_dynamic action in its payload.
        
        Args:
            parent_id: The ID of the parent node
            children: List of MenuNode children (from API)
            
        Returns:
            True if successful
        """
        parent = self.root.find_by_id(parent_id)
        if not parent:
            logger.warning(f"Parent not found: {parent_id}")
            return False
        
        for child in children:
            child.parent = parent
            parent.add_child(child)
        
        logger.info(f"Added {len(children)} dynamic children to {parent_id}")
        return True
    
    def get_root(self) -> MenuNode:
        """Get root node of the tree."""
        return self.root
    
    def validate(self) -> bool:
        """Validate tree structure."""
        if not self.root.children:
            logger.warning("Root has no children")
            return False
        logger.info(f"Tree valid: {len(self.root.children)} top-level items")
        return True
```

### Step 1.4: Create MenuEventProcessor

**File:** `app/ui/menu/menu_event_processor.py`

```python
"""
MenuEventProcessor - Extract actions from MenuNodes and raise events.
"""

from typing import Dict, Any
from .menu_node import MenuNode
from app.core import event_bus, Event, EventType
import logging

logger = logging.getLogger(__name__)


class MenuEventProcessor:
    """Process MenuNode selections and raise appropriate events."""
    
    def __init__(self):
        """Initialize the processor."""
        pass
    
    def process_node_selection(self, node: MenuNode) -> bool:
        """
        Process selection of a menu node.
        Extract payload and raise corresponding event.
        
        Args:
            node: The selected MenuNode
            
        Returns:
            True if event was processed, False if unable to handle
        """
        if not node.payload:
            logger.warning(f"Node {node.id} has no payload")
            return False
        
        action = node.payload.get("action")
        if not action:
            logger.warning(f"Node {node.id} payload has no action")
            return False
        
        logger.info(f"Processing node selection: {node.id}, action: {action}")
        
        # Dispatch based on action type
        if action == "load_submenu":
            return self._handle_load_submenu(node)
        elif action == "load_dynamic_menu":
            return self._handle_load_dynamic_menu(node)
        elif action == "select_chromecast_device":
            return self._handle_chromecast_selection(node)
        elif action == "browse_artists_in_range":
            return self._handle_browse_artists_in_range(node)
        elif action == "browse_artist_albums":
            return self._handle_browse_artist_albums(node)
        elif action == "play_album":
            return self._handle_play_album(node)
        elif action == "browse_albums":
            return self._handle_browse_albums(node)
        else:
            logger.warning(f"Unknown action: {action}")
            return False
    
    def _handle_load_submenu(self, node: MenuNode) -> bool:
        """Handle submenu loading."""
        # This is handled by navigation now, just emit navigation event
        event_bus.emit(Event(
            type=EventType.MENU_NAVIGATE,
            payload={"node_id": node.id, "node_name": node.name}
        ))
        return True
    
    def _handle_load_dynamic_menu(self, node: MenuNode) -> bool:
        """Handle dynamic menu loading."""
        menu_type = node.payload.get("menu_type")
        if not menu_type:
            return False
        
        event_bus.emit(Event(
            type=EventType.MENU_LOAD_DYNAMIC,
            payload={"node_id": node.id, "menu_type": menu_type}
        ))
        return True
    
    def _handle_chromecast_selection(self, node: MenuNode) -> bool:
        """Handle chromecast device selection."""
        device_name = node.payload.get("device_name")
        device_id = node.payload.get("device_id")
        
        if not device_id:
            return False
        
        event_bus.emit(Event(
            type=EventType.CHROMECAST_SELECTED,
            payload={"device_id": device_id, "device_name": device_name}
        ))
        return True
    
    def _handle_browse_artists_in_range(self, node: MenuNode) -> bool:
        """Handle browsing artists in alphabetical range."""
        start_letter = node.payload.get("start_letter")
        end_letter = node.payload.get("end_letter")
        
        event_bus.emit(Event(
            type=EventType.MENU_BROWSE_ARTISTS,
            payload={
                "node_id": node.id,
                "start_letter": start_letter,
                "end_letter": end_letter
            }
        ))
        return True
    
    def _handle_browse_artist_albums(self, node: MenuNode) -> bool:
        """Handle browsing albums by an artist."""
        artist_id = node.payload.get("artist_id")
        
        event_bus.emit(Event(
            type=EventType.MENU_BROWSE_ALBUMS,
            payload={"node_id": node.id, "artist_id": artist_id}
        ))
        return True
    
    def _handle_play_album(self, node: MenuNode) -> bool:
        """Handle album playback."""
        album_id = node.payload.get("album_id")
        
        if not album_id:
            return False
        
        event_bus.emit(Event(
            type=EventType.PLAY_ALBUM,
            payload={"album_id": album_id, "album_name": node.name}
        ))
        return True
    
    def _handle_browse_albums(self, node: MenuNode) -> bool:
        """Handle browsing all albums."""
        event_bus.emit(Event(
            type=EventType.MENU_BROWSE_ALL_ALBUMS,
            payload={"node_id": node.id}
        ))
        return True
```

---

## Phase 2: Update MenuDataService

Refactor to use the new components while maintaining backward compatibility:

**File:** `app/ui/menu/menu_data_service.py` (Refactored)

```python
"""
Menu Data Service - Refactored to use MenuNode tree architecture.
"""

import logging
from typing import Optional, List, Dict, Any
from .menu_builder import MenuBuilder
from .menu_node_navigator import MenuNodeNavigator
from .menu_event_processor import MenuEventProcessor
from .menu_node import MenuNode
from app.services.subsonic_service import SubsonicService
import logging

logger = logging.getLogger(__name__)


class MenuDataService:
    """
    Pure data service for menu hierarchy management using MenuNode tree.
    Single source of truth for all menu data (static + dynamic).
    """
    
    def __init__(self):
        """Initialize the menu data service."""
        self.builder = MenuBuilder()
        self.navigator: Optional[MenuNodeNavigator] = None
        self.processor = MenuEventProcessor()
        
        # For dynamic menu loading
        self.subsonic_service: Optional[SubsonicService] = None
        
        # Initialize on first access
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the menu system with all data.
        Must be called before other methods.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load static menus
            if not self.builder.load_static_menus():
                logger.error("Failed to load static menus")
                return False
            
            # Initialize navigator
            self.navigator = MenuNodeNavigator(self.builder.get_root())
            
            # Load dynamic data (if Subsonic available)
            try:
                self.subsonic_service = SubsonicService()
                self._setup_dynamic_menus()
            except Exception as e:
                logger.warning(f"Dynamic menus not available: {e}")
                self.subsonic_service = None
            
            self._initialized = True
            logger.info("MenuDataService initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MenuDataService: {e}")
            return False
    
    def _setup_dynamic_menus(self) -> None:
        """Set up dynamic menu generators for Subsonic data."""
        if not self.subsonic_service:
            return
        
        # Get Artists menu node
        artists_node = self.builder.get_root().find_by_id("artists")
        if artists_node:
            # Attach generator for artist groups
            self.builder.attach_dynamic_generator(
                "artists",
                self._generate_artist_groups
            )
    
    def _generate_artist_groups(self) -> List[MenuNode]:
        """Generate artist group MenuNodes from Subsonic data."""
        if not self.subsonic_service:
            return []
        
        try:
            groups = self.subsonic_service.get_alphabetical_groups()
            nodes = []
            
            for group in groups:
                node = MenuNode(
                    id=f"artist_group_{group['name'].lower().replace('-', '_')}",
                    name=group["name"],
                    payload={
                        "action": "browse_artists_in_range",
                        "start_letter": group["range"][0],
                        "end_letter": group["range"][1]
                    }
                )
                nodes.append(node)
            
            return nodes
        except Exception as e:
            logger.error(f"Failed to generate artist groups: {e}")
            return []
    
    # ===== New Tree-Based API (Primary) =====
    
    def get_navigator(self) -> MenuNodeNavigator:
        """Get the navigator for menu traversal."""
        if not self._initialized:
            self.initialize()
        return self.navigator
    
    def get_current_node(self) -> MenuNode:
        """Get the current menu node."""
        return self.get_navigator().get_current_node()
    
    def get_current_children(self) -> List[MenuNode]:
        """
        Get children of the current node as MenuNodes.
        (Type-safe, no conversion needed)
        """
        return self.get_navigator().get_current_children()
    
    def navigate_to_child(self, child_id: str) -> bool:
        """Navigate to a child by ID."""
        return self.get_navigator().navigate_to_child(child_id)
    
    def navigate_to_node(self, node: MenuNode) -> bool:
        """Navigate to a specific node."""
        return self.get_navigator().navigate_to_node(node)
    
    def go_back(self) -> bool:
        """Go back to previous menu."""
        return self.get_navigator().go_back()
    
    def reset_to_root(self) -> None:
        """Reset to root menu."""
        self.get_navigator().reset_to_root()
    
    def get_breadcrumb_path(self) -> List[str]:
        """Get breadcrumb path as display names."""
        return self.get_navigator().get_breadcrumb_names()
    
    def find_node_by_id(self, node_id: str) -> Optional[MenuNode]:
        """Find a node anywhere in the tree."""
        return self.get_navigator().find_node_by_id(node_id)
    
    def process_node_selection(self, node: MenuNode) -> bool:
        """Process selection of a menu node and raise event."""
        return self.processor.process_node_selection(node)
    
    # ===== Backward Compatibility API (to be phased out) =====
    
    def get_current_menu_items(self) -> List[Dict[str, Any]]:
        """
        Get items as dicts for UI rendering (backward compatibility).
        Deprecated: Use get_current_children() instead.
        """
        nodes = self.get_current_children()
        return [node.to_dict() for node in nodes]
    
    def get_menu_count(self) -> int:
        """Get number of items in current menu."""
        return len(self.get_current_children())
    
    def get_menu_item_at_index(self, index: int) -> Optional[MenuNode]:
        """Get menu item at index."""
        children = self.get_current_children()
        if 0 <= index < len(children):
            return children[index]
        return None
```

---

## Phase 3: Update MenuController

Gradually migrate MenuController to use the new API:

```python
# Key changes in app/ui/menu/menu_controller.py

def __init__(self):
    self.menu_data = MenuDataService()
    self.menu_data.initialize()  # Now we initialize explicitly
    
    self.navigator = self.menu_data.get_navigator()
    self.processor = self.menu_data.processor

def _load_current_menu_items(self):
    """Load menu items - now returns MenuNodes."""
    self.all_menu_items = self.menu_data.get_current_children()
    logger.info(f"Loaded {len(self.all_menu_items)} menu items")

def handle_item_selection(self, selected_item: MenuNode):
    """Handle selection - now accepts MenuNode directly."""
    # Navigate to selected item
    if self.menu_data.navigate_to_child(selected_item.id):
        # Process action and raise event
        self.menu_data.process_node_selection(selected_item)
        
        # Reload menu items for display
        self._load_current_menu_items()
        self._emit_menu_screen_update()
        return True
    
    return False
```

---

## Summary of Files to Create/Modify

| File | Action | Status |
|------|--------|--------|
| `app/ui/menu/menu_node.py` | Enhance with tree methods | Phase 1 |
| `app/ui/menu/menu_node_navigator.py` | Create new | Phase 1 |
| `app/ui/menu/menu_builder.py` | Create new | Phase 1 |
| `app/ui/menu/menu_event_processor.py` | Create new | Phase 1 |
| `app/ui/menu/menu_data_service.py` | Refactor | Phase 2 |
| `app/ui/menu/menu_controller.py` | Update | Phase 3 |
| `app/ui/menu/json_menu_adapter.py` | Keep (internal use) | Phase 4 |
| `app/ui/menu/subsonic_config_adapter.py` | Remove/integrate | Phase 4 |

---

## Testing Strategy

### Unit Tests

```python
# tests/test_menu_builder.py
def test_load_static_menus():
    builder = MenuBuilder()
    assert builder.load_static_menus()
    assert builder.root.children
    assert builder.root.find_by_id("music")

def test_add_dynamic_children():
    builder = MenuBuilder()
    builder.load_static_menus()
    
    new_children = [MenuNode("test1", "Test 1"), MenuNode("test2", "Test 2")]
    assert builder.add_dynamic_children("music", new_children)

# tests/test_menu_navigator.py
def test_navigate_to_child():
    tree = build_test_tree()
    nav = MenuNodeNavigator(tree.root)
    
    assert nav.navigate_to_child("music")
    assert nav.current_node.id == "music"
    assert nav.navigate_to_child("artists")
    assert nav.current_node.id == "artists"

def test_go_back():
    tree = build_test_tree()
    nav = MenuNodeNavigator(tree.root)
    
    nav.navigate_to_child("music")
    nav.navigate_to_child("artists")
    assert nav.go_back()
    assert nav.current_node.id == "music"

# tests/test_menu_event_processor.py
def test_process_node_selection():
    processor = MenuEventProcessor()
    node = MenuNode("test", "Test", payload={"action": "play_album", "album_id": "123"})
    
    assert processor.process_node_selection(node)
```

---

## Rollout Checklist

- [ ] **Phase 1: New Components**
  - [ ] Enhance MenuNode with tree methods
  - [ ] Create MenuNodeNavigator
  - [ ] Create MenuBuilder
  - [ ] Create MenuEventProcessor
  - [ ] Write unit tests for all new components
  - [ ] No changes to existing code yet

- [ ] **Phase 2: Update MenuDataService**
  - [ ] Add new tree-based methods
  - [ ] Implement initialize() method
  - [ ] Keep backward compatibility methods
  - [ ] Update MenuDataService tests
  - [ ] Verify existing code still works

- [ ] **Phase 3: Update MenuController**
  - [ ] Update to use new navigator API
  - [ ] Use MenuEventProcessor for actions
  - [ ] Simplify navigation logic
  - [ ] Update MenuController tests

- [ ] **Phase 4: Cleanup**
  - [ ] Remove backward compatibility methods
  - [ ] Remove unused adapters
  - [ ] Remove type conversion code
  - [ ] Update documentation
  - [ ] Final testing

---

## Rollback Plan

If issues arise:
1. Keep old `menu_data_service.py` in version control
2. Maintain backward compatibility layer until Phase 4
3. New components are side-by-side, can be disabled
4. Test thoroughly before each phase transition

