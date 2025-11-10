# Kiosk Component-Based Architecture - Refactoring Plan

## Current State Assessment

### Existing Structure
```
app/web/
├── routes.py                      # Route handlers
├── static/
│   ├── css/
│   │   ├── jukebox.css
│   │   ├── kiosk_styles.css
│   │   └── mdi.css
│   ├── fonts/
│   └── js/
│       └── toast.js
└── templates/
    ├── _base.html                 # Base template (shared)
    ├── _navbar.html               # Desktop navbar component
    ├── _global_styles.html        # Global CSS includes
    ├── mediaplayer_status.html    # Player page (BOTH layouts)
    ├── albums.html
    ├── nfc_encoding_status.html
    ├── subsonic_*.html
    └── ...
```

### Current Issues
1. **Mixed Layouts**: Desktop and kiosk layouts are in the SAME template file
2. **No Component Separation**: All kiosk UI elements are inline in one file
3. **Tight Coupling**: Desktop navbar, kiosk nav, controls, and player status are all mixed together
4. **Difficult to Maintain**: Adding new kiosk screens requires duplicating layout structure
5. **No Dynamic Loading**: Can't swap content in player status area without full page reload

## Proposed Architecture

### New Folder Structure

```
app/web/
├── routes.py
├── static/
│   ├── css/
│   │   ├── desktop.css            # Desktop-specific styles
│   │   ├── kiosk.css              # Kiosk-specific styles (renamed from kiosk_styles.css)
│   │   ├── jukebox.css            # Shared styles
│   │   └── mdi.css
│   ├── fonts/
│   └── js/
│       ├── toast.js
│       ├── kiosk-loader.js        # NEW: Dynamic content loading for kiosk
│       └── desktop-loader.js      # NEW: Desktop-specific JS (if needed)
└── templates/
    ├── layouts/                   # NEW: Base layouts
    │   ├── desktop_base.html      # Desktop base layout
    │   └── kiosk_base.html        # Kiosk base layout
    │
    ├── components/                # NEW: Reusable components
    │   ├── desktop/
    │   │   ├── _navbar.html       # Desktop navbar (move from root)
    │   │   └── _footer.html       # Desktop footer (if needed)
    │   │
    │   └── kiosk/
    │       ├── _status_bar.html   # Top status bar (breadcrumb + device selector)
    │       ├── _navigation.html   # Left sidebar navigation
    │       ├── _controls.html     # Bottom media controls
    │       ├── _player_status.html # Player status (album art + track info)
    │       ├── _media_library.html # Media library browser
    │       ├── _playlist_view.html # Playlist viewer
    │       ├── _device_selector.html # Device selection UI
    │       └── _system_menu.html  # System settings menu
    │
    ├── pages/                     # NEW: Full page templates
    │   ├── desktop/
    │   │   ├── player.html        # Desktop player page
    │   │   ├── albums.html
    │   │   ├── artists.html
    │   │   └── nfc.html
    │   │
    │   └── kiosk/
    │       └── player.html        # Kiosk player page (shell only)
    │
    └── _global_styles.html        # Keep global styles
```

## Key Architectural Decisions

### 1. **Separate Base Layouts**
- `layouts/desktop_base.html`: Traditional multi-page navigation
- `layouts/kiosk_base.html`: Fixed layout with dynamic content area

### 2. **Component-Based Kiosk**
Each kiosk component is self-contained:
- Own HTML structure
- Own event handlers (if needed)
- Can be loaded dynamically via AJAX/fetch

### 3. **Dynamic Content Loading**
Instead of navigating to new URLs, kiosk mode will:
- Keep status bar, navigation, and controls FIXED
- Swap content in the center area dynamically
- Use JavaScript to fetch and inject component HTML

### 4. **Shared vs Separate**
- **Shared**: `_global_styles.html`, `toast.js`, WebSocket handlers
- **Desktop**: Multi-page navigation, full page reloads
- **Kiosk**: Single-page app, dynamic content swapping

## Refactoring Steps

### Phase 1: Create New Folder Structure ✅
**Goal**: Set up new directories without breaking existing code

