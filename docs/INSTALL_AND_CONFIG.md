# Fresh Install and Configuration

## 1) Base OS

- Raspberry Pi OS 64-bit (Bookworm or newer)
- Network access enabled
- SSH optional but recommended

## 2) Clone + install

```bash
cd /home/pi
mkdir -p shared
cd shared
git clone <repo-url> jukebox
cd jukebox
chmod +x install_service.sh
./install_service.sh
```

What installer handles:

- System package install (Python, GPIO/SPI/I2C libs, MPV, Bluetooth, Avahi)
- SPI/I2C enablement (when `raspi-config` is available)
- Virtualenv + Python deps
- `jukebox.service` install with current path
- Polkit rules for service/system control

## 3) Configure `.env`

```bash
cp .env.example .env   # if missing
nano .env
```

Minimum required:

- `SUBSONIC_URL`
- `SUBSONIC_USER`
- `SUBSONIC_PASS`

Key mode toggles:

- `HARDWARE_MODE=true|false`
- `PLAYBACK_BACKEND=chromecast|mpv`

## 4) Start and verify

```bash
sudo systemctl start jukebox
sudo systemctl status jukebox
sudo journalctl -u jukebox -f
```

Optional quick validation:

```bash
./venv/bin/python tests/setup_env.py
```

## 5) Clean-install checklist (concise)

- Service starts and stays `active (running)`
- UI reachable on port `8000`
- Subsonic/Gonic authentication succeeds
- Chosen output backend plays audio

## 6) Common config blocks

### Chromecast-first

```dotenv
PLAYBACK_BACKEND=chromecast
DEFAULT_CHROMECAST_DEVICE=Living Room
CHROMECAST_DISCOVERY_TIMEOUT=3
CHROMECAST_WAIT_TIMEOUT=10
```

### MPV + Bluetooth-first

```dotenv
PLAYBACK_BACKEND=mpv
BT_SPEAKER_MAC=
BT_AUTO_RECONNECT=true
MPV_CACHE_ENABLED=true
MPV_CACHE_SECS=90
MPV_AUDIO_BUFFER_SECONDS=1.2
```
