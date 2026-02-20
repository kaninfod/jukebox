# Local Player Backend (MPV)

This project now supports a local playback backend using MPV with minimal changes to the existing app flow.

## Backend selection

Set in `.env`:

- `PLAYBACK_BACKEND=mpv` (or `chromecast`)

## MPV settings

- `MPV_BINARY=mpv`
- `MPV_IPC_SOCKET=/tmp/jukebox-mpv.sock`
- `MPV_AUDIO_DEVICE=` (optional)
- `MPV_EXTRA_ARGS=` (optional extra CLI args)
- `MPV_STARTUP_TIMEOUT_SECONDS=5`
- `MPV_MSG_LEVEL=` (optional mpv native log level, e.g. `all=v`)
- `MPV_LOG_FILE=` (optional mpv native log file, e.g. `/tmp/mpv-jukebox.log`)
- `MPV_DIAGNOSTIC_INTERVAL_SECONDS=20` (periodic backend diagnostics in app logs)
- `MPV_STALL_WARNING_SECONDS=90` (warn if playback time is stuck while state is PLAYING)

## Bluetooth speaker settings

- `BT_SPEAKER_MAC=AA:BB:CC:DD:EE:FF`
- `BT_AUTO_RECONNECT=true`

When `BT_SPEAKER_MAC` is configured, playback checks speaker connectivity before starting.
If `BT_AUTO_RECONNECT=true`, the app attempts reconnect via `bluetoothctl connect <MAC>`.

## Operational endpoint

Use:

- `GET /api/mediaplayer/output_readiness`

Response includes:

- active backend
- backend status
- output readiness (including BT connection status for MPV)

## Raspberry Pi prerequisites

Install required tools:

- `mpv`
- `bluez` (for `bluetoothctl`)
- `pipewire-pulse` or `pulseaudio` (for `pactl` default sink checks)

Typical first-time BT setup:

1. `bluetoothctl`
2. `scan on`
3. `pair <MAC>`
4. `trust <MAC>`
5. `connect <MAC>`

Then set `BT_SPEAKER_MAC` in `.env` and restart the app.

## Switching to a different Bluetooth speaker

When replacing your BT speaker, you must update both:

- `BT_SPEAKER_MAC`
- `MPV_AUDIO_DEVICE`

### 1) Connect and trust the new speaker

```bash
bluetoothctl
scan on
pair <NEW_MAC>
trust <NEW_MAC>
connect <NEW_MAC>
# optional: disconnect old speaker
disconnect <OLD_MAC>
exit
```

### 2) Get the correct sink name

Preferred method (always correct):

```bash
pactl list short sinks | grep -i bluez_output
```

Use the sink name from output, for example:

- `bluez_output.FC_8F_90_F8_A3_93.1`

Then set:

- `MPV_AUDIO_DEVICE=pipewire/bluez_output.FC_8F_90_F8_A3_93.1`

Formula method (usually works):

- MAC `AA:BB:CC:DD:EE:FF` → `AA_BB_CC_DD_EE_FF`
- `MPV_AUDIO_DEVICE=pipewire/bluez_output.AA_BB_CC_DD_EE_FF.1`

### 3) Update `.env`

```dotenv
BT_SPEAKER_MAC=FC:8F:90:F8:A3:93
MPV_AUDIO_DEVICE=pipewire/bluez_output.FC_8F_90_F8_A3_93.1
```

### 4) Restart and validate

```bash
sudo systemctl restart jukebox
curl -s http://127.0.0.1:8000/api/mediaplayer/output_readiness | jq
pactl list short sink-inputs
pactl list short sinks
```

Expected while playing:

- `output_readiness.ready = true`
- `output_readiness.default_sink` points to new BT sink
- `output_readiness.sink_is_bluetooth = true`
- BT sink state in `pactl list short sinks` is `RUNNING`

### 5) If no sound but playback says PLAYING

Test MPV directly as the service user:

```bash
sudo -u pi XDG_RUNTIME_DIR=/run/user/1000 \
PULSE_SERVER=unix:/run/user/1000/pulse/native \
mpv --no-video --audio-device=pipewire/bluez_output.FC_8F_90_F8_A3_93.1 \
/usr/share/sounds/alsa/Front_Center.wav
```

If needed, try pulse backend device string:

```bash
mpv --no-video --audio-device=pulse/bluez_output.FC_8F_90_F8_A3_93.1 /usr/share/sounds/alsa/Front_Center.wav
```

## Automatic diagnostics in logs

The MPV backend now emits periodic diagnostics to the normal app logs so you can analyze stalls without manually polling endpoints.

Example `.env` settings:

```dotenv
MPV_DIAGNOSTIC_INTERVAL_SECONDS=20
MPV_STALL_WARNING_SECONDS=90
# Optional deeper mpv-native logs:
MPV_MSG_LEVEL=all=v
MPV_LOG_FILE=/tmp/mpv-jukebox.log
```

When troubleshooting, look for:

- `MPV diagnostics (...)`
- `MPV end-file event: reason=...`
- `MPV possible stall: ...`