**Actions**:
1. Create `templates/layouts/`
2. Create `templates/components/desktop/`
3. Create `templates/components/kiosk/`
4. Create `templates/pages/desktop/`
5. Create `templates/pages/kiosk/`
6. Create `static/js/kiosk-loader.js` (empty placeholder)

**Impact**: None - just creating directories

---

### Phase 2: Extract Desktop Base Layout ✅
**Goal**: Move desktop-specific layout to new location

**Actions**:
1. Copy `_base.html` → `layouts/desktop_base.html`
2. Move `_navbar.html` → `components/desktop/_navbar.html`
3. Update `desktop_base.html` to reference new navbar path
4. Update all desktop pages to extend `layouts/desktop_base.html`

**Files Modified**:
- `layouts/desktop_base.html` (NEW)
- `components/desktop/_navbar.html` (MOVED)
- `pages/desktop/player.html` (NEW - from mediaplayer_status.html desktop layout)
- `pages/desktop/albums.html` (MOVED)
- `pages/desktop/nfc.html` (MOVED from nfc_encoding_status.html)

**Testing**: Desktop mode should work identically

---

### Phase 3: Create Kiosk Base Layout ✅
**Goal**: Create kiosk-specific base template with fixed structure

**Actions**:
1. Create `layouts/kiosk_base.html` with:
   - Fixed viewport (100vh, no scroll)
   - Include status bar, navigation, content area, controls
   - Define `{% block kiosk_content %}` for dynamic content
2. Add kiosk mode detection (via `kiosk_mode` template variable)

**File**: `layouts/kiosk_base.html`

**Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Kiosk-specific meta, styles -->
</head>
<body class="kiosk-layout">
    {% include 'components/kiosk/_status_bar.html' %}
    <div class="kiosk-main-content d-flex">
        {% include 'components/kiosk/_navigation.html' %}
        <div id="kiosk-content-area" class="flex-grow-1">
            {% block kiosk_content %}{% endblock %}
        </div>
    </div>
    {% include 'components/kiosk/_controls.html' %}
    
    <script src="/static/js/kiosk-loader.js"></script>
</body>
</html>
```

**Testing**: None yet - no pages use it

---

### Phase 4: Extract Kiosk Components ✅
**Goal**: Break kiosk layout into reusable components

**Actions**:
1. Extract from `mediaplayer_status.html` kiosk layout:
   - `_status_bar.html` (breadcrumb + device selector)
   - `_navigation.html` (left sidebar with 3 buttons)
   - `_controls.html` (bottom media controls)
   - `_player_status.html` (album art + track info)

2. Each component should:
   - Be self-contained HTML
   - Include necessary IDs for JavaScript
   - Use Bootstrap classes

**Files Created**:
- `components/kiosk/_status_bar.html`
- `components/kiosk/_navigation.html`
- `components/kiosk/_controls.html`
- `components/kiosk/_player_status.html`

**Testing**: None yet - components not used

---

### Phase 5: Create Kiosk Player Page ✅
**Goal**: Assemble kiosk components into player page

**Actions**:
1. Create `pages/kiosk/player.html`:
   - Extends `layouts/kiosk_base.html`
   - In `{% block kiosk_content %}`, include `_player_status.html`
   - Include WebSocket JavaScript

2. Update route handler to serve correct template:
```python
@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request, kiosk: bool = False):
    if kiosk:
        return templates.TemplateResponse("pages/kiosk/player.html", {
            "request": request,
            "kiosk_mode": True
        })
    else:
        return templates.TemplateResponse("pages/desktop/player.html", {
            "request": request,
            "kiosk_mode": False
        })
