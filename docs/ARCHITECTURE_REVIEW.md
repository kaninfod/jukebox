# Menu Architecture Review and Refactoring Plan

## Current State Analysis

### Issues with Current Architecture

#### 1. **Inconsistent Data Representation**
- **Problem**: Menu items exist in multiple formats simultaneously
  - Dict format in JSON files and cached dynamic menus
  - MenuNode objects from SubsonicConfigAdapter
  - Converts between them using `hasattr(items[0], 'to_dict')` checks
  
- **Impact**: 
  - Runtime type checking instead of compile-time safety
  - Conversion logic scattered throughout code
  - Difficult to maintain and extend

```python
# Current problematic pattern in menu_data_service.py:60-64
def get_current_menu_items(self) -> List[Dict[str, Any]]:
    items = current_menu.get("items", [])
    
    # Convert MenuNode objects to dict format if needed
    if items and hasattr(items[0], 'to_dict'):
        items = [item.to_dict() for item in items]
    
    return items
```

#### 2. **No Global Menu Structure**
- **Problem**: Menu is managed at two separate levels
  - Static menus stored as dicts in JSON config
  - Dynamic menus created on-demand as separate MenuNode lists
  - No unified tree representation
  
- **Current Flow**:
  ```
  MenuController → MenuDataService → JsonMenuAdapter (dicts)
                                 ↘ SubsonicConfigAdapter (lists of MenuNodes)
  ```

- **Impact**: 
  - Can't navigate a consistent tree
  - Navigation history managed with string identifiers
  - Dynamic content not integrated into permanent structure

#### 3. **Navigation Complexity**
- **Current implementation**:
  - Tracks current level by string identifier (`current_menu_level`)
  - Uses navigation history stack for breadcrumbs
  - Reloads data on each navigation
  - Different loading logic for static vs dynamic

```python
# Current pattern - duplicated logic for different menu types
def navigate_to_menu(self, menu_level: str) -> bool:
    if self.json_config.menu_exists(menu_level):  # Only checks static
        self.menu_history.append(self.current_menu_level)
        self.current_menu_level = menu_level
        return True
    return False
```

#### 4. **Load vs Navigate Inconsistency**
- Static menus use `navigate_to_menu()`
- Dynamic menus use `load_dynamic_menu()` with completely different logic
- Event emission logic mixed with data loading
- No clear separation of concerns

#### 5. **Limited Extensibility**
- Hard to add new menu types
- Dynamic menu caching with generated IDs (`dynamic_menu_type_param1_param2...`)
- No structured menu composition

---

## Proposed Clean Architecture

### Core Principle
**One global MenuNode tree containing all menu data (static + dynamic), processed on-demand to extract events.**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Global MenuNode Tree                     │
│  (Single Source of Truth - static + dynamic integrated)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┬───────────────────┐
        ↓                   ↓                   ↓
   MenuBuilder         NavigationService    MenuEventProcessor
   (Build tree)        (Navigate tree)      (Extract actions)
        ↓                   ↓                   ↓
  • Load JSON         • Find nodes          • Process payloads
  • Load dynamic      • Get children        • Raise events
  • Integrate         • Get path            • Execute actions
```

### Key Components

#### 1. **MenuBuilder** (New)
Responsible for constructing and maintaining the global MenuNode tree.

```python
class MenuBuilder:
    """Builds and maintains the global MenuNode tree."""
    
    def __init__(self):
        self.root: MenuNode = MenuNode(id="root", name="Root")
        
    def load_static_menus(self, config_data: Dict) -> None:
        """Load all static menu structure from JSON."""
        # Build tree from JSON
        
    def add_dynamic_menu(self, parent_id: str, dynamic_data: List[MenuNode]) -> None:
        """Add dynamic content as children of a parent node."""
        # Integrate dynamic content
        
    def rebuild(self, config_data: Dict = None) -> None:
        """Rebuild tree (useful for config changes)."""
        # Clear and rebuild
        
    def get_root(self) -> MenuNode:
        """Get the root node of the tree."""
