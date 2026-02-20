# User Guide

## What this system does

- Plays albums from your Subsonic/Gonic library.
- Supports card-based playback with RFID (optional).
- Supports Chromecast playback and local MPV playback.
- Offers web UI + API control.
- Supports physical controls in hardware mode (buttons, rotary encoder, display).

## Daily use

### Start / stop service

```bash
sudo systemctl start jukebox
sudo systemctl stop jukebox
sudo systemctl restart jukebox
sudo systemctl status jukebox
```

### Open UI

- Main UI: `http://<pi-ip>:8000`
- Kiosk status view: `http://<pi-ip>:8000/status?kiosk=1`

### Typical playback flow

1. Select output device/backend in the UI.
2. Browse albums and play.
3. Use RFID card scan to trigger mapped album (if enabled).
4. Use hardware controls (if `HARDWARE_MODE=true`).

## Modes

### Headless mode

- Set `HARDWARE_MODE=false`.
- No display/RFID/buttons/encoder required.
- Full web control remains available.

### Hardware mode

- Set `HARDWARE_MODE=true`.
- Initializes display + GPIO + RFID + encoder/button handlers.

## Feature summary (concise)

- **Playback backends**: Chromecast or MPV (`PLAYBACK_BACKEND`).
- **RFID**: maps card to album and starts playback.
- **Output switching**: device/backend change from UI/API.
- **API docs**: optional via `ENABLE_DOCS=true`.

## Limitations / caveats

- Bluetooth quality depends on RF conditions and distance.
- Chromecast availability depends on LAN discovery and network health.
- Wrong GPIO mappings can cause non-responsive controls.

## Quick troubleshooting

```bash
sudo journalctl -u jukebox -f
```

- No playback: check `SUBSONIC_*` credentials and selected output.
- Bluetooth choppy: increase distance margin / reduce interference.
- Hardware not responding: verify `HARDWARE_MODE` and GPIO pins in `.env`.