```

**Files Modified**:
- `pages/kiosk/player.html` (NEW)
- `routes.py` (UPDATED)

**Testing**: Kiosk mode should work identically to before

---

### Phase 6: Create Additional Kiosk Content Components ✅
**Goal**: Build components for other kiosk screens

**Actions**:
1. Create `components/kiosk/_media_library.html`:
   - Album grid view
   - Touch-optimized album cards
   - Search/filter bar

2. Create `components/kiosk/_playlist_view.html`:
   - Full playlist display
   - Current track highlighting
   - Touch-friendly track selection

3. Create `components/kiosk/_device_selector.html`:
   - List of available Chromecast devices
   - Current device indicator
   - Device switching

4. Create `components/kiosk/_system_menu.html`:
   - System settings
   - Restart/shutdown options
   - Volume/display controls

**Files Created**:
- `components/kiosk/_media_library.html`
- `components/kiosk/_playlist_view.html`
- `components/kiosk/_device_selector.html`
- `components/kiosk/_system_menu.html`

**Testing**: Create test pages to view each component

---

### Phase 7: Implement Dynamic Content Loading ✅
**Goal**: Enable dynamic content swapping without page reload

**Actions**:
1. Create `static/js/kiosk-loader.js`:
```javascript
class KioskContentLoader {
    constructor() {
        this.contentArea = document.getElementById('kiosk-content-area');
        this.currentView = 'player';
    }
    
    async loadContent(componentName) {
        const response = await fetch(`/api/kiosk/component/${componentName}`);
        const html = await response.text();
        this.contentArea.innerHTML = html;
        this.currentView = componentName;
        this.initializeComponent(componentName);
    }
    
    initializeComponent(name) {
        // Initialize component-specific JS (WebSocket, event handlers, etc.)
        switch(name) {
            case 'player':
                initPlayerStatus();
                break;
            case 'playlist':
                initPlaylistView();
                break;
            // ... etc
        }
    }
}

const kioskLoader = new KioskContentLoader();
```

2. Create API endpoint to serve component HTML:
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
    if not template_path:
        raise HTTPException(status_code=404)
    
    return templates.TemplateResponse(template_path, {"request": request})
```

3. Update navigation buttons:
```html
<button onclick="kioskLoader.loadContent('library')">Library</button>
<button onclick="kioskLoader.loadContent('playlist')">Playlist</button>
<button onclick="kioskLoader.loadContent('system')">System</button>
```

**Files Created/Modified**:
- `static/js/kiosk-loader.js` (NEW)
- `routes.py` (ADD endpoint)
- `components/kiosk/_navigation.html` (UPDATE onclick handlers)

**Testing**: Clicking nav buttons should swap content smoothly

---

### Phase 8: Update Styles ✅
**Goal**: Organize CSS into layout-specific files

**Actions**:
1. Rename `static/css/kiosk_styles.css` → `static/css/kiosk.css`
2. Create `static/css/desktop.css` for desktop-specific styles
3. Update base templates to load correct CSS:
   - `desktop_base.html` loads `desktop.css`
   - `kiosk_base.html` loads `kiosk.css`
4. Move shared styles to `jukebox.css`

**Files Modified**:
- `static/css/kiosk.css` (RENAMED)
- `static/css/desktop.css` (NEW)
- `static/css/jukebox.css` (UPDATED)
- `layouts/desktop_base.html` (UPDATE CSS links)
- `layouts/kiosk_base.html` (UPDATE CSS links)

**Testing**: Both layouts should render correctly

---

### Phase 9: Cleanup Old Files ✅
**Goal**: Remove old mixed-mode templates

**Actions**:
1. Delete `mediaplayer_status.html` (replaced by pages/desktop/player.html + pages/kiosk/player.html)
2. Delete old `_navbar.html` from root (moved to components/desktop/)
3. Delete `_base.html` from root (replaced by layouts/desktop_base.html + layouts/kiosk_base.html)
4. Update any remaining references

**Files Deleted**:
- `templates/mediaplayer_status.html`
- `templates/_navbar.html`
- `templates/_base.html`

**Testing**: Full regression test on all pages

---

### Phase 10: Documentation ✅
**Goal**: Document new architecture

**Actions**:
1. Update `KIOSK_MODE.md` with new structure
2. Create `COMPONENT_GUIDE.md` explaining each component
3. Update `QUICK_REFERENCE_CARD.md` with new file locations

**Files Created/Updated**:
- `docs/COMPONENT_ARCHITECTURE.md` (NEW)
- `docs/KIOSK_MODE.md` (UPDATED)
- `docs/QUICK_REFERENCE_CARD.md` (UPDATED)

---

