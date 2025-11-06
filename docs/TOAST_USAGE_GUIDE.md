# Toast Notification System - Usage Guide

## Overview

The Toast notification system provides a reusable, Bootstrap-based way to show notifications throughout the webapp. Toasts support stacking, auto-dismiss, custom durations, and multiple styles.

## Installation

The toast system is automatically loaded in all pages via `/app/web/templates/_navbar.html`. No additional setup required.

## Basic Usage

The global `toast` object is available in JavaScript on all pages:

```javascript
// Success notification (auto-dismisses after 5 seconds)
toast.success('Your action was successful!');

// Error notification
toast.error('Something went wrong!');

// Warning notification
toast.warning('Please review this information');

// Info notification
toast.info('Here is some information');
```

## API Reference

### `toast.show(message, type, duration, title)`

Show a toast notification with full control.

**Parameters:**
- `message` (string, required): The notification message
- `type` (string, optional): Toast type - `'success'`, `'error'`, `'warning'`, `'info'` (default: `'info'`)
- `duration` (number, optional): Auto-dismiss delay in milliseconds (default: `5000`, `0` = no auto-dismiss)
- `title` (string, optional): Custom title (defaults based on type)

**Example:**
```javascript
// Show error toast that doesn't auto-dismiss
toast.show('Database connection failed', 'error', 0, 'Critical Error');
```

### `toast.success(message, title, duration)`

Show a success notification.

**Parameters:**
- `message` (string, required): The notification message
- `title` (string, optional): Custom title (default: "Success")
- `duration` (number, optional): Auto-dismiss delay in ms (default: `5000`)

**Example:**
```javascript
toast.success('Album added to favorites!', 'Added', 3000);
```

### `toast.error(message, title, duration)`

Show an error notification.

**Parameters:**
- `message` (string, required): The notification message
- `title` (string, optional): Custom title (default: "Error")
- `duration` (number, optional): Auto-dismiss delay in ms (default: `5000`)

**Example:**
```javascript
toast.error('Failed to connect to Chromecast device', 'Connection Failed');
```

### `toast.warning(message, title, duration)`

Show a warning notification.

**Parameters:**
- `message` (string, required): The notification message
- `title` (string, optional): Custom title (default: "Warning")
- `duration` (number, optional): Auto-dismiss delay in ms (default: `5000`)

**Example:**
```javascript
toast.warning('This action cannot be undone', 'Warning');
```

### `toast.info(message, title, duration)`

Show an info notification.

**Parameters:**
- `message` (string, required): The notification message
- `title` (string, optional): Custom title (default: "Information")
- `duration` (number, optional): Auto-dismiss delay in ms (default: `5000`)

**Example:**
```javascript
toast.info('Syncing your music library...', 'Syncing');
```

## Common Patterns

### Pattern 1: API Error Handling

```javascript
async function playAlbum(albumId) {
    try {
        const response = await fetch(`/api/album/${albumId}/play`, { method: 'POST' });
        if (!response.ok) {
            const error = await response.json();
            toast.error(error.detail || 'Failed to play album', 'Playback Error');
            return;
        }
        toast.success('Album started playing!');
    } catch (error) {
        toast.error(error.message, 'Connection Error');
    }
}
```

### Pattern 2: Form Validation

```javascript
function submitForm(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    if (!email.includes('@')) {
        toast.warning('Please enter a valid email address', 'Invalid Input');
        return;
    }
    
    // Submit form...
    toast.success('Form submitted successfully!');
}
```

### Pattern 3: Conditional Notifications

```javascript
async function switchDevice(deviceName) {
    if (deviceName === currentDevice) {
        toast.info(`Already connected to ${deviceName}`, 'Already Active');
        return;
    }
    
    try {
        await fetch(`/api/chromecast/switch?device_name=${deviceName}`, { method: 'POST' });
        toast.success(`Switched to ${deviceName}`, 'Device Connected');
    } catch (error) {
        toast.error(`Failed to switch: ${error.message}`, 'Switch Failed');
    }
}
```

### Pattern 4: Long-Running Operations

```javascript
async function encodeNFC(dataType) {
    try {
        // Show info toast that doesn't auto-dismiss
        toast.info('Encoding in progress...', 'Please Wait', 0);
        
        const response = await fetch(`/api/nfc/encode`, {
            method: 'POST',
            body: JSON.stringify({ type: dataType })
        });
        
        if (response.ok) {
            // Remove the "please wait" toast is automatic
            toast.success('NFC encoding complete!');
        } else {
            toast.error('Encoding failed', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Error');
    }
}
```

## Styling

Toast notifications automatically receive appropriate colors based on their type:

| Type | Background | Text Color | Use For |
|------|-----------|-----------|---------|
| `success` | Green | White | Successful operations |
| `error` | Red | White | Errors and failures |
| `warning` | Yellow | Dark | Warnings and cautions |
| `info` | Blue | White | General information |

## Features

✅ **Stacking**: Multiple toasts stack vertically in the top-right corner
✅ **Auto-dismiss**: Toasts automatically disappear after their duration (configurable)
✅ **Manual dismiss**: Users can click the × button to dismiss toasts immediately
✅ **Accessibility**: Proper ARIA labels for screen readers
✅ **Bootstrap Integration**: Uses Bootstrap's toast component
✅ **Global**: Available on all pages without per-page setup

## Implementation Details

The toast system uses:
- **Bootstrap 5** Toast component for styling and behavior
- **Vanilla JavaScript** (no jQuery required)
- **CSS Grid** positioning for proper stacking
- **Z-index: 9999** to ensure toasts appear above all other content

## File Location

- **Toast Manager**: `/app/web/static/js/toast.js`
- **Navbar Integration**: `/app/web/templates/_navbar.html`

## Example Use Cases in Current App

### Device Switching (Navbar)
```javascript
// File: _navbar.html
async function switchDevice(deviceName) {
    if (deviceName === activeDevice) {
        toast.info(`Already connected to ${deviceName}`, 'Already Active');
        return;
    }
    
    try {
        await fetch(`/api/chromecast/switch?device_name=${encodeURIComponent(deviceName)}`, {
            method: 'POST'
        });
        
        activeDevice = deviceName;
        toast.success(`Switched to ${deviceName}`, 'Device Connected');
    } catch (error) {
        toast.error(`Failed to switch: ${error.message}`, 'Connection Error');
    }
}
```

## Best Practices

1. **Keep messages short and actionable**: Users should understand what happened in a glance
2. **Use appropriate types**: Help users understand the severity of the message
3. **Auto-dismiss wisely**: 
   - Use auto-dismiss for confirmations and info (faster feedback)
   - Disable auto-dismiss for errors or critical info (give users time to read)
4. **Provide context**: Include what failed, not just "Error occurred"
5. **Avoid toast spam**: Don't show multiple toasts for the same action

Good ❌ → `toast.error('Failed to connect to Living Room device')`
Bad ✅ → `toast.error('Error')`

Good ✅ → `toast.success('Music is now playing on Bedroom speaker')`
Bad ❌ → `toast.success('OK')`
