# Race Condition Logging Analysis - player-status.js

## Overview
Enhanced `player-status.js` with comprehensive timestamped logging to diagnose race condition issues where album data fails to display (shows "No track loaded" or null fields despite correct data in console logs).

## What Changed

### 1. Enhanced `safeInit()` Function
**Purpose**: Track when DOM elements become available
```javascript
- Logs timestamp when called
- Checks if kiosk-track-info element exists
- Logs error if element not found (component not loaded)
```

### 2. Enhanced `updateKioskTrackInfo()` Function
**Purpose**: Track data flow and validation
```javascript
- Logs timestamp and received data structure
- Validates data has current_track and playlist
- Checks DOM elements exist before updating
- Logs each field being set (device, volume, track info)
- Validates required fields (artist, album, year) before rendering
- Logs specific null/missing fields when rendering fails
- Shows whether album art URL exists and loads
```

### 3. Enhanced Module Initialization (IIFE)
**Purpose**: Track script loading and setup
```javascript
- Logs when module starts loading
- Records document.readyState at module load time
- Tracks apiReady and wsReady state flags
- Logs WebSocket URL and connection attempts
- Logs when WebSocket opens/errors/receives messages
- Correlates API and WS readiness with update attempts
```

### 4. Enhanced `initPlayerStatus()` Function
**Purpose**: Track API fetch and data rendering
```javascript
- Logs when function called
- Logs when API response received
- Sets apiReady = true after successful update
- Logs API errors with status codes
```

### 5. Enhanced WebSocket Handlers
**Purpose**: Track incoming messages and timing
```javascript
- ws.onopen: Logs connection established, sets wsReady = true
- ws.onerror: Logs connection errors
- ws.onmessage: Logs message received with apiReady/wsReady state
  - Logs message type (ping, error, notification, current_track)
  - Validates payload structure
  - Shows if updateKioskTrackInfo function exists
```

## Console Log Format

All logs use a consistent timestamp format with millisecond precision:
```
[HH:MM:SS.mmm] CATEGORY: Message details
```

Categories:
- `INIT` - Initialization and setup
- `WS` - WebSocket operations
- `UPDATE` - updateKioskTrackInfo operations

## How to Use the Logs

### Scenario 1: "No track loaded" appearing on fresh page load

Look for this sequence:
```
[HH:MM:SS.000] INIT: player-status.js module loading
[HH:MM:SS.001] INIT: document.readyState = "loading"
[HH:MM:SS.002] WS: Creating WebSocket connection to: wss://...
[HH:MM:SS.003] INIT: document.readyState is "loading", waiting for DOMContentLoaded
[HH:MM:SS.100] WS: WebSocket connected, wsReady = true
[HH:MM:SS.200] INIT: DOMContentLoaded fired, calling safeInit()
[HH:MM:SS.201] INIT: safeInit() called. kiosk-track-info element exists: true
[HH:MM:SS.202] INIT: DOM ready, calling window.initPlayerStatus()
[HH:MM:SS.203] INIT: initPlayerStatus() called
[HH:MM:SS.350] INIT: API response received: {...}
[HH:MM:SS.351] UPDATE: Received data: {...}
[HH:MM:SS.352] UPDATE: DOM elements - info: true, thumb: true, ...
```

**If** you see "UPDATE: Early return - DOM elements not found":
- Component template not loaded yet when WebSocket message arrived
- Race condition: WS message before component HTML inserted

**If** you see "UPDATE: MISSING REQUIRED FIELDS":
- API returned incomplete data
- Some fields (artist, album, year, playlist) are null/undefined
- Check backend API response structure

### Scenario 2: Album data appears then disappears

Look for multiple UPDATE calls with different data:
```
[HH:MM:SS.100] UPDATE: Track info rendered successfully
[HH:MM:SS.200] WS: current_track update received: {...}
[HH:MM:SS.201] UPDATE: Received data: {...}
[HH:MM:SS.202] UPDATE: No current_track in data. data.message: "..."
```

**Indicates**: WebSocket message with no current_track arrived after initial render
- Could be from transitioning between albums
- Could be server sending incomplete state update

### Scenario 3: DOM elements not found

Look for:
```
[HH:MM:SS.201] INIT: safeInit() called. kiosk-track-info element exists: false
[HH:MM:SS.202] INIT: kiosk-track-info element NOT FOUND - component may not be loaded
```

**Indicates**: Component template wasn't rendered when script tried to initialize
- kiosk-loader might not have inserted `_player_status.html` yet
- Component initialization race with DOM loading

## Key State Flags

The logs track two boolean flags:
- `apiReady`: Set to true after initial API call succeeds
- `wsReady`: Set to true after WebSocket connects

These appear in WS message logs to show readiness state:
```
[HH:MM:SS.350] WS: Message received. apiReady: true, wsReady: true
```

If you see `apiReady: false` when processing WS messages, it means WebSocket beat the API call.

## Debugging Workflow

1. **Open browser DevTools Console** (F12)
2. **Navigate to kiosk player page** (or refresh)
3. **Watch the timestamp sequence** for any gaps or unexpected ordering
4. **Look for Early return or MISSING REQUIRED FIELDS** errors
5. **Check if multiple UPDATE calls** occur for same/different data
6. **Note any "element not found"** messages

## Performance Observations

You can use these logs to measure:
- **Module load to WebSocket connect**: Time between first INIT log and "WS: WebSocket connected"
- **Module load to DOMContentLoaded**: Time between first INIT log and "DOMContentLoaded fired"
- **DOMContentLoaded to API response**: Time between "DOMContentLoaded fired" and "INIT: API response received"
- **Total time to first render**: Time between "INIT: initPlayerStatus() called" and "UPDATE: Track info rendered successfully"

## Next Steps After Analysis

Once you run this with fresh logs, share:
1. The complete timestamp sequence from browser console
2. Any "Early return", "MISSING REQUIRED FIELDS", or "element not found" errors
3. Whether multiple UPDATE calls occur
4. How the timing relates to when "No track loaded" appears

This will help identify:
- Whether issue is WebSocket vs. API timing
- Whether backend API returns incomplete data
- Whether component template loads before script initialization
- Whether rapid refreshes cause state conflicts