```

#### 2. **MenuNodeNavigator** (Enhanced from MenuDataService)
Handles navigation within the MenuNode tree.

```python
class MenuNodeNavigator:
    """Navigates the MenuNode tree and provides query capabilities."""
    
    def __init__(self, root: MenuNode):
        self.root = root
        self.current_node: MenuNode = root
        self.navigation_history: List[MenuNode] = []
        
    def navigate_to_child(self, child_id: str) -> bool:
        """Navigate to a child node by ID."""
        
    def navigate_to_node(self, node: MenuNode) -> bool:
        """Navigate to a specific node."""
        
    def go_back(self) -> bool:
        """Go back one level."""
        
    def get_current_node(self) -> MenuNode:
        """Get current node."""
        
    def get_current_children(self) -> List[MenuNode]:
        """Get children of current node."""
        
    def get_breadcrumb_path(self) -> List[MenuNode]:
        """Get path from root to current node."""
        
    def find_node_by_id(self, node_id: str, search_root: MenuNode = None) -> Optional[MenuNode]:
        """Find a node by ID (tree search)."""
```

#### 3. **MenuEventProcessor** (New)
Extracts and processes menu actions into events.

```python
class MenuEventProcessor:
    """Processes MenuNode payloads and raises appropriate events."""
    
    def process_node_selection(self, node: MenuNode) -> bool:
        """
        Process selection of a menu node.
        Extract payload and raise corresponding event.
        """
        # Determine action from payload
        # Emit appropriate EventBus event
        # Return success
```

#### 4. **MenuDataService** (Refactored)
Pure data layer without navigation state.

```python
class MenuDataService:
    """Pure data layer for menu hierarchy."""
    
    def __init__(self):
        self.builder = MenuBuilder()
        self.navigator = MenuNodeNavigator(self.builder.root)
        
    def initialize(self) -> None:
        """Load all static and dynamic menu data."""
        config_data = self._load_json_config()
        self.builder.load_static_menus(config_data)
        self.builder.add_dynamic_menu("music", self._load_artists_menu())
        
    def get_navigator(self) -> MenuNodeNavigator:
        """Get navigator for current menu interaction."""
        return self.navigator
    
    def get_current_node(self) -> MenuNode:
        """Get current menu node."""
        return self.navigator.current_node
    
    def get_current_children_as_dicts(self) -> List[Dict[str, Any]]:
        """Get current children as dicts for UI rendering."""
        return [child.to_dict() for child in self.navigator.get_current_children()]
