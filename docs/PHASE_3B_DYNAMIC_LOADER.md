# Next Steps: Phase 3b - DynamicLoader Implementation

## What's Working Now
✅ Static menu structure loads from JSON  
✅ MenuNode tree built and navigable  
✅ Event extraction working  
✅ MenuController integrated  

## What's Needed: DynamicLoader

### The Problem
When user selects "A - D" artists group, the node exists but has no children. We need to:
1. Load actual artists from Subsonic API
2. Create MenuNode objects for each artist
3. Add them as children to the "A - D" node
4. Then navigation works naturally

### The Solution: DynamicLoader

```python
# Step 1: Create DynamicLoader (new file)
# app/ui/menu/dynamic_loader.py

class DynamicLoader:
    """Load dynamic content from Subsonic and return MenuNodes"""
    
    def __init__(self, subsonic_service):
        self.subsonic = subsonic_service
    
    def load_artists_in_range(self, start_letter, end_letter):
        """
        Load artists from Subsonic API for range A-D, E-H, etc.
        
        Returns: List of MenuNode objects (one per artist)
        """
        # Call Subsonic API to get artists in range
        artists = self.subsonic.get_artists_in_range(start_letter, end_letter)
        
        # Convert each to MenuNode
        nodes = []
        for artist in artists:
            node = MenuNode(
                id=f"artist_{artist.id}",
                name=artist.name,
                parent=None,  # Will be set when added to tree
                payload={"action": "browse_artist_albums", "artist_id": artist.id}
            )
            nodes.append(node)
        
        return nodes
    
    def load_artist_albums(self, artist_id):
        """
        Load albums for specific artist.
        
        Returns: List of MenuNode objects (one per album)
        """
        albums = self.subsonic.get_artist_albums(artist_id)
        
        nodes = []
        for album in albums:
            node = MenuNode(
                id=f"album_{album.id}",
                name=album.name,
                parent=None,
                payload={"action": "select_album", "album_id": album.id}
            )
            nodes.append(node)
        
        return nodes
```

### How It Integrates

```
User navigates to "A - D" artist group
     ↓
MenuController._activate_menu_item(node)
     ↓
MenuEventProcessor identifies action: browse_artists_in_range
     ↓
Parameters: {start_letter: A, end_letter: D}
     ↓
NEW: Call DynamicLoader.load_artists_in_range("A", "D")
     ↓
Get List[MenuNode] of actual artists from API
     ↓
MenuBuilder.add_dynamic_nodes("artists_a_d", nodes)
     ↓
Now "A - D" node has children (Abba, AC/DC, etc.)
     ↓
MenuDataService.navigate_to_node(node)
     ↓
Show artists in menu!
```

### Implementation Steps

1. **Create DynamicLoader**
   - File: `app/ui/menu/dynamic_loader.py`
   - Methods: `load_artists_in_range()`, `load_artist_albums()`
   - Return: `List[MenuNode]`

2. **Update MenuController**
   - In `_activate_menu_item()`, when action is `BROWSE_ARTISTS_IN_RANGE`:
     ```python
     elif action_type == ActionType.BROWSE_ARTISTS_IN_RANGE:
         start = payload.get("start_letter")
         end = payload.get("end_letter")
         
         loader = DynamicLoader(get_subsonic_service())
         artist_nodes = loader.load_artists_in_range(start, end)
         
         builder = get_menu_builder()
         builder.add_dynamic_nodes(node.id, artist_nodes)
         
         # NOW navigate works
         self.menu_data.navigate_to_node(node)
         self.selected_index = 0
         self._load_current_menu_items()
         self._emit_menu_screen_update()
     ```

3. **Handle BROWSE_ARTIST_ALBUMS similarly**
   ```python
   elif action_type == ActionType.BROWSE_ARTIST_ALBUMS:
       artist_id = payload.get("artist_id")
       
       loader = DynamicLoader(get_subsonic_service())
       album_nodes = loader.load_artist_albums(artist_id)
       
       builder = get_menu_builder()
       builder.add_dynamic_nodes(node.id, album_nodes)
       
       self.menu_data.navigate_to_node(node)
       self.selected_index = 0
       self._load_current_menu_items()
       self._emit_menu_screen_update()
   ```

4. **Clean Up Old Code** (Phase 4)
   - Remove `JsonMenuAdapter` (only used MenuBuilder now)
   - Remove `SubsonicConfigAdapter` (replaced by DynamicLoader)
   - Remove old `load_dynamic_menu()` calls from MenuDataService

---

## Data Flow Example: "Select Album to Play"

