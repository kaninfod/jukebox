# Visual Summary: JSON-Driven Architecture

## The Principle (Simplified)

```
┌─────────────────────────────────────────────────┐
│         menu_config.json                        │
│  • What exists (structure)                      │
│  • Artist groups: A-D, E-H, I-M, N-R, S-V, W-Z │
│  • Devices: Living Room, TV Lounge, etc.        │
│  • Navigation paths                             │
│  STATIC - Doesn't change                       │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ MenuBuilder loads JSON
┌─────────────────────────────────────────────────┐
│         Global MenuNode Tree                    │
│  ✓ All static structure in one place            │
│  ✓ Ready for navigation                         │
│  ✓ Nodes have payload with parameters           │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ↓                   ↓
    ┌─────────────┐    ┌──────────────────┐
    │ Navigator   │    │ EventProcessor   │
    │ (navigate)  │    │ (extract action) │
    └─────────────┘    └────────┬─────────┘
         ↓                      ↓
    User moves       Routes to right handler
    through tree     ↓
                  Is it static?
                  ├─ YES: Navigate in tree
                  └─ NO: Call API for data
                        (DynamicLoader)
```

---

## Before vs After

### BEFORE ❌ (Messy)
```
Code file (SubsonicConfigAdapter):
  def get_alphabetical_groups():
      return [
          {"name": "A-D", "range": ("A", "D")},  ← MENU STRUCTURE IN CODE!
          {"name": "E-H", "range": ("E", "H")},
          ...
      ]

JSON file:
  "artists": { "action": "load_dynamic_menu", "type": "artists_alphabetical" }

MenuDataService:
  if menu_type == "artists_alphabetical":
      groups = subsonic_config.get_alphabetical_groups()  ← CALL CODE TO GET STRUCTURE
      create nodes from groups

PROBLEMS:
❌ Menu structure scattered in code
❌ Hard to see structure without reading code
❌ Can't change without coding
❌ Multiple places to update
```

### AFTER ✅ (Clean)
```
JSON file:
  "artists_menu": {
    "items": [
      { "id": "artists_a_d", "name": "A - D", ... },  ← MENU STRUCTURE IN JSON!
      { "id": "artists_e_h", "name": "E - H", ... },
      ...
    ]
  }

Code (MenuBuilder):
  def load_static_menus(config):
      for section_id, items in config.items():
          for item in items:
              create_node_from_item(item)              ← JUST LOAD FROM JSON!

BENEFITS:
✅ Menu structure visible in JSON
✅ Easy to understand and modify
✅ Edit JSON, no code changes needed
✅ Single source of truth
```

---

## Data Flow: A - D Artists Example

```
Timeline:
─────────────────────────────────────────────────────────────────

[APP STARTS]
  ↓
  MenuBuilder.load_static_menus()
  ├─ Read menu_config.json
  ├─ Create MenuNode("root")
  ├─ Create MenuNode("music_menu")
  ├─ Create MenuNode("artists_menu")
  │  ├─ Create MenuNode("A - D")  ← Static, from JSON
  │  ├─ Create MenuNode("E - H")  ← Static, from JSON
  │  ├─ Create MenuNode("I - M")  ← Static, from JSON
  │  └─ ...
  └─ Global tree ready for navigation


[USER NAVIGATES]
  ↓
  User selects: "Browse Artists"
  ↓
  Navigator.navigate_to_child("browse_artists")
  ├─ Finds node in tree
  ├─ Sets current_node = artists_menu
  └─ UI shows: [A - D] [E - H] [I - M] [N - R] [S - V] [W - Z]


[USER SELECTS GROUP]
  ↓
  User selects: "A - D"
  ↓
  EventProcessor.process_node_selection(node)
  ├─ Reads payload:
  │  {
  │    "action": "load_dynamic",
  │    "start_letter": "A",
  │    "end_letter": "D"
  │  }
  ├─ This is "load_dynamic" action
  └─ Call DynamicLoader.load_artists_in_range("A", "D")


[DYNAMIC CONTENT LOADED]
  ↓
  DynamicLoader.load_artists_in_range("A", "D")
  ├─ Call Subsonic API with parameters
  ├─ Get actual artists:
  │  [
  │    { id: "123", name: "Abba" },
  │    { id: "124", name: "AC/DC" },
  │    { id: "125", name: "Adams, Ryan" },
  │    ...
  │  ]
  ├─ Create MenuNode for each artist
  ├─ Add as children to "A - D" node
  └─ UI shows: [Abba] [AC/DC] [Adams, Ryan] ...


[USER SELECTS ARTIST]
  ↓
  User selects: "Abba"
  ↓
  EventProcessor.process_node_selection(abba_node)
  ├─ Reads payload: { "action": "browse_albums", "artist_id": "123" }
  ├─ Call Subsonic API for albums
  ├─ Create MenuNodes for albums
  └─ UI shows: [Dancing Queen] [Mamma Mia] ...
```

