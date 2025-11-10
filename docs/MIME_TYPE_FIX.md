# MIME Type Fix for JavaScript Files

## Problem
JavaScript files served from `/static/js/kiosk/*.js` were returning incorrect MIME type:
- **Expected**: `application/javascript` or `text/javascript`
- **Actual**: `application/json`

This caused browsers with strict MIME type checking (`X-Content-Type-Options: nosniff`) to block the files:
```
The resource from 'https://jukeplayer.hinge.icu/static/js/kiosk/player-status.js' 
was blocked due to MIME type ('application/json') mismatch (X-Content-Type-Options: nosniff).
```

## Root Cause
Python's `mimetypes` module doesn't always correctly identify `.js` files, especially on:
- macOS systems
- Systems with custom MIME type configurations
- When certain file metadata is present

## Solution
Created custom `CustomStaticFiles` class that intercepts HTTP responses and fixes MIME types.

### Files Modified

1. **`/app/core/static_files.py`** (NEW)
   - Extended `StaticFiles` with response interception
   - Overrides `__call__` method to wrap the `send` function
   - Explicitly sets Content-Type header based on file extension
   - Uses custom `_get_mime_type()` method with explicit mappings
   - Ensures JavaScript files are always served as `application/javascript`

2. **`/app/main.py`**
   - Changed import from `fastapi.staticfiles.StaticFiles` to `app.core.static_files.CustomStaticFiles`
   - Updated static file mounting to use `CustomStaticFiles(directory=web_static_dir)`

### Implementation Details

```python
# Response interception approach
async def __call__(self, scope: Scope, receive: Receive, send: Send):
    # Get the correct MIME type for the requested file
    correct_mime_type = self._get_mime_type(scope["path"])
    
    # Wrap the send function to modify headers
    async def send_wrapper(message):
        if message["type"] == "http.response.start":
            # Override the content-type header
            headers[b"content-type"] = correct_mime_type.encode()
        await send(message)
    
    # Call parent with our wrapper
    await super().__call__(scope, receive, send_wrapper)
```

This ensures the Content-Type header is always set correctly, regardless of what Python's mimetypes module returns.

## Additional Cleanup
Removed macOS extended attribute files (`._*.js`) from `/static/js/kiosk/` directory:
```bash
rm -f /Volumes/shared/jukebox/app/web/static/js/kiosk/._*.js
```

## Testing
After deploying these changes:

1. **Restart the FastAPI server** to load the new `CustomStaticFiles` class
2. **Clear browser cache** or do hard reload (Cmd+Shift+R / Ctrl+Shift+F5)
3. **Verify MIME types** with browser DevTools Network tab
4. **Test all kiosk components**:
   - Player status (live track updates)
   - Playlist view (WebSocket updates)
   - Media library (navigation)
   - Device selector (Chromecast switching)
   - System menu (restart/reboot/shutdown)

## Expected Outcome
All JavaScript files should now:
- Return `Content-Type: application/javascript`
- Load successfully in browsers with strict MIME checking
- Execute properly to initialize kiosk components

## Rollback Plan
If issues occur, revert both changes:
```python
# In app/main.py
from fastapi.staticfiles import StaticFiles  # Restore original import
app.mount("/static", StaticFiles(directory=web_static_dir), name="web_static")
```

## Future Improvements
Consider:
- Adding more MIME types as needed
- Monitoring for any other MIME type issues
- Potentially using nginx/Apache in production for static file serving
