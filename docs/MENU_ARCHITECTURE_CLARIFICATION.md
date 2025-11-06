# Menu Architecture - Clarification: Static in JSON Only

## 🎯 Confirmed Approach: Configuration-Driven, Not Code-Driven

You want:
> **ALL static menu structure in JSON file. NOTHING in code. Only dynamic content (actual API results) generated at runtime.**

This is the **clean architecture** approach. Perfect!

---

## 📋 What Goes Where

### ✅ **IN JSON FILE** (all static structure)
- Menu hierarchy (root, music, artists, chromecasts, etc.)
- Alphabetical groups (A-D, E-H, I-M, etc.) ← **Key insight!**
- Device names and IDs
- All menu metadata (names, IDs, payloads)
- All actions and parameters

### ✅ **GENERATED AT RUNTIME** (dynamic content only)
- Actual artists from Subsonic API (for A-D group, artists starting E-H, etc.)
- Actual albums from Subsonic API
- Actual tracks (if needed)
- Any other live data that changes

### ❌ **NOT IN CODE** (moved to JSON)
- Alphabetical groups (were implicitly in SubsonicConfigAdapter)
- Menu structure (some was implicit in navigation logic)
- String-based menu ID generation
- Any hard-coded menu definitions

---

## 📊 New JSON Structure (Proposed)

```json
{
  "root": {
    "name": "Root",
    "items": [
      {
        "id": "music",
        "name": "Music",
        "payload": {"action": "navigate", "target": "music_menu"}
      },
      {
        "id": "chromecasts",
        "name": "Chromecasts",
        "payload": {"action": "navigate", "target": "chromecasts_menu"}
      }
    ]
  },
  
  "music_menu": {
    "name": "Music",
    "items": [
      {
        "id": "artists",
        "name": "Artists",
        "payload": {"action": "navigate", "target": "artists_menu"}
      },
      {
        "id": "albums",
        "name": "Albums",
        "payload": {"action": "browse_albums"}
      }
    ]
  },
  
  "artists_menu": {
    "name": "Browse Artists",
    "items": [
      {
        "id": "artists_a_d",
        "name": "A - D",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "A",
          "end_letter": "D"
        }
      },
      {
        "id": "artists_e_h",
        "name": "E - H",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "E",
          "end_letter": "H"
        }
      },
      {
        "id": "artists_i_m",
        "name": "I - M",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "I",
          "end_letter": "M"
        }
      },
      {
        "id": "artists_n_r",
        "name": "N - R",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "N",
          "end_letter": "R"
        }
      },
      {
        "id": "artists_s_v",
        "name": "S - V",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "S",
          "end_letter": "V"
        }
      },
      {
        "id": "artists_w_z",
        "name": "W - Z",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "W",
          "end_letter": "Z"
        }
      }
    ]
  },
  
  "chromecasts_menu": {
    "name": "Chromecasts",
    "items": [
      {
        "id": "chromecast_living_room",
        "name": "🔗 Living Room",
        "payload": {
          "action": "select_device",
          "device_id": "living_room",
          "device_name": "Living Room"
        }
      },
      {
        "id": "chromecast_tv_lounge",
        "name": "⚪ TV Lounge",
        "payload": {
          "action": "select_device",
          "device_id": "tv_lounge",
          "device_name": "TV Lounge"
        }
      },
      {
        "id": "chromecast_signe",
        "name": "⚪ Signe",
        "payload": {
          "action": "select_device",
          "device_id": "signe",
          "device_name": "Signe"
        }
      },
      {
        "id": "chromecast_bathroom",
        "name": "⚪ Bathroom Speaker",
        "payload": {
          "action": "select_device",
          "device_id": "bathroom_speaker",
          "device_name": "Bathroom Speaker"
        }
      }
    ]
  }
}
```

---

## 🏗️ Architecture Flow (Refined)

