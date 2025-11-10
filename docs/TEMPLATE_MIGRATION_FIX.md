# Template Migration Fix

## Issue
After refactoring, desktop pages were failing with:
```
jinja2.exceptions.TemplateNotFound: '_base.html' not found in search path: 'app/web/templates'
```

## Root Cause
Several templates were still referencing the deleted `_base.html` and `_navbar.html` files:
- `subsonic_artists.html`
- `subsonic_albums.html`  
- `subsonic_album_songs.html`
- `albums.html`
- `nfc_encoding_status.html`

## Fix Applied

### Templates Extending `_base.html`
Updated to extend `layouts/desktop_base.html`:
- ✅ `subsonic_artists.html`
- ✅ `subsonic_albums.html`
- ✅ `subsonic_album_songs.html`

### Templates with Standalone HTML
Updated navbar import path from `_navbar.html` to `components/desktop/_navbar.html`:
- ✅ `albums.html`
- ✅ `nfc_encoding_status.html`

## Changes Made

### subsonic_artists.html
```diff
- {% extends "_base.html" %}
+ {% extends "layouts/desktop_base.html" %}
```

### subsonic_albums.html
```diff
- {% extends "_base.html" %}
+ {% extends "layouts/desktop_base.html" %}
```

### subsonic_album_songs.html
```diff
- {% extends "_base.html" %}
+ {% extends "layouts/desktop_base.html" %}
```

### albums.html
```diff
- {% from '_navbar.html' import navbar %}
+ {% from 'components/desktop/_navbar.html' import navbar %}
```

### nfc_encoding_status.html
```diff
- {% from '_navbar.html' import navbar %}
+ {% from 'components/desktop/_navbar.html' import navbar %}
```

## Status
✅ **All templates migrated successfully**  
✅ **Desktop navigation should work**  
✅ **No more references to deleted files**

## Testing
Test these desktop pages:
- `/status` - Player page
- `/library/artists` - Subsonic artists
- `/albums` - Local album catalog
- `/nfc` - NFC encoding status

All should now load without errors!
