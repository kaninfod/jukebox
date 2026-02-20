# Integrations Setup

This page describes required configuration for each integration without deep vendor-specific tutorials.

## 1) Hardware integration

### Display (ILI9488 SPI)

Config keys:

- `DISPLAY_WIDTH`, `DISPLAY_HEIGHT`, `DISPLAY_ROTATION`
- `DISPLAY_POWER_GPIO`, `DISPLAY_BACKLIGHT_GPIO`
- `DISPLAY_GPIO_CS`, `DISPLAY_GPIO_DC`, `DISPLAY_GPIO_RST`

Requirements:

- SPI enabled
- Correct GPIO mapping

### Pushbuttons

Config keys:

- `BUTTON_1_GPIO` .. `BUTTON_5_GPIO`
- `BUTTON_BOUNCETIME`

### Rotary encoder (KY-040)

Config keys:

- `ROTARY_ENCODER_PIN_A`
- `ROTARY_ENCODER_PIN_B`
- `ENCODER_BOUNCETIME`

### RFID reader

Config keys:

- `RFID_CS_PIN`
- `NFC_CARD_SWITCH_GPIO`
- `RFID_POLL_INTERVAL`, `RFID_READ_TIMEOUT`

## 2) Gonic / Subsonic integration

Required:

- `SUBSONIC_URL`
- `SUBSONIC_USER`
- `SUBSONIC_PASS`

Optional:

- `SUBSONIC_CAST_BASE_URL` (LAN/reverse-proxy cases)
- `SUBSONIC_PROXY_BASIC_USER`, `SUBSONIC_PROXY_BASIC_PASS`

Expectation:

- Server reachable from Pi and (for casting) reachable by Chromecast device.

## 3) Chromecast integration

Config keys:

- `PLAYBACK_BACKEND=chromecast`
- `DEFAULT_CHROMECAST_DEVICE`
- `CHROMECAST_DEVICES`
- `CHROMECAST_FALLBACK_DEVICES`
- `CHROMECAST_DISCOVERY_TIMEOUT`, `CHROMECAST_WAIT_TIMEOUT`

Requirements:

- Same LAN / multicast discovery available
- Avahi/mDNS services healthy

## 4) Bluetooth + MPV integration

Config keys:

- `PLAYBACK_BACKEND=mpv`
- `BT_SPEAKER_MAC`
- `BT_AUTO_RECONNECT`
- `MPV_AUDIO_DEVICE` (optional explicit sink)
- `MPV_CACHE_*`, `MPV_AUDIO_BUFFER_SECONDS`

Requirements:

- `mpv`, `bluetoothctl`, PulseAudio/PipeWire user runtime
- Speaker paired and trusted

## 5) Security + access integration

Config keys:

- `API_KEY`
- `CORS_ALLOW_ORIGINS`
- `ALLOWED_HOSTS`
- `ENABLE_HTTPS_REDIRECT`
- `PUBLIC_BASE_URL`

Use this when exposing the UI/API outside local development.

---

## Confirm with owner (to finalize)

Please confirm these hardware mapping details for final docs hardening:

1. Final production GPIO map for display, RFID, encoder, and all buttons.
2. Whether `NFC_CARD_SWITCH_GPIO` is wired as `4` or another pin in production.
3. Any board-specific wiring notes (pull-ups, inversion, shared SPI quirks).
