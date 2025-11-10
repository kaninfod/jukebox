# Component Architecture Guide

## Overview

The Jukebox application uses a **component-based architecture** that separates desktop and kiosk interfaces into distinct, reusable components. This enables:

- **Clean separation of concerns** between desktop and kiosk UI
- **Dynamic content loading** in kiosk mode without full page reloads
- **Easier maintenance** with smaller, focused files
- **Better scalability** for adding new features

---

## Folder Structure

```
app/web/
├── routes.py                                  # Route handlers + API endpoints
├── static/
│   ├── css/
│   │   ├── jukebox.css                        # Shared styles
│   │   ├── kiosk.css                          # Kiosk-specific styles
│   │   └── mdi.css                            # Material Design Icons
│   ├── fonts/                                 # Icon fonts
│   └── js/
│       ├── toast.js                           # Toast notifications (shared)
│       └── kiosk-loader.js                    # Dynamic content loader for kiosk
│
└── templates/
    ├── layouts/                               # Base layouts
    │   ├── desktop_base.html                  # Desktop base template
    │   └── kiosk_base.html                    # Kiosk base template (fixed layout)
    │
    ├── components/                            # Reusable components
    │   ├── desktop/
    │   │   └── _navbar.html                   # Desktop navigation bar
    │   │
    │   └── kiosk/
    │       ├── _status_bar.html               # Top status bar (breadcrumb + device)
    │       ├── _navigation.html               # Left sidebar navigation
    │       ├── _controls.html                 # Bottom media controls
    │       ├── _player_status.html            # Player status (album art + track info)
    │       ├── _media_library.html            # Media library browser
    │       ├── _playlist_view.html            # Playlist viewer
    │       ├── _device_selector.html          # Device selection UI
    │       └── _system_menu.html              # System settings menu
    │
    ├── pages/                                 # Full page templates
    │   ├── desktop/
    │   │   └── player.html                    # Desktop player page
    │   │
    │   └── kiosk/
    │       └── player.html                    # Kiosk player page
    │
    ├── _global_styles.html                    # Global CSS/JS includes
    ├── albums.html                            # Desktop albums page
    ├── nfc_encoding_status.html               # Desktop NFC page
    └── subsonic_*.html                        # Desktop subsonic pages
```

---

## Architecture Principles

### 1. **Desktop Mode (Multi-Page)**
- Uses `layouts/desktop_base.html` as base
- Traditional navigation with full page reloads
- Bootstrap cards and responsive grid layout
- Desktop navbar component with Chromecast device selector

### 2. **Kiosk Mode (Single-Page App)**
- Uses `layouts/kiosk_base.html` as base
- **Fixed layout structure** (status bar + nav + content + controls)
- **Dynamic content area** that swaps components without page reload
- Optimized for 720×1280 portrait touchscreen
- Large touch targets, simplified navigation

---

## Kiosk Layout Structure

```
┌─────────────────────────────────────┐
│     Status Bar (50px)               │  ← Breadcrumb + Device Selector
├────┬────────────────────────────────┤
│    │                                │
│ N  │                                │
│ a  │    Dynamic Content Area        │  ← Swappable components
│ v  │    (flex-grow-1)               │
│    │                                │
│ 60 │                                │
│ px │                                │
├────┴────────────────────────────────┤
│     Controls (100px)                │  ← Media buttons (fixed)
└─────────────────────────────────────┘
```

---

## How It Works

### Desktop Flow

1. User navigates to `/status`
2. Route handler serves `pages/desktop/player.html`
3. Template extends `layouts/desktop_base.html`
4. Desktop navbar loaded from `components/desktop/_navbar.html`
5. WebSocket updates track info in real-time

### Kiosk Flow

1. User navigates to `/status?kiosk=1`
2. Route handler serves `pages/kiosk/player.html`
3. Template extends `layouts/kiosk_base.html`
4. Base layout includes:
   - `components/kiosk/_status_bar.html` (top)
   - `components/kiosk/_navigation.html` (left)
   - Dynamic content area (center)
   - `components/kiosk/_controls.html` (bottom)
