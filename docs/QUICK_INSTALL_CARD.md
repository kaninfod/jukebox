# RPI4 Jukebox - Quick Installation Reference Card

## 🎯 One-Page Installation Guide

### Prerequisites
- Raspberry Pi 4 (2GB+ RAM)
- 16GB+ microSD card
- Subsonic/Navidrome server running
- Chromecast device

---

## ⚡ Quick Install (30 minutes)

### 1. Flash OS (5 min)
```
Download: Raspberry Pi Imager
OS: Raspberry Pi OS (64-bit) Bookworm
Settings: Enable SSH, set hostname "jukeplayer", configure WiFi
```

### 2. SSH and Clone (3 min)
```bash
ssh pi@jukeplayer.local
cd /home/pi && mkdir -p shared && cd shared
git clone [YOUR_REPO_URL] jukebox
cd jukebox
```

### 3. Install (15 min)
```bash
chmod +x install_service.sh
./install_service.sh
# ☕ Wait for completion
```

### 4. Configure (5 min)
```bash
nano .env
```
**Required settings:**
```bash
HARDWARE_MODE=false                        # true if using display/RFID
SUBSONIC_URL=http://your-server:4747
SUBSONIC_USER=your_username
SUBSONIC_PASS=your_password
```
Save: `Ctrl+X` → `Y` → `Enter`

### 5. Start (2 min)
```bash
sudo systemctl start jukebox
sudo journalctl -u jukebox -f
```
**Look for**: ✅ "Jukebox app startup complete"

### 6. Test
Open browser: `http://jukeplayer.local:8000`

---

## 🔧 Essential Commands

```bash
# Service Control
sudo systemctl start jukebox       # Start
sudo systemctl stop jukebox        # Stop
sudo systemctl restart jukebox     # Restart
sudo systemctl status jukebox      # Status

# Logs
sudo journalctl -u jukebox -f      # Follow logs
sudo journalctl -u jukebox -n 50   # Last 50 lines

# Configuration
nano /home/pi/shared/jukebox/.env  # Edit config
sudo systemctl restart jukebox     # Apply changes

# Helper Script
cd /home/pi/shared/jukebox
./jukebox.sh start|stop|restart|status|logs
```

---

## 🎛️ Configuration Modes

### Headless Mode (No Hardware)
```bash
HARDWARE_MODE=false
```
✅ Web interface only  
✅ Perfect for development  
✅ No GPIO/display needed

### Full Hardware Mode
```bash
HARDWARE_MODE=true
DISPLAY_WIDTH=480
DISPLAY_HEIGHT=320
```
✅ ILI9488 TFT display  
✅ RC522 RFID reader  
✅ Physical buttons/encoder

### Production Security
```bash
API_KEY=your-secure-random-key
ALLOWED_HOSTS=jukeplayer.local,your-domain.com
ENABLE_HTTPS_REDIRECT=true
ALLOW_LOCAL_API_BYPASS=false
ENABLE_DOCS=false
```

---

## 🐛 Quick Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u jukebox -n 50
# Check: .env exists, venv created, correct permissions
```

### Can't Access Web Interface
```bash
# Check service is running
sudo systemctl status jukebox

# Check firewall
sudo ufw status

# Test locally
curl http://localhost:8000
```

### No Chromecast Devices
```bash
# Check network
ping your-chromecast-ip

# Scan network
sudo apt install avahi-utils
avahi-browse -a | grep -i cast
```

### Hardware Not Working
```bash
# Check interfaces
ls /dev/spi*        # Should show /dev/spidev0.0
sudo i2cdetect -y 1 # Should show I2C devices

# Check groups
groups pi           # Should include: gpio spi i2c

# Enable if missing
sudo raspi-config
# → Interface Options → Enable SPI/I2C
sudo reboot
```

---

## 📱 Web Interface URLs

| URL | Purpose |
|-----|---------|
| `http://jukeplayer.local:8000` | Main interface |
| `http://jukeplayer.local:8000/status` | Status page |
| `http://jukeplayer.local:8000/status?kiosk=1` | Kiosk mode |
| `http://jukeplayer.local:8000/docs` | API docs (if enabled) |
| `http://jukeplayer.local:8000/metrics` | Prometheus metrics (if enabled) |

---

## 📂 Important File Locations

```
/home/pi/shared/jukebox/
├── .env                    # Configuration (edit this)
├── venv/                   # Python virtual environment
├── app/                    # Application code
├── static_files/           # Album covers
├── app/database/album.db   # SQLite database
└── docs/                   # Documentation

/etc/systemd/system/jukebox.service  # Service file
/var/log/journal/                    # Systemd logs
```

---

## 🎵 First Use

1. **Access Web Interface**: `http://jukeplayer.local:8000`
2. **Go to Albums**: Browse music from Subsonic
3. **Add RFID Card**: Scan card, associate with album
4. **Play Music**: Scan card → Music plays on Chromecast
5. **Kiosk Mode**: Access `?kiosk=1` for touchscreen interface

---

## 📚 Full Documentation

- **Detailed Install**: `docs/FRESH_INSTALL.md`
- **Config Reference**: `.env.example`
- **Hardware Setup**: `docs/HARDWARE.md`
- **Kiosk Mode**: `docs/KIOSK_MODE.md`

---

## 🆘 Getting Help

1. Check logs: `sudo journalctl -u jukebox -f`
2. Read troubleshooting: `docs/FRESH_INSTALL.md`
3. Verify configuration: `.env` file
4. Test components individually
5. Check network connectivity

---

**Quick Install Complete! 🎉**

For detailed information, see: `docs/FRESH_INSTALL.md`
