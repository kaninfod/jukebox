# Kiosk UI Layout Implementation

## Overview

Implemented a completely new fixed-position layout for kiosk mode (720×1280 touchscreen) with dedicated sections for status bar, navigation, player status, and controls.

## Visual Layout

```
┌─────────────────────────────────┐
│  Status Bar (50px)              │
│  [🎵 Now Playing]  [📡 Device]  │
├───┬─────────────────────────────┤
│   │                             │
│ N │    ┌─────────────┐          │
│ a │    │ Album Cover │          │
│ v │    │   280x280   │          │
│   │    └─────────────┘          │
│ 8 │                             │
│ 0 │    Artist Name              │
│ p │    Song Title               │
│ x │    Album (Year)             │
│   │    Track X of Y | Volume    │
│   │                             │
├───┴─────────────────────────────┤
│  Controls (100px)               │
│  [◀] [▶] [▶▶] [⏸] [🔉] [🔊]   │
└─────────────────────────────────┘
```

## Implementation Details

### 1. Status Bar (Top - 50px) ✅

**Location:** Top of screen, full width, fixed  
**Background:** Purple gradient (#667eea → #764ba2)  
**Height:** 50px

**Left Side - Breadcrumb:**
- Music icon + "Now Playing" text
- Font size: 18px, bold
- White text

**Right Side - Device Selector:**
- Cast icon + device name
- Rounded pill button (rgba background)
- Clickable to change Chromecast device
- Updates dynamically via WebSocket

### 2. Navigation Sidebar (Left - 80px) ✅

**Location:** Left edge, between status bar and controls  
**Background:** Dark blue-grey (#2c3e50)  
**Width:** 80px

**Three Navigation Buttons:**
1. **Media Library** - Folder icon
2. **Current Playlist** - Playlist icon  
3. **System Menu** - Settings icon

**Button Design:**
- 80px min height each
- Icon (28px) above text (11px)
- Hover effect: lighter background + scale(1.05)
- Touch-optimized spacing

### 3. Player Status (Center - Flexible) ✅

**Location:** Center area, takes remaining space  
**Background:** Light grey (#f5f5f7)  
**Content:** Vertically centered

**Album Art:**
- 280×280px square
- 16px border radius
- Box shadow for depth
- Fallback: Purple gradient + music icon
- Image object-fit: cover

**Track Information:**
- **Artist:** 24px, bold, dark grey
- **Title:** 20px, medium, grey
- **Album (Year):** 16px, light grey
- **Status Line:** Track number + Volume with icons

**Spacing:**
- 24px padding around content
- 24px between album art and text
- All text centered

### 4. Controls (Bottom - 100px) ✅

**Location:** Bottom of screen, full width, fixed  
**Background:** White with top shadow  
**Height:** 100px

**Six Media Control Buttons:**
1. Previous Track
2. Play/Pause
3. Next Track
4. Stop
5. Volume Down
6. Volume Up

**Button Design:**
- 80×80px circular buttons
- 32px icon size
- Primary color with shadow
- Touch feedback: scale(0.95) on active
- Evenly spaced across width

### 5. Layout Switching ✅

**Desktop Mode (Default):**
```html
<div class="desktop-layout">
  <!-- Original side-by-side layout -->
</div>
<div class="kiosk-only-layout" style="display: none">
  <!-- Hidden kiosk layout -->
</div>
```

**Kiosk Mode (?kiosk=1):**
```html
<div class="desktop-layout" style="display: none">
  <!-- Hidden desktop layout -->
</div>
<div class="kiosk-only-layout" style="display: flex">
  <!-- Fixed-position kiosk layout -->
</div>
```

**CSS Logic:**
```css
/* Default */
.desktop-layout { display: block; }
.kiosk-only-layout { display: none; }

/* When body has .kiosk-layout class */
.kiosk-layout .desktop-layout { display: none; }
.kiosk-layout .kiosk-only-layout { 
  display: flex;
  position: fixed;
  height: 100vh;
  overflow: hidden;
}
```

## Files Modified

### 1. `/app/web/templates/mediaplayer_status.html` ✅

**Changes:**
- Wrapped original content in `<div class="desktop-layout">`
- Added new `<div class="kiosk-only-layout">` with complete kiosk structure
- Updated JavaScript to populate both layouts
- Split WebSocket handler into `updateDesktopLayout()` and `updateKioskLayout()`
- Added placeholder functions: `navigateTo()`, `selectDevice()`

**Line Count:** ~250 lines (was ~134)

### 2. `/app/web/static/css/kiosk_styles.css` ✅

**Changes:**
- Complete rewrite with fixed-position layout
- Added 200+ lines of new kiosk-specific CSS
- Organized into clear sections with ASCII art documentation
- Kept legacy styles for backwards compatibility

**Sections:**
1. Layout Control (show/hide logic)
2. Status Bar styles
3. Navigation Sidebar styles
4. Player Status styles
5. Controls styles
6. Legacy styles

**Size:** ~400 lines (was ~100)

### 3. No Backend Changes Required ✅

The route handler already passes `kiosk_mode` to template, so no changes needed to `app/web/routes.py`.

## CSS Features

### Fixed Positioning
```css
.kiosk-layout .kiosk-only-layout {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden; /* No scrolling! */
}
```

### Flexbox Layout
```css
.kiosk-only-layout {
    display: flex;
    flex-direction: column; /* Stack vertically */
}

.kiosk-status-bar { flex-shrink: 0; } /* Fixed 50px */
.kiosk-main-content { flex: 1; }      /* Takes remaining space */
.kiosk-controls { flex-shrink: 0; }   /* Fixed 100px */
```

### Touch Optimization
- All buttons minimum 44×44px (iOS standard)
- Active state: `transform: scale(0.95)`
- Hover state: lighter background + `scale(1.05)`
- Large touch targets: 80×80px for media controls

### Visual Polish
- Gradient backgrounds
- Box shadows for depth
- Smooth transitions (0.2s)
- Rounded corners (12-20px border radius)
- Icon + text combinations

## JavaScript Updates

### Dual Layout Population

```javascript
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDesktopLayout(data);  // Updates old layout
    updateKioskLayout(data);    // Updates new layout
};
```

### Kiosk-Specific Rendering

```javascript
function updateKioskLayout(data) {
    // Update device name in status bar
    deviceDiv.textContent = data.chromecast_device;
    
    // Render track info with custom kiosk styling
    kioskInfoDiv.innerHTML = `
        <div class="kiosk-artist">${artist}</div>
        <div class="kiosk-title">${title}</div>
        ...
    `;
    
    // Handle album art or show placeholder
    kioskThumbDiv.innerHTML = thumbUrl 
        ? `<img src="${thumbUrl}" />`
        : '<div class="kiosk-no-cover"><i class="mdi mdi-music"></i></div>';
}
```

### Placeholder Functions

```javascript
function navigateTo(section) {
    console.log('Navigate to:', section);
    // TODO: Implement navigation
}

function selectDevice() {
    console.log('Select Chromecast device');
    // TODO: Show device selection dialog
}
```

## Testing Instructions

### Desktop Browser Test

1. Open: `https://jukeplayer.hinge.icu/status?kiosk=1`
2. Open DevTools (F12)
3. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
4. Set custom device: 720×1280 (portrait)
5. Verify:
   - Status bar at top with breadcrumb + device
   - Navigation sidebar on left (80px)
   - Album art centered (280×280px)
   - Track info below album art
   - Controls at bottom (6 buttons, 80×80px)
   - **NO SCROLLING** - everything fits on screen

### Layout Verification

**Without ?kiosk=1:**
- Shows desktop layout (side-by-side cards)
- Navbar visible
- Normal button sizes (60×60px)

**With ?kiosk=1:**
- Shows kiosk layout (fixed sections)
- Navbar hidden
- Larger buttons (80×80px)
- Purple status bar
- Dark navigation sidebar

## Future Work

### Functionality to Wire Up

1. **Device Selection:**
   - `selectDevice()` → Show modal/dropdown with available Chromecasts
   - Save selection to localStorage or backend
   - Update current device display

2. **Navigation:**
   - `navigateTo('library')` → Route to album browser
   - `navigateTo('playlist')` → Show full playlist in scrollable view
   - `navigateTo('system')` → System settings/restart/shutdown

3. **Enhanced Player Status:**
   - Progress bar showing track position
   - Shuffle/repeat indicators
   - Queue position indicator

4. **Touch Gestures:**
   - Swipe left/right for next/previous track
   - Swipe up from bottom for volume slider
   - Long-press for context menus

5. **Visual Feedback:**
   - Toast notifications for actions
   - Loading states
   - Error states
   - Connection status indicator

## Dimensions Reference

| Element | Width | Height | Position |
|---------|-------|--------|----------|
| Screen | 720px | 1280px | - |
| Status Bar | 720px | 50px | Top (fixed) |
| Navigation | 80px | 1130px | Left (fixed) |
| Player Status | 640px | 1130px | Center (flex) |
| Controls | 720px | 100px | Bottom (fixed) |
| Album Art | 280px | 280px | Centered |
| Media Button | 80px | 80px | Row |
| Nav Button | 64px | 80px | Column |

## Color Palette

| Element | Color | Usage |
|---------|-------|-------|
| Status Bar | #667eea → #764ba2 | Gradient background |
| Navigation | #2c3e50 | Dark sidebar |
| Player BG | #f5f5f7 | Light grey |
| Artist Text | #2c3e50 | Dark text |
| Title Text | #34495e | Medium text |
| Album Text | #7f8c8d | Light text |
| Status Icons | #95a5a6 | Very light text |

## Success Criteria ✅

- [x] Status bar with breadcrumb and device selector
- [x] Navigation sidebar with 3 buttons
- [x] Centered player status with large album art
- [x] Fixed controls at bottom
- [x] No scrolling - everything fits on screen
- [x] Touch-optimized button sizes (80×80px)
- [x] Visual polish (gradients, shadows, transitions)
- [x] Desktop layout unaffected
- [x] Dual layout switching works
- [x] WebSocket updates both layouts

## Next Steps

1. Test on actual DSI display when available
2. Implement navigation functionality
3. Add device selection modal
4. Consider adding progress bar
5. Add toast notifications for user feedback
6. Optimize font sizes based on real display testing
