# Quick Reference: HomeScreen Refactoring Changes

## The Core Change: Direct Player Access

### **Import Addition**
```python
from app.core.service_container import get_service
```

### **State Variables: Context → Cache**

**Before:**
```python
self.context = {}
self.current_track = None
self.volume = 25
self.player_status = PlayerStatus.STANDBY
self.artist_name = "Unknown Artist"
self.album_name = "Unknown Album"
self.album_year = "----"
self.track_title = "No Track"
self.album_id = None
self.cc_device = "No Device"
```

**After:**
```python
# Cache for display values - updated on each draw() from player
self._volume = 25
self._player_status = PlayerStatus.STANDBY
self._artist_name = "Unknown Artist"
self._album_name = "Unknown Album"
self._album_year = "----"
self._track_title = "No Track"
self._album_id = None
self._cc_device = "No Device"
```

**Why**: Underscore prefix signals "internal cache, not source of truth"

---

## The Draw Method: Event-Based → Player-Based

### **Before: Hope Context is Current**
```python
def draw(self, draw_context, fonts, context=None, image=None):
    self.context = context
    if self.context is not None:
        self._set_context(context)  # ← Depends on timely event
    # ... use potentially stale self.artist_name, etc.
```

### **After: Fetch Fresh State**
```python
def draw(self, draw_context, fonts, context=None, image=None):
    """Draw with live data from MediaPlayer - always current!"""
    
    try:
        player = get_service("jukebox_mediaplayer")
        if player:
            current_track = player.current_track
            if current_track:
                self._artist_name = current_track.get('artist', 'Unknown Artist')
                self._track_title = current_track.get('title', 'No Track')
                self._album_id = current_track.get('album_cover_filename')
                self._album_name = current_track.get('album', 'Unknown Album')
                self._album_year = str(current_track.get('year', '----'))
            else:
                # No track playing
                self._artist_name = 'Unknown Artist'
                self._track_title = 'No Track'
                # ... etc
            
            # Get other properties
            self._volume = player.volume if player.volume is not None else 25
            self._player_status = player.status if player.status else PlayerStatus.STANDBY
            try:
                self._cc_device = player.cc_service.device_name if player.cc_service else 'No Device'
            except Exception:
                self._cc_device = 'No Device'
        else:
            self._use_defaults()
    except Exception as e:
        logger.warning(f"Error fetching player state: {e}, using defaults")
        self._use_defaults()
    
    # ... render with guaranteed fresh data
```

**Why**: No timing dependencies. Data fetched at render time.

---

## Removed: `_set_context()` Method

**What was deleted:**
```python
def _set_context(self, context):
    self.current_track = context.get('current_track', {})
    if self.current_track:
        self.artist_name = self.current_track.get('artist', 'Unknown Artist')
        # ... more mapping
    else:
        self.artist_name = 'Unknown Artist'
        # ... defaults
    
    self.player_status = PlayerStatus(context.get('status', PlayerStatus.STANDBY.value))
    self.volume = context.get('volume', 0)
```

**Replaced by:**
```python
def _use_defaults(self):
    """Set display values to safe defaults when player data unavailable."""
    self._artist_name = 'Unknown Artist'
    self._track_title = 'No Track'
    self._album_id = None
    self._album_name = 'Unknown Album'
    self._album_year = '----'
    self._cc_device = 'No Device'
    self._volume = 0
    self._player_status = PlayerStatus.STANDBY
```

**Why**: Simpler, only used as fallback. Main path queries player directly.

---

## Updated Variable Names Throughout Draw

All references to display state updated from `self.X` to `self._X`:

```python
# Before
album_with_year = f"{self.album_name} ({self.album_year})"
volume_value_element = TextElement(..., f"{self.volume}%", ...)
path = self._get_icon_filename()  # uses self.player_status

# After
album_with_year = f"{self._album_name} ({self._album_year})"
volume_value_element = TextElement(..., f"{self._volume}%", ...)
path = self._get_icon_filename()  # uses self._player_status
```

---

## Bug Fix: Dirty Flag in ScreenManager

**File**: `app/ui/manager.py`, line 150

**Before:**
```python
self.current_screen.dirty = True  # ❌ Always marks as dirty!
```

**After:**
```python
self.current_screen.dirty = False  # ✅ Mark as clean after rendering
```

**Impact**: Screens won't re-render unnecessarily.

---

## Documentation: ScreenQueue Fallback

**File**: `app/ui/screen_queue.py`

Added comment explaining that empty context is fine:
```python
def _show_fallback_screen(self):
    # Note: HomeScreen now fetches fresh data directly from MediaPlayer,
    # so passing empty context is fine - it will query player.current_track, etc.
    if self.screen_manager.is_music_playing():
        logger.info("[ScreenQueue] Fallback: Showing home screen (music playing)")
        self.screen_manager.show_home_screen({})  # ← Empty dict is OK
```

---

## Summary: 3 Files, 3 Changes

| File | Change | Type |
|------|--------|------|
| `app/ui/screens/home.py` | HomeScreen: event-based → player-based | Refactor |
| `app/ui/manager.py` | Fix: `dirty = True` → `dirty = False` | Bug Fix |
| `app/ui/screen_queue.py` | Add clarifying comment | Documentation |

---

## Before/After Scenario: Album Load

### **BEFORE** (Event-Based):
```
T=0ms:    User scans RFID
T=1ms:    PlaybackManager.load_from_album_id()
T=2ms:    player.play() called
T=5ms:    Player emits STATUS_CHANGED
T=10ms:   ScreenManager queues "home" with player.get_context()
T=15ms:   Message "Album Loaded" displays
T=3015ms: Message times out
T=3020ms: HomeScreen._set_context() called with OLD context
T=3021ms: Display shows STALE album info momentarily 😞
T=3500ms: Another event arrives, display updates (finally)
```

Problem: Data is stale when home screen displays.

### **AFTER** (Direct Queries):
```
T=0ms:    User scans RFID
T=1ms:    PlaybackManager.load_from_album_id()
T=2ms:    player.play() called (player.current_track is NOW current)
T=5ms:    Player emits STATUS_CHANGED (but HomeScreen doesn't care)
T=10ms:   ScreenManager queues "home"
T=15ms:   Message "Album Loaded" displays
T=3015ms: Message times out
T=3020ms: HomeScreen.draw() calls player = get_service(...)
T=3021ms: current_track = player.current_track (FRESH! ✅)
T=3022ms: Display shows CORRECT album info immediately 😊
```

Benefit: Data always fresh, no timing issues.

---

## Testing Tip

**Monitor logs for this pattern:**
```
[ScreenQueue] Displaying screen: message (duration: 3.0s)
[ScreenQueue] Sleeping for 3.0s after showing message
[ScreenQueue] Queue empty. Showing fallback screen.
[ScreenQueue] Fallback: Showing home screen (music playing)
HomeScreen.draw() - fetching fresh player state
🖥️  SCREEN CHANGED SUCCESSFULLY: Home Screen
```

If you see `Error fetching player state`, the fallback works—displays defaults instead of crashing.

---

## Success Indicators

✅ **You'll know it's working when:**
1. Load album → Message shows → Home screen displays **immediately** with correct data
2. No momentary stale data display
3. Cover images update
4. Track title, artist, album all correct
5. Volume bar reflects actual volume
6. Status icon (play/pause/stop) matches actual state

**Expected behavior**: Seamless, synchronized home screen that always reflects actual player state.