5. Initial content: `_player_status.html` loaded in center
6. User clicks nav button (e.g., "Library")
7. JavaScript calls `kioskLoader.loadContent('library')`
8. Fetches `/api/kiosk/component/library`
9. Server returns `_media_library.html`
10. JavaScript injects HTML into `#kiosk-content-area`
11. Component-specific initializer runs

**Result**: Navigation, controls, status bar stay visible; only center content changes

---

## Component Details

### Status Bar (`_status_bar.html`)
- **Size**: 50px height
- **Content**: Breadcrumb (left) + Device selector button (right)
- **Styling**: `kiosk-status-bar` class in `kiosk.css`

### Navigation (`_navigation.html`)
- **Size**: 60px width
- **Content**: 3 icon-only buttons (Library, Playlist, System)
- **Behavior**: Calls `navigateTo(section)` → loads component dynamically

### Controls (`_controls.html`)
- **Size**: 100px height
- **Content**: 6 media buttons (prev, play/pause, next, stop, vol-, vol+)
- **Styling**: 80×80px buttons with MDI icons

### Player Status (`_player_status.html`)
- **Layout**: 2-column flex (album art + track info)
- **Album Art**: 280×280px with rounded corners
- **Track Info**: Artist (42px), Title (36px), Album (22px)
- **WebSocket**: Updates in real-time via `updateKioskTrackInfo()`

### Media Library (`_media_library.html`)
- **Content**: Album grid with search bar
- **Behavior**: Click album → play album (future implementation)
- **Initializer**: `initMediaLibrary()` (in kiosk-loader.js)

### Playlist View (`_playlist_view.html`)
- **Content**: List of tracks in current playlist
- **Behavior**: Highlight current track
- **Initializer**: `initPlaylistView()`

### Device Selector (`_device_selector.html`)
- **Content**: List of available Chromecast devices
- **Behavior**: Click device → switch playback
- **Initializer**: `initDeviceSelector()`

### System Menu (`_system_menu.html`)
- **Content**: System info, display settings, power actions
- **Actions**: Exit kiosk, restart, shutdown

---

## Dynamic Content Loading

### JavaScript (`kiosk-loader.js`)

```javascript
class KioskContentLoader {
    async loadContent(componentName) {
        // Fetch component HTML from API
        const response = await fetch(`/api/kiosk/component/${componentName}`);
        const html = await response.text();
        
        // Inject into content area
        this.contentArea.innerHTML = html;
        
        // Initialize component-specific JavaScript
        this.initializeComponent(componentName);
    }
}
```

### API Endpoint (`routes.py`)

```python
@router.get("/api/kiosk/component/{component_name}")
async def get_kiosk_component(component_name: str, request: Request):
    component_map = {
        'player': 'components/kiosk/_player_status.html',
        'library': 'components/kiosk/_media_library.html',
        'playlist': 'components/kiosk/_playlist_view.html',
        'devices': 'components/kiosk/_device_selector.html',
        'system': 'components/kiosk/_system_menu.html',
    }
    
    template_path = component_map.get(component_name)
    return templates.TemplateResponse(template_path, {"request": request})
```

---

## Adding New Components

### 1. Create Component File

```bash
touch app/web/templates/components/kiosk/_my_feature.html
```

### 2. Add to Component Map

In `routes.py`:

```python
component_map = {
    # ... existing entries
    'my_feature': 'components/kiosk/_my_feature.html',
}
```

### 3. Add Navigation Button

In `components/kiosk/_navigation.html`:

```html
<button class="kiosk-nav-btn btn" onclick="navigateTo('my_feature')">
    <i class="mdi mdi-icon-name"></i>
</button>
```

### 4. Add Initializer (if needed)

In `kiosk-loader.js`:

