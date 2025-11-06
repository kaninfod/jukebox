# Menu Architecture: Current vs Proposed Flow Comparison

## Current Data Flow (Problematic)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MenuController                              │
│  (Manages UI state, pagination, selection, event handlers)           │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       MenuDataService                                │
│  (Pure data layer - but only sort of...)                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ get_current_menu() returns different types:               │   │
│  │ • Dict from JSON (static)                                 │   │
│  │ • Dict wrapper around MenuNode list (dynamic)             │   │
│  │                                                            │   │
│  │ Runtime type checking:                                    │   │
│  │ if hasattr(items[0], 'to_dict'): convert()              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
    ┌────────────────┐   ┌──────────────────────┐
    │ JsonMenuAdapter│   │ SubsonicConfigAdapter│
    │                │   │                      │
    │ Returns: Dict  │   │ Returns: MenuNode[]  │
    └────────────────┘   │ (not integrated)     │
         ↓               └──────────────────────┘
    ┌────────────────┐            ↓
    │ menu_config.   │    ┌──────────────────────┐
    │ json (static)  │    │ Subsonic API calls   │
    └────────────────┘    │ (fetches on-demand)  │
                          └──────────────────────┘

PROBLEMS:
❌ Two separate data sources (JSON + API)
❌ Different return types from same service
❌ Runtime type conversion throughout code
❌ Navigation logic duplicated for static/dynamic
❌ No unified tree structure
❌ State tracking via string identifiers (fragile)
```

---

## Proposed Data Flow (Clean)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MenuController                              │
│  (Manages UI state, pagination, selection)                           │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       MenuDataService                                │
│  (Pure data layer - single source of truth)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Always returns MenuNode objects                             │  │
│  │ No type conversion                                          │  │
│  │ get_current_children() → List[MenuNode]                   │  │
│  │ navigate_to_child() → bool                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────────────┐
        │   Global MenuNode Tree        │
        │  (Built once at init)         │
        │  (Static + Dynamic integrated)│
        └──────────────────────────────┘
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
    ┌──────────────────┐  ┌─────────────────────┐
    │ MenuBuilder      │  │ MenuNodeNavigator   │
    │                  │  │                     │
    │ Loads JSON       │  │ Navigate tree       │
    │ + dynamic data   │  │ Query nodes         │
    │ = MenuNode tree  │  │ Get breadcrumbs     │
    └──────────────────┘  └─────────────────────┘
         ↓                         ↓
    ┌──────────────────┐  ┌─────────────────────┐
    │ menu_config.json │  │ MenuEventProcessor  │
    │ (loaded once)    │  │                     │
    │                  │  │ Extract payloads    │
    │ + SubsonicAPI    │  │ Raise events       │
    │ (on init/reload) │  │                     │
    └──────────────────┘  └─────────────────────┘

BENEFITS:
✅ Single tree (static + dynamic unified)
✅ Single return type (always MenuNode)
✅ Consistent navigation API
✅ Built once, navigated many times
✅ Type-safe throughout
✅ Clear separation of concerns
```

---

## Code Comparison: Static Menu Navigation

### Current (Problematic)

```python
# MenuDataService
def navigate_to_menu(self, menu_level: str) -> bool:
    """Navigate to a specific menu level."""
    if self.json_config.menu_exists(menu_level):  # Only checks static
        # Save current level to history for back navigation
        self.menu_history.append(self.current_menu_level)
        self.current_menu_level = menu_level  # String identifier ❌
        logger.info(f"Navigated to menu level: {menu_level}")
        return True
    else:
        logger.warning(f"Menu level not found: {menu_level}")
        return False

def get_current_menu_items(self) -> List[Dict[str, Any]]:
    """Get items for the current menu level."""
    current_menu = self.get_current_menu()
    items = current_menu.get("items", [])
    
    # Convert MenuNode objects to dict format if needed ❌ Runtime checking
    if items and hasattr(items[0], 'to_dict'):
        items = [item.to_dict() for item in items]
    
    return items

# MenuController
def _load_current_menu_items(self):
    """Load menu items."""
    self.all_menu_items = self.menu_data.get_current_menu_items()
    # Returns either dicts or converted MenuNodes ❌ Type ambiguity
```

### Proposed (Clean)

