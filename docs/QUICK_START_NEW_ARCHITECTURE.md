# Quick Start: New Menu Architecture Components

## 🎯 What You Now Have

### MenuBuilder (`app/ui/menu/menu_builder.py`)
Builds the global MenuNode tree from JSON configuration.

**Usage**:
```python
from app.ui.menu.menu_builder import initialize_menu_tree, find_menu_node

# At app startup
root = initialize_menu_tree()  # Loads menu_config.json, builds tree

# Later, find any node
node = find_menu_node("artists_a_d")  # Lookup by ID
```

**Key Classes/Functions**:
- `MenuBuilder` - Main builder class (handles tree construction)
- `initialize_menu_tree()` - Called once at startup
- `get_menu_builder()` - Get singleton instance
- `find_menu_node(node_id)` - Fast lookup by ID
- `get_menu_root()` - Get root node

### MenuEventProcessor (`app/ui/menu/menu_event_processor.py`)
Extracts actions from MenuNodes and routes to handlers.

**Usage**:
```python
from app.ui.menu.menu_event_processor import (
    get_menu_event_processor, 
    ActionType, 
    MenuEvent
)

processor = get_menu_event_processor()

# When user selects a menu item
event = processor.process_node_selection(node)

# Check what action was triggered
if event.action_type == ActionType.BROWSE_ARTISTS_IN_RANGE:
    start = event.parameters["start_letter"]
    end = event.parameters["end_letter"]
    # Load artists from start to end
```

**ActionTypes**:
- `NAVIGATE` - Navigate to submenu
- `LOAD_DYNAMIC` - Load dynamic content
- `BROWSE_ARTISTS_IN_RANGE` - Load artists in range
- `BROWSE_ARTIST_ALBUMS` - Load artist albums
- `SELECT_ALBUM` - Play album
- `SELECT_DEVICE` - Switch device
- `UNKNOWN` - Unknown action

### MenuDataService (Updated)
Now uses MenuNode tree instead of dicts.

**Updated Methods**:
```python
from app.ui.menu.menu_data_service import MenuDataService

service = MenuDataService()  # Automatically initializes tree

# Navigate
service.navigate_to_node(node)              # Go to specific node
service.navigate_to_child("child_id")       # Go to child by ID
service.navigate_to_child_at_index(0)       # Go to child by index
service.go_back()                           # Go back one level
service.reset_to_root()                     # Go to root

# Query
current_node = service.get_current_node()           # Get current MenuNode
children = service.get_current_menu_items()        # Get children as MenuNodes
item = service.find_menu_item_by_id("item_id")    # Find in current menu
count = service.get_menu_count()                    # Count children
is_valid = service.is_valid_index(0)               # Check index validity
```

**Removed Methods** (will be replaced by DynamicLoader):
- ~~`load_dynamic_menu()`~~ - Use DynamicLoader instead
- ~~`navigate_to_menu(level)`~~ - Use `navigate_to_node(node)`

## 📋 menu_config.json Structure

```json
{
  "root": {
    "name": "Root Menu",
    "items": [
      {
        "id": "music",
        "name": "🎵 Music",
        "menu_ref": "music_menu"
      },
      {
        "id": "chromecasts",
        "name": "📻 Chromecasts",
        "menu_ref": "chromecasts_menu"
      }
    ]
  },
  "music_menu": {
    "name": "Music Library",
    "items": [
      {
        "id": "browse_artists",
        "name": "Browse Artists",
        "menu_ref": "artists"
      }
    ]
  },
  "artists": {
    "name": "Artists",
    "items": [
      {
        "id": "artists_a_d",
        "name": "A - D",
        "payload": {
          "action": "browse_artists_in_range",
          "start_letter": "A",
          "end_letter": "D"
        }
      },
      {
        "id": "artists_e_h",
        "name": "E - H",
        "payload": {
          "action": "browse_artists_in_range",
          "start_letter": "E",
          "end_letter": "H"
        }
      }
    ]
  },
  "chromecasts_menu": {
    "name": "Select Device",
    "items": [
      {
        "id": "device_living_room",
        "name": "Living Room",
        "payload": {
          "action": "select_device",
          "device_name": "Living Room"
        }
      }
    ]
  }
}
```

## 🔄 MenuNode Structure

```python
class MenuNode:
    id: str                 # Unique identifier
    name: str              # Display name
    parent: Optional[MenuNode]  # Parent node (or None if root)
    children: List[MenuNode]    # Child nodes
    payload: Dict[str, Any]     # Action metadata
    
    # Methods:
    add_child(node)        # Add a child
    get_child_by_id(id)    # Find child by ID
    get_path_to_root()     # Get path from root to this node
    to_dict()              # Convert to dictionary
```

## 🎯 Action Flow Example

```
User selects "A - D" artists
    ↓
MenuController.activate_selected()
    ↓
Find MenuNode for "artists_a_d"
    ↓
MenuEventProcessor.process_node_selection(node)
    ├─ Read payload: {"action": "browse_artists_in_range", "start_letter": "A", "end_letter": "D"}
    ├─ Create MenuEvent with ActionType.BROWSE_ARTISTS_IN_RANGE
    └─ Return event with parameters
    ↓
MenuController._activate_menu_item()
    ├─ Check if action_type == ActionType.BROWSE_ARTISTS_IN_RANGE
    ├─ Extract start_letter="A", end_letter="D"
    └─ TODO: Call DynamicLoader (Phase 3)
```

## 📝 Payload Format

All static menu items should have a `payload` with `action` and parameters:

```json
{
  "id": "unique_id",
  "name": "Display Name",
  "payload": {
    "action": "action_type_here",
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Common actions in payload**:
- `browse_artists_in_range` - start_letter, end_letter
- `select_device` - device_name
- `select_album` - album_id
- `play_album` - album_id, album_name

## ✅ What's Tested

- MenuBuilder loads JSON and builds tree ✅
- MenuNode tree has correct hierarchy ✅
- MenuDataService navigates tree correctly ✅
- MenuEventProcessor extracts actions correctly ✅
- MenuController displays menus with pagination ✅
- All syntax valid, no import errors ✅

## ⏳ What's Next (Phase 3)

1. **DynamicLoader** - Load artists/albums from Subsonic API
2. **Cleanup** - Remove old JsonMenuAdapter and SubsonicConfigAdapter
3. **Testing** - End-to-end tests for dynamic content

## 📚 Related Files

- `ARCHITECTURE_REVIEW.md` - Full analysis of old architecture
- `MENU_IMPLEMENTATION_GUIDE.md` - Implementation details
- `VISUAL_SUMMARY_JSON_ARCHITECTURE.md` - Visual diagrams
- `PHASE_1_2_COMPLETE.md` - Detailed completion report

---

**Status**: ✅ Phase 1-2 Complete - Ready for Phase 3 DynamicLoader Implementation

