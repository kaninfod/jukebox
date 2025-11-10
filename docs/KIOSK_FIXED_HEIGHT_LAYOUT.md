# Kiosk Layout Fixed Height Implementation

## Problem
The controls were not staying at the bottom of the 720px kiosk screen because flex layout with `vh` units wasn't reliable.

## Solution
**Fixed pixel-based layout** - All components sized to exactly 720px total.

## Layout Math

```
Status Bar:    50px
Main Content: 570px  (720 - 50 - 100)
Controls:     100px
─────────────────
TOTAL:        720px ✅
```

## Changes Made

### 1. kiosk.css - Fixed Sizing
```css
/* HTML and Body: Exact 720px height */
html.kiosk-mode,
body.kiosk-layout {
    width: 1280px !important;  /* Landscape width */
    height: 720px !important;  /* Landscape height - FIXED */
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Status Bar: Fixed 50px */
.kiosk-status-bar {
    height: 50px;
    flex-shrink: 0;
}

/* Main Content: Fixed 570px */
.kiosk-main-content {
    height: 570px !important;
    display: flex;
    overflow: hidden;
}

/* Controls: Fixed 100px */
.kiosk-controls {
    height: 100px;
    flex-shrink: 0;
}
```

### 2. kiosk_base.html - Added Class
```html
<html lang="en" class="kiosk-mode">
```

## Component Breakdown

### Status Bar (50px)
- Breadcrumb (left)
- Device selector (right)
- No scrolling

### Main Content (570px)
- Navigation sidebar: 60px width
- Content area: Remaining width (1220px)
- Overflow: hidden

### Controls (100px)
- 6 buttons (80×80px each)
- Evenly spaced
- No scrolling

## Benefits

✅ **No more flex calculation issues** - Exact pixel sizing  
✅ **No viewport dependencies** - Works regardless of browser  
✅ **Predictable layout** - Always fits 720px screen  
✅ **No overflow** - Components sized to fit perfectly  

## Testing

1. Navigate to `/status?kiosk=1`
2. Controls should be at bottom edge
3. No scroll bars should appear
4. Total height should be exactly 720px

---

**Date**: November 7, 2025  
**Status**: ✅ Complete