```
menu_config.json
│
├─ root
│  └─ items: [Music, Chromecasts]
│
├─ music_menu
│  └─ items: [Browse Artists, Browse Albums]
│
└─ artists_menu
   └─ items: [A-D, E-H, I-M, ...]  ← All in JSON


User Journey:
─────────────

1. Enters menu → Shows root
   Items: [Music, Chromecasts]

2. Selects "Music" → Navigates to music_menu
   Items: [Browse Artists, Browse Albums]

3. Selects "Browse Artists" → Navigates to artists_menu
   Items: [A-D, E-H, I-M, N-R, S-V, W-Z]

4. Selects "A-D" → BROWSE_ARTISTS_IN_RANGE action
   DynamicLoader loads artists from Subsonic
   Creates nodes: [Abba, AC/DC, Adams Ryan, ...]
   MenuBuilder adds them as children
   Navigates to "A-D" node
   Items: [Abba, AC/DC, Adams Ryan, ...]

5. Selects "Abba" → BROWSE_ARTIST_ALBUMS action
   DynamicLoader loads albums for artist
   Creates nodes: [Dancing Queen, Mamma Mia, ...]
   MenuBuilder adds them as children
   Navigates to "Abba" node
   Items: [Dancing Queen, Mamma Mia, ...]

6. Selects "Dancing Queen" → SELECT_ALBUM action
   Emits PLAY_ALBUM event
   PlaybackManager starts playback
   Exits menu
```

---

## Testing DynamicLoader on RPi

```python
# Test 1: Verify DynamicLoader loads artists
from app.ui.menu.dynamic_loader import DynamicLoader
from app.services.subsonic_service import SubsonicService

subsonic = SubsonicService()
loader = DynamicLoader(subsonic)

# Load artists A-D
artists_nodes = loader.load_artists_in_range("A", "D")
print(f"Loaded {len(artists_nodes)} artists in A-D range")
for node in artists_nodes[:5]:  # Show first 5
    print(f"  - {node.name} (payload: {node.payload})")

# Test 2: Verify nodes can be added to tree
from app.ui.menu.menu_builder import get_menu_builder

builder = get_menu_builder()
builder.add_dynamic_nodes("artists_a_d", artists_nodes)

# Verify we can now find them
ad_node = builder.get_node_by_id("artists_a_d")
print(f"A-D node now has {len(ad_node.children)} children")

# Test 3: Verify MenuDataService can navigate to them
from app.ui.menu.menu_data_service import MenuDataService

service = MenuDataService()
service.navigate_to_menu("music")
service.navigate_to_menu("artists_menu")
service.navigate_to_child("artists_a_d")

items = service.get_current_menu_items()
print(f"Currently viewing: {service.get_current_node().name}")
print(f"Items: {len(items)}")
```

---

## Files to Create/Modify

| File | Action | Complexity |
|------|--------|-----------|
| `app/ui/menu/dynamic_loader.py` | CREATE | Easy (100 lines) |
| `app/ui/menu/menu_controller.py` | MODIFY | Medium (add ~30 lines) |
| `app/ui/menu/menu_data_service.py` | Optional cleanup | Easy |
| `app/ui/menu/json_menu_adapter.py` | DELETE (Phase 4) | N/A |
| `app/ui/menu/subsonic_config_adapter.py` | DELETE (Phase 4) | N/A |

---

## Architecture After Phase 3b

```
┌──────────────────────────────────────┐
│      menu_config.json                │
│  Static structure only               │
└──────────────┬───────────────────────┘
               │
               ↓
        ┌──────────────────┐
        │ MenuBuilder      │
        │ • load_config()  │
        │ • build_tree()   │
        │ • add_dynamic_X()│
        └────────┬─────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │ MenuNode Tree        │
        │ (Static + Dynamic)   │
        └────────┬─────────────┘
                 │
      ┌──────────┴──────────┐
      ↓                     ↓
┌───────────────┐   ┌──────────────────┐
│ MenuDataSvc   │   │ DynamicLoader    │
│ (navigate)    │   │ (fetch from API) │
└──────┬────────┘   └────────┬─────────┘
       │                     │
       └─────────┬───────────┘
               ↓
        ┌──────────────────┐
        │ MenuEventProc    │
        │ (extract action) │
        └────────┬─────────┘
                 │
                 ↓
        ┌──────────────────┐
        │ MenuController   │
        │ (route + handle) │
        └──────────────────┘
```

**All components working together:**
- **Static:** JSON config → MenuBuilder → MenuNode tree
- **Dynamic:** Subsonic API → DynamicLoader → MenuNode tree
- **Navigation:** MenuDataService traverses tree
- **Actions:** MenuEventProcessor extracts actions
- **UI:** MenuController handles pagination and user input

---

## Ready for Next Iteration?

✅ Phase 1: MenuBuilder + MenuEventProcessor + MenuDataService refactor  
✅ Phase 2: MenuController integration  
🔄 Phase 3b: DynamicLoader implementation (next)  
⏳ Phase 4: Cleanup and testing

**Recommendation:** Test Phase 1 on your RPi first using the test cases above, then proceed to Phase 3b when ready.