## Benefits of New Architecture

### 1. **Separation of Concerns**
- Desktop and kiosk are completely separate
- Each component has single responsibility
- Easy to modify one without affecting others

### 2. **Reusability**
- Components can be used in different contexts
- Easy to create new kiosk pages
- Shared components reduce duplication

### 3. **Dynamic Content Loading**
- Kiosk behaves like SPA (Single Page App)
- Faster navigation (no full page reload)
- Status bar, nav, controls always visible
- Smooth transitions

### 4. **Maintainability**
- Clear folder structure
- Components are self-contained
- Easy to locate and modify code
- Testing individual components easier

### 5. **Scalability**
- Easy to add new kiosk views
- Just create new component and add nav button
- Can build complex UIs from simple components

## Migration Strategy

### Option A: Big Bang (NOT Recommended)
- Do all phases at once
- High risk of breaking things
- Difficult to test incrementally

### Option B: Incremental (RECOMMENDED)
1. Create new structure alongside old
2. Migrate one page at a time
3. Test thoroughly after each phase
4. Keep old code until new is proven
5. Delete old code only when confident

### Testing Checklist

After each phase:
- ✅ Desktop mode works (`/status`)
- ✅ Kiosk mode works (`/status?kiosk=1`)
- ✅ WebSocket updates both layouts
- ✅ Media controls work
- ✅ Navigation works
- ✅ CSS/styles load correctly
- ✅ No console errors
- ✅ Mobile responsive (if applicable)

## File Size Comparison

### Before Refactoring
```
mediaplayer_status.html: 275 lines (desktop + kiosk + JS)
_base.html: 26 lines (shared)
kiosk_styles.css: 358 lines
```

### After Refactoring
```
layouts/desktop_base.html: ~40 lines
layouts/kiosk_base.html: ~50 lines
pages/desktop/player.html: ~80 lines
pages/kiosk/player.html: ~30 lines
components/kiosk/_status_bar.html: ~20 lines
components/kiosk/_navigation.html: ~15 lines
components/kiosk/_controls.html: ~30 lines
components/kiosk/_player_status.html: ~25 lines
static/js/kiosk-loader.js: ~100 lines
kiosk.css: ~300 lines
```

**Total**: More files, but each is smaller and focused

## Timeline Estimate

Assuming careful, incremental approach:

- **Phase 1-2**: 1 hour (setup + desktop)
- **Phase 3-4**: 2 hours (kiosk base + components)
- **Phase 5**: 1 hour (kiosk player page)
- **Phase 6**: 3 hours (additional components)
- **Phase 7**: 3 hours (dynamic loading + API)
- **Phase 8**: 1 hour (CSS organization)
- **Phase 9**: 1 hour (cleanup)
- **Phase 10**: 1 hour (documentation)

**Total**: ~13 hours of focused work

## Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Test after each phase
- Keep old code until new is proven
- Use feature flags if needed

### Risk 2: Template Path Issues
**Mitigation**:
- Use absolute template paths from root
- Test all includes/extends thoroughly
- Add error handling for missing templates

### Risk 3: JavaScript Complexity
**Mitigation**:
- Start simple, add features incrementally
- Use modern ES6 classes for organization
- Add error handling and logging

### Risk 4: CSS Conflicts
**Mitigation**:
- Use specific class names (e.g., `.kiosk-*`)
- Test both layouts side-by-side
- Use CSS scoping if needed

## Next Steps

1. **Review this plan** - Discuss and adjust
2. **Get approval** - Confirm approach
3. **Create branch** - Don't work on main
4. **Phase 1** - Create folder structure
5. **Test incrementally** - After each phase

## Questions to Answer Before Starting

1. **Routing**: Should kiosk have its own URL prefix (e.g., `/kiosk/player`) or keep `?kiosk=1` parameter?
2. **API Design**: REST endpoints or WebSocket for component loading?
3. **State Management**: How to share state between components (e.g., current device, volume)?
4. **Caching**: Should components be cached client-side?
5. **Fallbacks**: What if JavaScript fails? Server-side rendering fallback?

---

**Ready to start? Let's begin with Phase 1!** 🚀
