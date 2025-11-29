# Race Condition Fix - player-status.js

## Issue Identified

**Root Cause:** Mismatched data structures between WebSocket and API endpoints

### The Problem (from real logs):

```timeline
[11:57:13.513] WS: current_track update received: {current_track: {...}, playlist: [...], ...}
[11:57:13.513] UPDATE: Track info rendered successfully ✅ (WebSocket data works!)

[11:57:13.503] INIT: API response received: {type: 'current_track', payload: {...}}
[11:57:13.521] UPDATE: Received data: {type: 'current_track', payload: {...}}
[11:57:13.521] UPDATE: Data structure - has current_track: false, has playlist: false ❌
[11:57:13.521] UPDATE: No current_track in data. data.message: "undefined" ❌ (Overwrites good render!)
```

### Why This Happens:

The **WebSocket** and **API** return data in different envelope formats:

**WebSocket Message:**
```javascript
{
  current_track: { artist: "...", title: "...", ... },
  playlist: [...],
  status: "playing",
  volume: 40,
  chromecast_device: "..."
}
```

**API Response (GET /api/mediaplayer/status):**
```javascript
{
  type: "current_track",
  payload: {
    current_track: { artist: "...", title: "...", ... },
    playlist: [...],
    status: "playing",
    volume: 40,
    chromecast_device: "..."
  }
}
```

When the API response (arriving later) overwrites the WS render, it passes the envelope structure to `updateKioskTrackInfo()`. The function can't find `data.current_track` (it's at `data.payload.current_track`), so it renders "No track loaded".

---

## Solution Implemented

### Changed: `initPlayerStatus()` function

**Before:**
```javascript
const data = await response.json();
console.log(`[${respTimestamp}] INIT: API response received:`, data);
updateKioskTrackInfo(data);  // ❌ Passes envelope, not payload
```

**After:**
```javascript
const data = await response.json();
console.log(`[${respTimestamp}] INIT: API response received (raw):`, data);

// Unwrap API envelope if present (API returns {type, payload} but we need just the payload)
const payloadData = (data.type && data.payload) ? data.payload : data;
console.log(`[${respTimestamp}] INIT: API response unwrapped:`, payloadData);

updateKioskTrackInfo(payloadData);  // ✅ Passes payload in correct format
```

### How It Works:

1. **Check** if response has `type` and `payload` properties
2. **Extract** the payload if envelope is present
3. **Fall back** to raw data if no envelope (backwards compatible)
4. **Pass** the unwrapped payload to `updateKioskTrackInfo()`

Now both WebSocket and API data arrive in the same structure format.

---

## Testing

After this fix:

1. **Fresh page load**: Should display track immediately without "No track loaded"
2. **Album change**: UI should update smoothly without brief "No track loaded" flash
3. **Page refresh**: Album data should persist and render correctly
4. **Console logs**: Should show API response unwrapped and rendering successfully

### Expected Console Output After Fix:

```
[HH:MM:SS.xxx] INIT: API response received (raw): {type: 'current_track', payload: {...}}
[HH:MM:SS.xxx] INIT: API response unwrapped: {current_track: {...}, playlist: [...], ...}
[HH:MM:SS.xxx] UPDATE: Track info rendered successfully ✅
```

---

## Why This Wasn't Caught Before

The WebSocket arrives first and renders correctly, so users rarely see the issue **unless**:
- Network is slow and API response significantly delayed
- Page is refreshed (no WS message yet, only API)
- User navigates away and back (component reloads)
- Rapid album changes cause timing conflicts

The logging revealed the issue by showing the **exact timing** and **data structure mismatches** between the two sources.

---

## Related Files

- **Modified**: `/Volumes/jukeplayer/jukebox/app/web/static/js/kiosk/player-status.js`
- **API Endpoint**: `/app/routes/mediaplayer.py` line 182 (GET /api/mediaplayer/status)
- **WebSocket Handler**: `/app/routes/mediaplayer.py` line 199+ (WS /ws/mediaplayer/status)
- **Documentation**: `/Volumes/jukeplayer/jukebox/docs/RACE_CONDITION_LOGGING_ANALYSIS.md`

---

## Backwards Compatibility

The fix is **backwards compatible**:
- If data has `{type, payload}` structure → extracts payload
- If data is already unwrapped → uses as-is
- Works with both WebSocket and API responses