```
┌─────────────────────────────────────────────────────┐
│         menu_config.json (ALL static)               │
│  • Root                                              │
│  • Music → Artists, Albums                          │
│  • Artists → A-D, E-H, I-M, N-R, S-V, W-Z          │
│  • Chromecasts → Devices                            │
│  • Devices → Living Room, TV Lounge, etc.           │
│  NO CODE, PURE CONFIG                              │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│         MenuBuilder (Build Tree Once)               │
│  1. Load menu_config.json                           │
│  2. Create MenuNode tree from ALL items in JSON     │
│  3. Return complete static tree                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│    Global MenuNode Tree (Ready for Navigation)      │
│  Root                                                │
│  ├─ Music                                           │
│  │  ├─ Artists                                      │
│  │  │  ├─ A-D (static, will load dynamic children) │
│  │  │  ├─ E-H (static, will load dynamic children) │
│  │  │  └─ ...                                       │
│  │  └─ Albums                                       │
│  └─ Chromecasts                                     │
│     ├─ Living Room (static)                        │
│     ├─ TV Lounge (static)                          │
│     └─ ...                                          │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
   Navigator    EventProcessor  DynamicLoader
   (navigate)   (extract actions)(load actual artists)
         ↓           ↓           ↓
      User sees   Events fired  API called for
      structure   (play, select) specific range
```

---

## 🔄 How It Works

### Example: Browse Artists A-D

**1. User navigates to "Artists"**
```
Navigator.navigate_to_child("artists")
→ Current node = "artists_menu"
```

**2. User sees list from JSON:**
```
[
  "A - D",
  "E - H", 
  "I - M",
  ...
]
```
All these are static MenuNodes from JSON

**3. User selects "A - D"**
```
EventProcessor.process_node_selection(node_a_d)
→ Payload says: action="load_dynamic", start_letter="A", end_letter="D"
→ Event emitted with these parameters
```

**4. Dynamic loader fetches actual artists**
```
DynamicLoader.load_artists_for_range("A", "D")
→ Calls Subsonic API
→ Returns actual artists (Abba, AC/DC, etc.)
→ Creates MenuNodes for each
→ Adds as children to "A - D" node
```

**5. UI displays actual artists**
```
Navigator.get_current_children()
→ Returns "A - D" node with children (Abba, AC/DC, etc.)
→ UI renders them
```

---

## 💾 JSON Structure Advantages

### Before (Code-driven - Bad)
```python
# Had to generate alphabetical groups in code
groups = self.subsonic_service.get_alphabetical_groups()
# or hard-coded in SubsonicConfigAdapter
for group in groups:
    create_menu_node(...)

# To change structure: modify code, redeploy
```

### After (JSON-driven - Good)
```json
// All structure in JSON
"artists_a_d": {...},
"artists_e_h": {...},
// To change structure: edit JSON, reload config
// NO code change needed
```

---

## 🎯 Key Principle

> **JSON file defines the COMPLETE static menu structure (hierarchy, navigation paths, static items). Code only handles dynamic content generation (actual API results).**

---

## ✅ What This Means for Implementation

### MenuBuilder (Simpler Now!)
```python
def load_static_menus(self, config_data: Dict) -> bool:
    """
    Load menu structure from JSON.
    That's it! Nothing else needed.
    """
    # Just iterate through config and create MenuNodes
    # No special logic for artist groups
    # No special logic for any static structure
    # Just pure JSON → MenuNode tree
```

### DynamicLoader (New responsibility)
```python
def load_artists_in_range(self, start_letter: str, end_letter: str):
    """
    When user navigates to A-D node and selects it,
    THIS code runs to fetch actual artists from API
    and create MenuNodes for them
    """
    artists = self.subsonic_api.get_artists(start_letter, end_letter)
    for artist in artists:
        create_menu_node(artist)  # This is the dynamic part
```

### EventProcessor (Routes to right handler)
```python
def process_node_selection(self, node):
    if node.payload.get("action") == "navigate":
        # Static navigation
        self.navigator.navigate_to_node(...)
    elif node.payload.get("action") == "load_dynamic":
        # Dynamic loading
        self.dynamic_loader.load_artists_in_range(...)
    elif node.payload.get("action") == "select_device":
        # Device selection
        self.emit_event(EventType.DEVICE_SELECTED, ...)
```

---

## 📝 Updated JSON for Your System

Here's what your `menu_config.json` should look like:

```json
{
  "root": {
    "name": "Root",
    "items": [
      {
        "id": "music",
        "name": "🎵 Music",
        "payload": {"action": "navigate", "target": "music_menu"}
      },
      {
        "id": "chromecasts",
        "name": "🔊 Chromecasts",
        "payload": {"action": "navigate", "target": "chromecasts_menu"}
      }
    ]
  },
  
  "music_menu": {
    "name": "Music",
    "items": [
      {
        "id": "browse_artists",
        "name": "Browse Artists",
        "payload": {"action": "navigate", "target": "artists_menu"}
      },
      {
        "id": "browse_albums",
        "name": "Browse Albums",
        "payload": {"action": "browse_albums"}
      }
    ]
  },
  
  "artists_menu": {
    "name": "Artists",
    "items": [
      {
        "id": "artists_a_d",
        "name": "A - D",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "A",
          "end_letter": "D"
        }
      },
      {
        "id": "artists_e_h",
        "name": "E - H",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "E",
          "end_letter": "H"
        }
      },
      {
        "id": "artists_i_m",
        "name": "I - M",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "I",
          "end_letter": "M"
        }
      },
      {
        "id": "artists_n_r",
        "name": "N - R",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "N",
          "end_letter": "R"
        }
      },
      {
        "id": "artists_s_v",
        "name": "S - V",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "S",
          "end_letter": "V"
        }
      },
      {
        "id": "artists_w_z",
        "name": "W - Z",
        "payload": {
          "action": "load_dynamic",
          "dynamic_type": "artists_in_range",
          "start_letter": "W",
          "end_letter": "Z"
        }
      }
    ]
  },
  
  "chromecasts_menu": {
    "name": "Chromecasts",
    "items": [
      {
        "id": "device_living_room",
        "name": "🔗 Living Room",
        "payload": {
          "action": "select_device",
          "device_id": "living_room",
          "device_name": "Living Room"
        }
      },
      {
        "id": "device_tv_lounge",
        "name": "⚪ TV Lounge",
        "payload": {
          "action": "select_device",
          "device_id": "tv_lounge",
          "device_name": "TV Lounge"
        }
      },
      {
        "id": "device_signe",
        "name": "⚪ Signe",
        "payload": {
          "action": "select_device",
          "device_id": "signe",
          "device_name": "Signe"
        }
      },
      {
        "id": "device_bathroom",
        "name": "⚪ Bathroom Speaker",
        "payload": {
          "action": "select_device",
          "device_id": "bathroom_speaker",
          "device_name": "Bathroom Speaker"
        }
      }
    ]
  }
}
```

---

## 🎨 Benefits of This Approach

1. **No Code in JSON** ✅
   - JSON is pure data
   - Easy to edit without programming knowledge
   - No risk of syntax errors breaking code
   
2. **Easy to Extend** ✅
   - Add new alphabetical groups? Edit JSON
   - Add new devices? Edit JSON
   - Add new music categories? Edit JSON
   - NO code changes needed

3. **Clear Separation** ✅
   - JSON = Static structure (what exists)
   - Code = Dynamic content (what changes)
   - Code = Navigation logic (how it works)

4. **Single Source of Truth** ✅
   - All static structure in one JSON file
   - No duplication in code
   - Easy to review structure

5. **Configuration-Driven** ✅
   - Entire menu structure is configuration
   - Can swap JSON files for different setups
   - Perfect for multiple installations

---

## 📋 Summary

**Configuration approach:**
```
Menu structure (what) → JSON file
Navigation logic (how) → Python code  
Dynamic content (data) → Subsonic API
```

**You want:**
- ✅ Artist groups (A-D, E-H, etc.) in JSON (not generated in code)
- ✅ Device list in JSON (not scattered in code)
- ✅ All static structure in JSON
- ✅ Only dynamic data (actual API results) generated at runtime

**Result:**
- Clean separation between config and code
- Easy to modify menu structure without touching code
- Clear what's static (in JSON) vs dynamic (from API)
- Single global MenuNode tree from pure JSON structure

---

## ✅ Next Steps

1. Update `menu_config.json` with the new structure above
2. Update `MenuBuilder` to just load JSON → build tree (no special logic)
3. Create `DynamicContentLoader` to handle loading actual artists, albums, etc.
4. `EventProcessor` routes to correct handler based on payload action
5. Everything flows from the JSON config

This is the **cleanest approach** - configuration-driven, not code-driven! 🎉

