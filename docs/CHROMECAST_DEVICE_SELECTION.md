# Chromecast Device Selection Implementation

## Overview
Implemented dynamic Chromecast device selection through the jukebox menu system, allowing users to switch between different Chromecast devices at runtime.

## Features Implemented

### 1. Menu System Integration
- **Location**: Main Menu → Chromecasts
- **Device List**: Pre-configured devices in menu adapters:
  - Living Room (default)
  - TV Lounge
  - Signe
  - Bathroom Speaker

### 2. Visual Indicators
- **Current Device**: Shows with 🔗 icon and "(Current)" label
- **Other Devices**: Shows with ⚪ icon
- **Separator**: Visual separation between device list and controls
- **Additional Options**: Status check and volume control access

### 3. Event-Driven Architecture
- **New Event Type**: `CHROMECAST_DEVICE_CHANGED`
- **Event Flow**:
  1. User selects device from menu
  2. Menu controller emits `CHROMECAST_DEVICE_CHANGED` event
  3. PlaybackManager handles device switching
  4. User gets visual feedback via messages

### 4. Error Handling
- **Offline Devices**: Shows error message if device connection fails
- **Graceful Fallback**: Maintains current device if switch fails
- **User Feedback**: Clear success/error messages displayed

## Files Modified

### Core Event System
- `app/core/event_factory.py`: Added `CHROMECAST_DEVICE_CHANGED` event type

### Menu System
- `app/ui/menu/menu_adapter.py`: Updated `create_chromecasts_menu()` with device list
- `app/ui/menu/subsonic_config_adapter.py`: Updated `create_chromecasts_menu()` with device list
- `app/ui/menu/menu_controller.py`: Added handlers for:
  - `select_chromecast_device`
  - `chromecast_status`
  - `chromecast_volume_control`
  - `separator` (no-op)

### Playback Management
- `app/services/playback_manager.py`: Added `_handle_chromecast_device_change()` method

## User Workflow

1. **Access Menu**: User navigates to Main Menu → Chromecasts
2. **View Devices**: See list of 4 configured Chromecast devices
3. **Current Device**: Clearly marked with icon and label
4. **Select Device**: Choose different device from list
5. **Feedback**: Get immediate visual confirmation of switch
6. **Error Handling**: If device is offline, receive error message and instruction to try another device

## Technical Implementation

### Device Configuration
```python
chromecast_devices = [
    "Living Room",
    "TV Lounge", 
    "Signe",
    "Bathroom Speaker"
]
```

### Event Emission
```python
event_bus.emit(Event(
    type=EventType.CHROMECAST_DEVICE_CHANGED,
    payload={"device_name": device_name}
))
```

### Device Switching
```python
new_chromecast_service = PyChromecastServiceOnDemand(device_name)
self.player.cc_service = new_chromecast_service
self.player.sync_volume_from_chromecast()
```

## Benefits

1. **Static Configuration**: No dynamic discovery overhead
2. **Reliable Experience**: Pre-configured devices ensure predictable behavior
3. **Error Handling**: Clear feedback when devices are unavailable
4. **User-Friendly**: Visual indicators and intuitive menu navigation
5. **Event-Driven**: Loosely coupled, maintainable architecture

## Testing

Verified functionality with `test_chromecast_selection.py`:
- ✅ Menu generation with proper device list
- ✅ Event emission and handling
- ✅ Visual indicators (current device marking)
- ✅ Payload structure for device selection

## Future Enhancements

1. **Dynamic Current Device**: Show actual current device instead of hardcoded default
2. **Device Status**: Real-time availability checking
3. **Persistent Selection**: Remember last selected device across restarts
4. **Enhanced Status**: Detailed device information and connection status
