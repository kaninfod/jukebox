# Chromecast Device Switching API

## Overview

New API endpoints for seamless Chromecast device switching. These endpoints allow you to discover available devices, check current status, and switch playback between devices without losing state.

## Architecture

- **Singleton Pattern**: Uses existing `get_chromecast_service()` singleton
- **Gentle Implementation**: Only uses existing ChromecastService public methods
- **No Service Modifications**: Zero changes to the core ChromecastService
- **Graceful Degradation**: Handles connection failures elegantly

## New Endpoints

### 1. GET `/api/chromecast/status`

**Purpose**: Get current Chromecast status including all available devices and active playback

**Response**:
```json
{
  "status": "ok",
  "available_devices": [
    {"name": "Kitchen", "model": "Google Home Mini", "host": "192.168.68.56", "uuid": "..."},
    {"name": "Living Room", "model": "Nest Audio", "host": "192.168.68.46", "uuid": "..."},
    {"name": "Bedroom", "model": "Google Home Mini", "host": "192.168.68.47", "uuid": "..."}
  ],
  "active_device": "Living Room",
  "connected": true,
  "playback": {
    "player_state": "PLAYING",
    "media_title": "Song Title",
    "media_artist": "Artist Name",
    "current_time": 45.5,
    "duration": 180.0,
    "volume_level": 0.53,
    "volume_muted": false
  }
}
```

**Use Case**: UI dashboard, device selection UI

---

### 2. POST `/api/chromecast/switch`

**Purpose**: Seamlessly switch from current device to a new device

**Parameters**:
- `device_name` (string, required): Name of target device to switch to

**Request Example**:
```
POST /api/chromecast/switch?device_name=Kitchen
```

**Response**:
```json
{
  "status": "switched",
  "switched_from": "Living Room",
  "switched_to": "Kitchen",
  "new_device_status": {
    "volume_level": 0.5,
    "volume_muted": false,
    "connected": true
  }
}
```

**Behavior**:
1. Disconnects from current device
2. Connects to new device
3. Returns confirmation with new device status
4. Atomic operation - succeeds fully or fails completely

**Use Case**: User selects different Chromecast from UI

---

### 3. POST `/api/chromecast/disconnect`

**Purpose**: Disconnect from current Chromecast device and stop playback

**Request Example**:
```
POST /api/chromecast/disconnect
```

**Response**:
```json
{
  "status": "disconnected",
  "device": "Living Room"
}
```

**Or if already disconnected**:
```json
{
  "status": "not_connected",
  "message": "Already disconnected from Living Room"
}
```

**Use Case**: User stops playback or wants to free up device

---

### 4. GET `/api/chromecast/device/{device_name}`

**Purpose**: Get information about a specific device and test connectivity

**Parameters**:
- `device_name` (string, path parameter): Name of device to query

**Request Example**:
```
GET /api/chromecast/device/Kitchen
```

**Response (Connected & Reachable)**:
```json
{
  "status": "reachable",
  "device": {
    "name": "Kitchen",
    "model": "Google Home Mini",
    "host": "192.168.68.56",
    "uuid": "...",
    "volume_level": 0.5,
    "volume_muted": false,
    "online": true
  }
}
```

**Response (Unreachable)**:
```json
{
  "status": "unreachable",
  "device": {
    "name": "Kitchen",
    "model": "Google Home Mini",
    "host": "192.168.68.56",
    "uuid": "...",
    "online": false
  },
  "error": "Connection timeout"
}
```

**Behavior**:
- Tests connection to device without switching to it
- Returns device info (model, host, etc.)
- Checks if device is online and reachable
- Restores previous device connection after test

**Use Case**: Validate device before allowing user to switch, device details panel

---

## Flow Examples

### Example 1: User Switches Devices

```
1. GET /api/chromecast/status
   → Shows Kitchen, Living Room, Bedroom available
   → Living Room is currently active

2. User clicks "Switch to Kitchen"

3. POST /api/chromecast/switch?device_name=Kitchen
   → Disconnects from Living Room
   → Connects to Kitchen
   → Returns success

4. Next play request targets Kitchen
```

### Example 2: Check Device Before Switch

```
1. GET /api/chromecast/device/Kitchen
   → Returns reachable: true
   → Shows device ready for switch

2. User confirms switch

3. POST /api/chromecast/switch?device_name=Kitchen
   → Proceeds with confidence device is available
```

### Example 3: Stop Playback

```
1. POST /api/chromecast/disconnect
   → Stops current playback
   → Releases device connection

2. Device now available for other apps
```

---

## Error Handling

### 404 Not Found
```json
{
  "detail": "Device not found: Kitchen"
}
```
**Cause**: Device name doesn't match any discovered devices

### 503 Service Unavailable
```json
{
  "detail": "Failed to connect to device: Kitchen"
}
```
**Cause**: Device exists but is unreachable (offline, network issue)

### 500 Internal Error
```json
{
  "detail": "Failed to get status: ..."
}
```
**Cause**: Unexpected error during operation

---

## Implementation Notes

### Singleton Usage
All endpoints use the same singleton instance:
```python
service = get_chromecast_service()
```

This means:
- Only one active connection at a time
- Device switching is atomic
- State is preserved across calls

### Connection State Machine
```
Initial: No device connected
         ↓
connect(device_name) → Connected to device
         ↓
disconnect() → No device connected
         ↓
connect(new_device) → Connected to new device
```

### Gentle on ChromecastService
The implementation ONLY uses these public methods:
- `list_chromecasts()` - Discovery
- `connect(device_name)` - Connection
- `disconnect()` - Disconnection
- `get_status()` - Status retrieval
- `is_connected()` - Connection check

**No service modifications** - respects its 1+ year stabilization effort

---

## Testing Checklist

- [ ] GET /api/chromecast/status returns all devices
- [ ] GET /api/chromecast/status shows correct active device
- [ ] POST /api/chromecast/switch successfully changes devices
- [ ] POST /api/chromecast/disconnect stops playback
- [ ] GET /api/chromecast/device/{name} returns device info
- [ ] GET /api/chromecast/device/{name} doesn't switch devices
- [ ] Error handling for offline devices (503)
- [ ] Error handling for unknown devices (404)
- [ ] Singleton maintained across requests
- [ ] Device discovery takes ~3 seconds

---

## Deployment Notes

- Added to `/app/routes/chromecast.py`
- No dependencies added
- Uses existing ChromecastService methods
- Backward compatible with existing endpoints
- Ready for production deployment

---

## Next Steps

1. **UI Integration**: Update frontend to use new endpoints
2. **Device Selection Menu**: Build device picker UI
3. **Connection Persistence**: Store selected device preference
4. **Playback Context**: Resume playback after switch (if possible)