```

---

## Migration Path

### Phase 1: Build New Components (Side-by-side)
1. Create `MenuBuilder` to load JSON and construct tree
2. Create `MenuNodeNavigator` with tree query capabilities
3. Create `MenuEventProcessor` for action handling
4. Keep existing code working (no breaking changes)

### Phase 2: Update MenuDataService
1. Add new methods that use MenuBuilder/Navigator
2. Keep old methods for compatibility
3. Update MenuController to use new methods

### Phase 3: Update MenuController
1. Change to use new `MenuNodeNavigator` API
2. Update event emission to use `MenuEventProcessor`
3. Update data access methods

### Phase 4: Cleanup
1. Remove conversion logic (no more `to_dict` checks)
2. Remove JsonMenuAdapter or keep as internal utility
3. Remove SubsonicConfigAdapter or integrate into MenuBuilder
4. Update tests to use new API

---

## Benefits of New Architecture

### 1. **Consistency**
- ✅ All menu items are MenuNodes throughout the system
- ✅ No type conversion logic scattered around
- ✅ Compile-time type safety

### 2. **Simplicity**
- ✅ Single navigation API (navigate to any node in tree)
- ✅ Consistent method for static and dynamic menus
- ✅ Natural parent-child relationships

### 3. **Extensibility**
- ✅ Easy to add new menu types (just add them to tree)
- ✅ Dynamic content integrates naturally
- ✅ New features can traverse the tree as needed

### 4. **Testability**
- ✅ MenuBuilder can be tested independently
- ✅ Navigator can be tested with mock trees
- ✅ EventProcessor can be tested with mock payloads

### 5. **Performance**
- ✅ Single tree built once on init
- ✅ Navigation is simple tree traversal
- ✅ Less memory fragmentation than dict copies

### 6. **Maintainability**
- ✅ Clear separation of concerns
- ✅ Easy to trace data flow
- ✅ Reduced cyclomatic complexity

---

## Implementation Checklist

- [ ] Create `MenuBuilder` class
  - [ ] Load static menus from JSON
  - [ ] Create MenuNode tree structure
  - [ ] Add method to integrate dynamic content
  
- [ ] Create `MenuNodeNavigator` class
  - [ ] Implement tree navigation
  - [ ] Implement node search
  - [ ] Implement breadcrumb generation
  
- [ ] Create `MenuEventProcessor` class
  - [ ] Parse node payloads
  - [ ] Map actions to events
  - [ ] Emit events via EventBus
  
- [ ] Refactor `MenuDataService`
  - [ ] Use MenuBuilder to initialize
  - [ ] Use MenuNodeNavigator for navigation
  - [ ] Maintain backward compatibility during transition
  
- [ ] Update `MenuController`
  - [ ] Use new navigator API
  - [ ] Use MenuEventProcessor for actions
  - [ ] Remove pagination workarounds
  
- [ ] Update tests
  - [ ] Test MenuBuilder tree construction
  - [ ] Test MenuNodeNavigator traversal
  - [ ] Test MenuEventProcessor actions
  
- [ ] Cleanup
  - [ ] Remove JsonMenuAdapter (or keep as internal utility)
  - [ ] Remove SubsonicConfigAdapter integration code
  - [ ] Remove type conversion checks
  - [ ] Update documentation

---

## Code Examples

### Current (Problematic) Pattern
```python
# Mixing dicts and MenuNodes with runtime checks
items = self.menu_data.get_current_menu_items()
if items and hasattr(items[0], 'to_dict'):
    items = [item.to_dict() for item in items]

for item in items:
    # Can't be sure if item is a dict or MenuNode
    display_name = item.get("name")  # Works for dicts
    payload = item.get("payload", {})
```

### Proposed Pattern
```python
# Always MenuNodes, type-safe
children = self.navigator.get_current_children()
for child in children:
    # We know child is a MenuNode
    display_name = child.name
    payload = child.payload
    
    # Process the action
    self.event_processor.process_node_selection(child)
```

### Current Navigation (Problematic)
```python
# String-based navigation with separate logic paths
if self.json_config.menu_exists(menu_level):
    # Static menu
    self.navigate_to_menu(menu_level)
elif menu_type:
    # Dynamic menu
    self.load_dynamic_menu(menu_type, **params)
```

### Proposed Navigation (Unified)
```python
# Node-based navigation - same code for static and dynamic
child = self.navigator.current_node.get_child_by_id(child_id)
if child:
    self.navigator.navigate_to_node(child)
    return True
return False
```

---

## Questions for Review

1. **Dynamic Menu Timing**: Should dynamic menus be pre-loaded on init or loaded on-demand when navigating to them?
   - Current: On-demand
   - Proposed: Pre-load on init for consistency
   
2. **Caching Strategy**: Should we cache dynamic results?
   - Current: Yes (in `_dynamic_menus` dict)
   - Proposed: Keep cached in MenuNode tree
   
3. **Menu Updates**: How should the tree handle real-time updates (e.g., new artists added)?
   - Proposed: MenuBuilder can rebuild portions of tree
   
4. **Backward Compatibility**: How long should we maintain dict-based API?
   - Proposed: Phase out over 2-3 refactor phases