```javascript
initializeComponent(name) {
    switch(name) {
        // ... existing cases
        case 'my_feature':
            this.initMyFeature();
            break;
    }
}

initMyFeature() {
    console.log('My feature initialized');
    // Add event listeners, load data, etc.
}
```

---

## CSS Organization

### Global Styles (`jukebox.css`)
- Shared styles for both desktop and kiosk
- Typography, colors, utilities

### Kiosk Styles (`kiosk.css`)
- **Layout control**: `.kiosk-layout`, fixed positioning
- **Status bar**: `.kiosk-status-bar`, breadcrumb, device selector
- **Navigation**: `.kiosk-nav-sidebar`, `.kiosk-nav-btn`
- **Player status**: `.kiosk-player-status`, `.kiosk-album-art`, `.kiosk-track-details`
- **Controls**: `.kiosk-controls`, `.btn-media-control`
- **Typography**: Large fonts for touchscreen (42px/36px/22px)

---

## Testing Checklist

After making changes:

- [ ] Desktop mode works (`/status`)
- [ ] Kiosk mode works (`/status?kiosk=1`)
- [ ] WebSocket updates both layouts
- [ ] Media controls work
- [ ] Navigation switches components (kiosk)
- [ ] CSS/styles load correctly
- [ ] No console errors
- [ ] Components initialize properly

---

## Best Practices

### Template Files
- Use `{% include 'path/to/component.html' %}` for static includes
- Use API endpoint + JavaScript for dynamic loading
- Keep components self-contained (HTML + inline styles/scripts if needed)
- Use meaningful class names (`.kiosk-*` prefix)

### JavaScript
- Initialize component-specific code in `kiosk-loader.js`
- Use `document.getElementById()` for kiosk elements
- Clean up event listeners when switching components
- Handle errors gracefully (show error message in content area)

### CSS
- Use `!important` sparingly (only when fighting Bootstrap defaults)
- Organize by section (layout → status bar → navigation → etc.)
- Use comments to mark sections
- Test on actual 720×1280 touchscreen

---

## Migration Notes

### What Changed

**Before Refactoring**:
- `mediaplayer_status.html`: 275 lines, desktop + kiosk mixed
- `_base.html`: Conditional kiosk class, both layouts in one file
- `kiosk_styles.css`: All kiosk styles

**After Refactoring**:
- **Layouts**: `desktop_base.html` + `kiosk_base.html` (separate)
- **Desktop**: `pages/desktop/player.html` (clean, focused)
- **Kiosk**: `pages/kiosk/player.html` + 8 component files
- **CSS**: `kiosk.css` (renamed from `kiosk_styles.css`)
- **JavaScript**: `kiosk-loader.js` (dynamic loading)
- **API**: `/api/kiosk/component/{name}` endpoint

### Benefits

✅ **Separation of concerns** - Desktop and kiosk completely independent  
✅ **Reusable components** - Easy to create new kiosk screens  
✅ **Dynamic loading** - SPA-like navigation in kiosk mode  
✅ **Maintainability** - Smaller, focused files  
✅ **Scalability** - Easy to add features  

---

## Troubleshooting

### Component Not Loading
- Check browser console for errors
- Verify component name in `component_map` (routes.py)
- Ensure template path is correct
- Check API endpoint returns HTML (not JSON)

### Styles Not Applied
- Clear browser cache
- Verify `kiosk.css` is loaded (check Network tab)
- Check CSS specificity (use `!important` if needed)
- Ensure `kiosk-layout` class on `<body>`

### JavaScript Errors
- Check `kiosk-loader.js` is loaded
- Verify `kioskLoader` global variable exists
- Check component initializer exists
- Use `console.log()` for debugging

---

## Future Enhancements

- [ ] Component caching (avoid re-fetching)
- [ ] Transitions between components
- [ ] State management (share data between components)
- [ ] Progressive Web App (PWA) for offline support
- [ ] Component lazy loading
- [ ] Error boundaries for failed components

---

**Last Updated**: November 2025  
**Maintained By**: Jukebox Team
