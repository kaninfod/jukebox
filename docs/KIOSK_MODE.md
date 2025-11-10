# Kiosk Mode Implementation

## Overview

The jukebox web application now supports **kiosk mode** - a responsive layout optimized for the 5" DSI touchscreen display (720×1280 pixels) running in Raspberry Pi's graphical environment.

## Key Features

✅ **Single Codebase** - One web app serves both desktop and kiosk displays  
✅ **Responsive Layout** - Automatically adjusts based on `?kiosk=1` parameter  
✅ **Touch-Optimized** - Larger buttons (80×80px) and touch targets  
✅ **Vertical Stack** - Content stacked vertically to fit portrait display  
✅ **Hidden Navigation** - Navbar hidden on kiosk for more screen space  

## Usage

### Desktop Mode (Default)
```
https://jukeplayer.hinge.icu/status
```
- Side-by-side layout (album art | playlist)
- Standard 60×60px buttons
- Full navigation bar

### Kiosk Mode
```
https://jukeplayer.hinge.icu/status?kiosk=1
http://localhost:8000/status?kiosk=1
```
- Stacked vertical layout
- Larger 80×80px touch buttons
- No navigation bar
- Compact spacing

## Testing on Desktop

Before setting up the DSI display, you can test kiosk mode on your desktop:

1. Open browser: `https://jukeplayer.hinge.icu/status?kiosk=1`
2. Open DevTools (F12)
3. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
4. Set custom device: 720×1280 (portrait)
5. Verify layout:
   - Content stacks vertically
   - Buttons are larger
   - Navigation is hidden
   - Playlist is scrollable

## Kiosk Setup on Raspberry Pi

### 1. Install Desktop Environment (if needed)
```bash
sudo apt-get update
sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox
sudo apt-get install chromium-browser
```

### 2. Auto-Start Chromium in Kiosk Mode

Create: `/home/pi/.config/openbox/autostart`
```bash
#!/bin/bash

# Disable screensaver
xset s off
xset -dpms
xset s noblank

# Hide cursor after 5 seconds of inactivity
unclutter -idle 5 &

# Start chromium in kiosk mode
chromium-browser --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  --start-fullscreen \
  http://localhost:8000/status?kiosk=1
```

Make executable:
```bash
chmod +x /home/pi/.config/openbox/autostart
```

### 3. Auto-Login to X Server

Edit `/etc/systemd/system/getty@tty1.service.d/autologin.conf`:
```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM
```

Add to `/home/pi/.bash_profile`:
```bash
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
```

## Layout Differences

### Desktop Layout (≥768px width)
```
┌─────────────────────────────────┐
│  [Navigation Bar]               │
├──────────────┬──────────────────┤
│              │                  │
│  Album Art   │    Playlist      │
│  Track Info  │    (scrollable)  │
│              │                  │
├──────────────┴──────────────────┤
│  [◀] [▶] [▶▶] [⏸] [🔉] [🔊]   │
└─────────────────────────────────┘
```

### Kiosk Layout (720x1280)
```
┌──────────────┐
│              │
│  Album Art   │
│  Track Info  │
│              │
├──────────────┤
│              │
│  Playlist    │
│ (scrollable) │
│              │
├──────────────┤
│ [◀] [▶] [▶▶]│
│ [⏸] [🔉] [🔊]│
└──────────────┘
```

## CSS Implementation

All kiosk-specific styles are centralized in a single CSS file for easy maintenance:

**File:** `app/web/static/css/kiosk_styles.css`

The kiosk mode uses a `.kiosk-layout` class on the `<body>` element to apply specific styles:

```css
/* Hide navigation bar to maximize screen space */
.kiosk-layout .navbar { display: none; }

/* Larger touch-friendly media control buttons */
.kiosk-layout .btn-media-control { 
    width: 80px; 
    height: 80px; 
    font-size: 32px; 
}

/* Stack columns vertically instead of side-by-side */
.kiosk-layout .row { flex-direction: column; }
```

**Benefits of separate CSS file:**
- ✅ Single source of truth for all kiosk styles
- ✅ Works across all pages automatically
- ✅ Easy to maintain and extend
- ✅ No duplicate styles in page templates
- ✅ Can be conditionally loaded if needed

## Backend Implementation

### Route Handler
```python
@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request, kiosk: bool = False):
    return templates.TemplateResponse("mediaplayer_status.html", {
        "request": request,
        "kiosk_mode": kiosk
    })
```

### Template
```html
<body class="{% if kiosk_mode %}kiosk-layout{% endif %}">
```

## Future Enhancements

Potential improvements for kiosk mode:

- [ ] Auto-detect display resolution (no URL parameter needed)
- [ ] Touch gesture support (swipe for next/previous track)
- [ ] Screen timeout/dim controls
- [ ] On-screen keyboard for search
- [ ] Larger album artwork on kiosk
- [ ] Landscape vs portrait orientation detection
- [ ] Optional: NFC reader UI on kiosk display

## Troubleshooting

### Icons not loading
- Verify `/static/css/mdi.css` loads successfully
- Check browser console for CSP violations

### Layout not changing
- Ensure `?kiosk=1` is in URL (or `?kiosk=true`)
- Clear browser cache
- Check DevTools → Elements → `<body>` has `kiosk-layout` class

### Touch not working
- Verify touchscreen drivers installed
- Test with: `xinput list` (should show touchscreen)
- Calibrate if needed: `xinput_calibrator`

### Service won't start
- Restart jukebox: `./jukebox.sh restart`
- Check logs: `journalctl -u jukebox -f`

## Related Documentation

- `QUICK_REFERENCE_CARD.md` - Overall architecture
- `app/web/routes.py` - Route handlers
- `app/web/templates/mediaplayer_status.html` - Main template
- `app/web/templates/_base.html` - Base template with kiosk class
- `app/web/static/css/kiosk_styles.css` - All kiosk-specific CSS styles