---

## Key File Updates

### 1. menu_config.json Structure

```
root
  └─ items
      ├─ Music → music_menu
      └─ Chromecasts → chromecasts_menu

music_menu
  └─ items
      ├─ Browse Artists → artists_menu
      └─ Browse Albums → browse_albums action

artists_menu ← NEW! Groups defined here
  └─ items
      ├─ A - D → load_dynamic, start="A", end="D"
      ├─ E - H → load_dynamic, start="E", end="H"
      ├─ I - M → load_dynamic, start="I", end="M"
      ├─ N - R → load_dynamic, start="N", end="R"
      ├─ S - V → load_dynamic, start="S", end="V"
      └─ W - Z → load_dynamic, start="W", end="Z"

chromecasts_menu
  └─ items
      ├─ Living Room → select_device
      ├─ TV Lounge → select_device
      ├─ Signe → select_device
      └─ Bathroom Speaker → select_device
```

### 2. MenuBuilder (Simpler)

```python
# BEFORE: Complex logic to generate groups
def get_alphabetical_groups():
    return [...] # Hard-coded in code

# AFTER: Just load from JSON
def load_static_menus(config):
    for section in config.values():
        for item in section["items"]:
            create_node_from_config(item)  # Pure JSON → Node
```

---

## Advantages Visualized

```
┌─────────────────────────────────────────────────────────────┐
│                     ADVANTAGES                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BEFORE (Code-driven) ❌    │    AFTER (Config-driven) ✅   │
│  ──────────────────────────────────────────────────────────  │
│                            │                                 │
│  Structure in code        │    Structure in JSON             │
│  Hard to see overall      │    Clear overview                │
│  Must edit & redeploy     │    Edit JSON, restart app        │
│  Duplication risk         │    Single source of truth        │
│  Version control messy    │    Config easy to diff           │
│  Manual testing needed    │    Can swap configs easily       │
│                           │                                  │
│  Example change:          │    Example change:               │
│  "Add A-B group"          │    "Add A-B group"               │
│  → Modify code            │    → Edit JSON                   │
│  → Recompile              │    → No code changes             │
│  → Redeploy               │    → Works immediately           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Summary

### What You're Building

```
Component              Purpose                    Status
────────────────────────────────────────────────────────
MenuBuilder            Load JSON → Tree          ✅ Code Ready
MenuNodeNavigator      Navigate tree             ✅ Code Ready
MenuEventProcessor     Extract actions           ✅ Code Ready
DynamicLoader          Fetch API data            ⬜ New (next phase)
───────────────────────────────────────────────────────────
menu_config.json       All static structure      ✅ Updated
```

### What's Different

```
OLD Architecture:
Code (groups) → JSON (trigger) → Service (load) → Tree

NEW Architecture:
JSON (EVERYTHING) → MenuBuilder (load) → Tree
                ↘ DynamicLoader (only for API data)
```

---

## Summary Grid

| Aspect | Value |
|--------|-------|
| **Static menus location** | ✅ JSON file only |
| **Artist groups** | ✅ In JSON (A-D, E-H, etc.) |
| **Devices list** | ✅ In JSON |
| **Navigation logic** | ✅ In Python code |
| **API data loading** | ✅ In Python code (DynamicLoader) |
| **Code complexity** | ✅ Reduced (simpler MenuBuilder) |
| **Configurability** | ✅ Pure JSON config |
| **Extensibility** | ✅ Edit JSON to extend |
| **Testability** | ✅ Test with mock JSON files |

---

## Read Next

- **ARCHITECTURE_CONFIRMED.md** - Final confirmation
- **STATIC_IN_JSON_CLARIFICATION.md** - Detailed explanation
- **MENU_ARCHITECTURE_CLARIFICATION.md** - Deep dive
- **MENU_IMPLEMENTATION_GUIDE.md** - Phase 1 code

---

**Architecture: Confirmed & Ready! 🎉**