```python
# MenuDataService
def navigate_to_child(self, child_id: str) -> bool:
    """Navigate to a child node by ID."""
    child = self.navigator.current_node.get_child_by_id(child_id)
    if child:
        return self.navigator.navigate_to_node(child)
    return False

def get_current_children(self) -> List[MenuNode]:
    """Get children of current node."""
    return self.navigator.get_current_children()  # ✅ Always MenuNode
    
def get_current_children_as_dicts(self) -> List[Dict[str, Any]]:
    """Get children as dicts for UI rendering (conversion only at UI boundary)."""
    return [child.to_dict() for child in self.get_current_children()]

# MenuController
def _load_current_menu_items(self):
    """Load menu items."""
    self.all_menu_items = self.menu_data.get_current_children()
    # Returns List[MenuNode] - type safe ✅
```

---

## Code Comparison: Dynamic Menu Navigation

### Current (Problematic)

```python
# MenuDataService
def load_dynamic_menu(self, menu_type: str, **kwargs) -> bool:
    """Load a dynamic menu using the SubsonicConfigAdapter."""
    if not self.subsonic_config:
        logger.error("SubsonicConfigAdapter not available")
        return False
    
    try:
        # Generate unique menu identifier
        menu_id = f"dynamic_{menu_type}"
        if kwargs:
            # Add parameters to make unique identifier ❌ Fragile ID generation
            param_str = "_".join(f"{k}_{v}" for k, v in kwargs.items())
            menu_id += f"_{param_str}"
        
        # Get dynamic menu nodes
        menu_nodes = self.subsonic_config.get_dynamic_menu_nodes(menu_type, **kwargs)
        
        # Store in dynamic menus cache
        self._dynamic_menus[menu_id] = {"items": menu_nodes}  # ❌ Wrap in dict
        
        # Navigate to the dynamic menu
        self.menu_history.append(self.current_menu_level)
        self.current_menu_level = menu_id  # ❌ Still string identifier
        
        logger.info(f"Loaded dynamic menu: {menu_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load dynamic menu {menu_type}: {e}")
        return False

# MenuController
def handle_music_navigation(self, selected_item):
    """Handle music menu navigation."""
    menu_type = selected_item.get("menu_type")  # ❌ Digging into dicts
    menu_params = selected_item.get("menu_params", {})
    
    if menu_type and self.menu_data.load_dynamic_menu(menu_type, **menu_params):
        self._load_current_menu_items()
        return True
    return False
```

### Proposed (Clean)

```python
# MenuDataService (and MenuBuilder internally)
class MenuBuilder:
    """Build global tree with dynamic content pre-integrated."""
    
    def __init__(self):
        self.root = MenuNode(id="root", name="Root")
    
    def load_static_menus(self, config: Dict) -> None:
        """Load static menu structure from JSON."""
        # Build tree from config
    
    def add_dynamic_menu_generator(self, parent_id: str, generator_func) -> None:
        """Attach a function that generates children on-demand."""
        parent = self.root.find_by_id(parent_id)
        if parent:
            parent.dynamic_children_generator = generator_func
            parent.is_dynamic = True

def navigate_to_child(self, child_id: str) -> bool:
    """Navigate to child - works same for static AND dynamic."""
    child = self.navigator.current_node.get_child_by_id(child_id)
    if child:
        # If node has dynamic children, generate them on first access
        if child.is_dynamic and not child.children:
            child.dynamic_children_generator()  # ✅ Lazy generation
        return self.navigator.navigate_to_node(child)
    return False

# MenuController
def handle_item_selection(self, selected_item: MenuNode):  # ✅ MenuNode, not dict
    """Handle any menu item selection."""
    # Same code works for static AND dynamic
    if self.menu_data.navigate_to_child(selected_item.id):
        self._load_current_menu_items()
        return True
    return False
```

---

## Initialization Flow Comparison

### Current (Scattered)

```
Application Start
    ↓
MenuDataService.__init__()
    ├─ Initialize JsonMenuAdapter
    │  └─ Stores path to menu_config.json (but doesn't load yet!)
    │
    ├─ Initialize SubsonicService
    │  └─ May fail, becomes None
    │
    ├─ Initialize SubsonicConfigAdapter (conditionally)
    │  └─ Stores reference to SubsonicService
    │
    ├─ Initialize empty _dynamic_menus dict
    │
    └─ Call json_config.load_config()
       └─ Loads JSON into self.menu_data dict

Current state: Static menus loaded, dynamic not yet
Dynamic menus only created when navigated to ❌

Problems:
- Uninitialized state (dynamic menus missing)
- Incomplete data on first access
- Lazy loading mixed with eager loading
```

