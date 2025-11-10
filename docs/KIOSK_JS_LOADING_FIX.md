# Kiosk JavaScript Loading Fix

## Problem
After refactoring kiosk components to use external JavaScript files, the scripts weren't loading when components were dynamically loaded via `innerHTML`. This caused:
- Media library hanging/not responding
- No functionality in any dynamically loaded component
- Browser logs showing "Navigate to: library" but no errors

## Root Cause
When HTML is inserted via `innerHTML`, browsers **do not execute** `<script>` tags (even with `src` attributes) for security reasons. Our refactored components had `<script src="...">` tags that were being stripped/ignored.

## Solution: Load All Scripts Upfront

Instead of trying to dynamically load scripts, we now load all kiosk component JavaScript files in the base template. This is simpler, better for caching, and avoids the innerHTML security restriction.

### Changes Made

#### 1. `/app/web/templates/layouts/kiosk_base.html`
**Added** all component scripts to the base template (after kiosk-loader.js):
```html
<!-- Load all kiosk component scripts upfront (small files, better for caching) -->
<script src="/static/js/kiosk/player-status.js"></script>
<script src="/static/js/kiosk/playlist-view.js"></script>
<script src="/static/js/kiosk/media-library.js"></script>
<script src="/static/js/kiosk/device-selector.js"></script>
<script src="/static/js/kiosk/system-menu.js"></script>
```

#### 2. Component Templates (5 files)
**Removed** `<script>` tags from all component templates:
- `/app/web/templates/components/kiosk/_player_status.html`
- `/app/web/templates/components/kiosk/_playlist_view.html`
- `/app/web/templates/components/kiosk/_media_library.html`
- `/app/web/templates/components/kiosk/_device_selector.html`
- `/app/web/templates/components/kiosk/_system_menu.html`

#### 3. `/app/web/static/js/kiosk-loader.js`
**Simplified** `loadContent()` method - removed script extraction logic:
```javascript
async loadContent(componentName) {
    const response = await fetch(`/api/kiosk/component/${componentName}`);
    const html = await response.text();
    
    // Set the HTML content (scripts are already loaded in base template)
    this.contentArea.innerHTML = html;
    
    this.currentView = componentName;
    this.initializeComponent(componentName);
}
```

#### 4. `/app/main.py`
**Reverted** to standard `StaticFiles` (removed CustomStaticFiles):
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=web_static_dir), name="web_static")
app.mount("/album_covers", StaticFiles(directory=album_cover_dir), name="album_covers")
app.mount("/assets", StaticFiles(directory=album_cover_dir), name="assets")
```

## Benefits

1. **Simpler Architecture**: No complex script extraction/injection logic
2. **Better Caching**: All scripts loaded once, cached by browser
3. **Faster Navigation**: No script loading delay when switching views
4. **Standard FastAPI**: Uses stock StaticFiles (no custom middleware needed)
5. **Reliable**: Avoids innerHTML security restrictions

## File Summary

| File | Change |
|------|--------|
| `kiosk_base.html` | Added 5 script tags |
| `_player_status.html` | Removed 1 script tag |
| `_playlist_view.html` | Removed 1 script tag |
| `_media_library.html` | Removed 1 script tag |
| `_device_selector.html` | Removed 1 script tag |
| `_system_menu.html` | Removed 1 script tag |
| `kiosk-loader.js` | Simplified (removed 20+ lines) |
| `main.py` | Reverted to StaticFiles |
| `static_files.py` | No longer needed (can be deleted) |

## Total Impact
- **JavaScript files**: 5 files (640 lines) remain unchanged
- **HTML changes**: 6 files modified
- **JS changes**: 1 file simplified
- **Python changes**: 1 file reverted to standard

## Testing Checklist
After restart:
- [ ] Browser requests `/static/js/kiosk/*.js` files on page load
- [ ] All 5 JavaScript files return `200 OK` with `application/javascript` MIME type
- [ ] Player status displays current track
- [ ] Playlist view loads and updates via WebSocket
- [ ] Media library navigation works (groups → artists → albums)
- [ ] Device selector shows Chromecast devices
- [ ] System menu functions work (exit/restart/reboot/shutdown)

## Why This Approach?

**Alternative considered**: Dynamic script loading with `document.createElement('script')`
- **Rejected**: Complex, error-prone, slower, harder to debug

**Chosen approach**: Load all scripts upfront
- ✅ Simple and standard
- ✅ Better browser caching
- ✅ No dynamic script injection security concerns
- ✅ Faster perceived performance (no loading delay between views)
- ✅ Total size: ~25KB (5 small files) - negligible on modern connections