### Proposed (Predictable)

```
Application Start
    ↓
MenuDataService.initialize()
    ├─ MenuBuilder starts building tree
    │  ├─ Load menu_config.json
    │  ├─ Create MenuNode tree from JSON
    │  │  (Root → Music → Artists, Albums, etc.)
    │  │
    │  └─ Add dynamic content
    │     ├─ Fetch artists groups from Subsonic
    │     ├─ Create MenuNode for each group
    │     ├─ Attach as children to "Artists" node
    │     │
    │     ├─ Fetch artist list for each group
    │     ├─ Create MenuNode for each artist
    │     ├─ Attach as children to group nodes
    │     │
    │     └─ Attach dynamic generator for sub-items
    │        (albums per artist, tracks per album)
    │
    └─ Complete tree ready for navigation ✅

Current state: Complete MenuNode tree, all data integrated
Ready for immediate navigation ✅

Benefits:
- Predictable state after init
- Complete data available
- No surprises during navigation
- Easier to test
```

---

## Memory Model Comparison

### Current (Fragmented)

```
MenuDataService Instance
├─ json_config: JsonMenuAdapter
│  └─ menu_data: Dict[str, Dict[str, Any]]  ← Static menus (dict copies)
│     ├─ "root": {"items": [...]}
│     ├─ "music_menu": {"items": [...]}
│     └─ "chromecasts_menu": {"items": [...]}
│
├─ subsonic_config: SubsonicConfigAdapter
│  └─ _cached_menu_data: Dict  ← Cache but sparse, incomplete
│
└─ _dynamic_menus: Dict[str, Dict]
   ├─ "dynamic_artists_alphabetical": {"items": [MenuNode, ...]}
   ├─ "dynamic_artists_in_range_A_D": {"items": [MenuNode, ...]}
   └─ "dynamic_artist_albums_123": {"items": [MenuNode, ...]}

Problems:
- Data duplicated in different formats
- MenuNodes inside dicts
- Sparse caching
- No relationship tracking
```

### Proposed (Unified)

```
MenuDataService Instance
├─ builder: MenuBuilder
│  └─ root: MenuNode ← Single tree root
│     ├─ id: "root"
│     ├─ name: "Root"
│     ├─ payload: {}
│     ├─ children: [MenuNode, ...]
│     │  ├─ [0] MenuNode: id="music", name="Music"
│     │  │   ├─ payload: {action: "load_submenu", submenu: "music_menu"}
│     │  │   ├─ children: [MenuNode, ...]
│     │  │   │  ├─ MenuNode: id="artists", name="Artists"
│     │  │   │  │  ├─ is_dynamic: True
│     │  │   │  │  ├─ children: [MenuNode, ...]  ← Lazy-loaded
│     │  │   │  │  │  ├─ MenuNode: id="group_a_d", name="A-D"
│     │  │   │  │  │  │  ├─ children: [MenuNode, ...]  ← Lazy-loaded
│     │  │   │  │  │  │  └─ dynamic_generator: func()
│     │  │   │  │  │  └─ ...
│     │  │   │  │  └─ dynamic_generator: func()
│     │  │   │  │
│     │  │   │  └─ MenuNode: id="albums", name="Albums"
│     │  │   │
│     │  │   └─ payload: {...}
│     │  │
│     │  └─ [1] MenuNode: id="chromecasts", name="Chromecasts"
│     │     ├─ children: [MenuNode, ...]
│     │     └─ payload: {...}
│     │
│     └─ parent: None
│
└─ navigator: MenuNodeNavigator
   ├─ root: MenuNode (reference to same tree)
   ├─ current_node: MenuNode (navigation pointer)
   └─ navigation_history: [MenuNode, ...]

Benefits:
- Single source of truth
- All data in one place
- Natural hierarchy
- Lazy loading when needed
- No duplication
```

---

## Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Data Types** | Dict + MenuNode mixed | Always MenuNode |
| **Type Safety** | Runtime checks | Compile-time safe |
| **Navigation** | String IDs + 2 code paths | Node references + 1 code path |
| **Static vs Dynamic** | Completely different | Same code path |
| **Initialization** | Lazy/scattered | Complete/upfront |
| **Memory Model** | Fragmented | Unified tree |
| **Extensibility** | Difficult | Easy (add nodes) |
| **Testing** | Hard to mock | Easy (mock tree) |

