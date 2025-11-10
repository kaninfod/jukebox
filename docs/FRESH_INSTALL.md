$$$$$$$$# Fresh Installation Guide - Raspberry Pi 4 Jukebox

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Hardware Setup](#hardware-setup)
3. [Operating System Installation](#operating-system-installation)
4. [Jukebox Software Installation](#jukebox-software-installation)
5. [Configuration](#configuration)
6. [First Boot](#first-boot)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

### Required Hardware
- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **MicroSD Card** (16GB+ Class 10 or better)
- **Power Supply** (Official Pi 4 power supply recommended - 5V/3A USB-C)
- **Network Connection** (Ethernet or WiFi)

### Optional Hardware (for full hardware mode)
- **ILI9488 480x320 TFT Display** with SPI interface
- **RC522 RFID Reader Module**
- **KY-040 Rotary Encoder**
- **Push Buttons** (5-6 buttons for controls)
- **Connecting Wires** and breadboard or custom PCB

### Required Services
- **Subsonic/Navidrome Music Server** (must be accessible from Pi)
- **Chromecast Device** (for audio playback)

---

## 🔧 Hardware Setup

### Option 1: Headless Mode (Development/Testing)
No physical hardware required! Just the Raspberry Pi and network connection.

### Option 2: Full Hardware Mode
See [docs/HARDWARE.md](HARDWARE.md) for detailed wiring diagrams and assembly instructions.

**Quick Pin Reference:**
- Display: SPI0 (MOSI, MISO, SCLK, CE0) + GPIO 6, 5, 20, 18
- RFID: SPI0 (shared with display) + CS on GPIO 7
- Rotary Encoder: GPIO 27, 22
- Buttons: GPIO 26, 14, 15, 12, 19, 17

---

## 💿 Operating System Installation

### Step 1: Download Raspberry Pi OS
1. Download **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Insert your microSD card into your computer
3. Run Raspberry Pi Imager

### Step 2: Configure and Flash
1. **Choose OS**: `Raspberry Pi OS (64-bit)` - Bookworm or later
   - Select: "Raspberry Pi OS (64-bit)" from the list
   
2. **Choose Storage**: Select your microSD card

3. **Advanced Options** (gear icon):
   ```
   ✅ Set hostname: jukeplayer (or your preference)
   ✅ Enable SSH: Use password authentication
   ✅ Set username: pi
   ✅ Set password: [your secure password]
   ✅ Configure WiFi: [your network details]
   ✅ Set locale: [your timezone/keyboard]
   ```

4. **Write**: Flash the OS to the microSD card

### Step 3: First Boot
1. Insert the microSD card into your Raspberry Pi
2. Connect power and network
3. Wait 2-3 minutes for first boot
4. Find your Pi's IP address:
   ```bash
   # On your computer:
   ping jukeplayer.local
   # OR check your router's DHCP table
   ```

### Step 4: Initial SSH Connection
```bash
ssh pi@jukeplayer.local
# OR
ssh pi@[IP_ADDRESS]
```

---

## 📦 Jukebox Software Installation

### Step 1: Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Clone Repository
```bash
cd /home/pi
mkdir -p shared
cd shared
git clone [YOUR_REPOSITORY_URL] jukebox
cd jukebox
```

### Step 3: Run Installation Script
```bash
chmod +x install_service.sh
./install_service.sh
```

**This script will:**
- ✅ Install all system dependencies
- ✅ Enable SPI and I2C interfaces
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Install systemd service
- ✅ Setup polkit rules for system control
- ✅ Create .env configuration file

**⏱️ Installation takes 10-15 minutes**

---

## ⚙️ Configuration

### Step 1: Edit Configuration File
```bash
cd /home/pi/shared/jukebox
nano .env
```

### Step 2: Required Configuration

**Minimum configuration for headless mode:**
```bash
# Hardware Mode
HARDWARE_MODE=false

# Subsonic/Navidrome Server
SUBSONIC_URL=http://your-music-server:4747
SUBSONIC_USER=your_username
SUBSONIC_PASS=your_password

# Chromecast (if using HTTPS or reverse proxy)
PUBLIC_BASE_URL=https://your-domain.com  # Optional
```

**For full hardware mode:**
```bash
# Hardware Mode
HARDWARE_MODE=true

# ... (same Subsonic config as above)

# Display Configuration
DISPLAY_WIDTH=480
DISPLAY_HEIGHT=320
DISPLAY_ROTATION=0

# GPIO pins match your wiring
# (see .env.example for all GPIO options)
```

### Step 3: Security Configuration (Production)
```bash
# Generate a secure API key
API_KEY=[generate-secure-random-string]

# Restrict allowed hosts
ALLOWED_HOSTS=jukeplayer.local,192.168.1.100

# Enable HTTPS redirect (if using reverse proxy)
ENABLE_HTTPS_REDIRECT=true
```

### Step 4: Save and Exit
Press `Ctrl+X`, then `Y`, then `Enter`

---

## 🚀 First Boot

### Step 1: Start the Service
```bash
sudo systemctl start jukebox
```

### Step 2: Check Status
```bash
sudo systemctl status jukebox
```

**Expected output:**
```
● jukebox.service - Raspberry Pi Jukebox Application
   Loaded: loaded (/etc/systemd/system/jukebox.service; enabled)
   Active: active (running) since ...
```

### Step 3: View Logs
```bash
sudo journalctl -u jukebox -f
```

**Look for:**
```
✅ Configuration validation passed
✅ Service container initialized  
✅ Jukebox app startup complete
```

### Step 4: Enable Auto-start
```bash
sudo systemctl enable jukebox
```

### Step 5: Reboot (Recommended)
```bash
sudo reboot
```

After reboot, the jukebox will start automatically.

---

## 🧪 Testing

### Test 1: Web Interface
1. Open browser: `http://jukeplayer.local:8000`
2. You should see the jukebox web interface
3. Navigate to `/status?kiosk=1` for kiosk mode

### Test 2: API Documentation (if enabled)
1. Set `ENABLE_DOCS=true` in `.env`
2. Restart: `sudo systemctl restart jukebox`
3. Open: `http://jukeplayer.local:8000/docs`
4. Interactive API documentation should load

### Test 3: Chromecast Discovery
```bash
# View logs
sudo journalctl -u jukebox -f

# In web interface:
# - Go to Devices section
# - Should show discovered Chromecast devices
```

### Test 4: RFID (if hardware connected)
1. Scan an RFID card
2. Check logs for card UID
3. Associate card with album in web interface

### Test 5: Hardware Controls (if connected)
- **Buttons**: Press each button, check logs for GPIO events
- **Rotary Encoder**: Turn encoder, check volume changes
- **Display**: Should show current track info

---

## 🔧 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u jukebox -n 50 --no-pager
```

**Common issues:**
- ❌ **Missing .env file**: Copy from .env.example
- ❌ **Wrong Python path**: Check venv was created properly
- ❌ **Port already in use**: Another service on port 8000
- ❌ **Permission denied**: GPIO/SPI/I2C group membership

**Fix permissions:**
```bash
sudo usermod -a -G gpio,spi,i2c pi
# Logout and login again
```

### Can't Connect to Subsonic

**Test connection manually:**
```bash
curl "http://your-server:4747/rest/ping?u=user&p=pass&v=1.15.0&c=test"
```

**Should return:**
```xml
<subsonic-response status="ok" version="1.15.0">
```

### No Chromecast Devices Found

**Check network:**
```bash
# Install avahi tools
sudo apt install avahi-utils

# Scan for Chromecasts
avahi-browse -a | grep -i cast
```

**Common issues:**
- ❌ Pi and Chromecast on different VLANs
- ❌ mDNS/multicast blocked by firewall
- ❌ Chromecast offline/powered off

### Hardware Not Detected

**Test SPI:**
```bash
ls /dev/spi*
# Should show: /dev/spidev0.0 /dev/spidev0.1
```

**Test I2C:**
```bash
sudo i2cdetect -y 1
```

**Test GPIO:**
```bash
groups pi
# Should include: gpio spi i2c
```

**Enable interfaces if missing:**
```bash
sudo raspi-config
# Interface Options → Enable SPI
# Interface Options → Enable I2C
sudo reboot
```

### Python Package Issues

**Reinstall dependencies:**
```bash
cd /home/pi/shared/jukebox
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Display Not Working

**Check SPI connection:**
```bash
# Test SPI communication
sudo apt install python3-spidev
python3 -c "import spidev; spi = spidev.SpiDev(); spi.open(0,0); print('SPI OK')"
```

**Check luma.lcd installation:**
```bash
source venv/bin/activate
python3 -c "import luma.lcd; print('luma.lcd OK')"
```

---

## 📚 Next Steps

### Configure Album Library
1. Access web interface: `http://jukeplayer.local:8000`
2. Go to **Albums** section
3. Scan RFID cards and associate with albums
4. Download album artwork

### Setup Kiosk Mode
1. Edit `.env`: Add display/touch configuration
2. Restart service
3. Access: `http://jukeplayer.local:8000/status?kiosk=1`
4. Full-screen kiosk interface for 1280×720 displays

### Optional: Setup Reverse Proxy
For HTTPS access and external connectivity:
- Install Nginx or Caddy
- Configure SSL certificates (Let's Encrypt)
- Update `PUBLIC_BASE_URL` in `.env`

### Optional: Monitoring
Enable Prometheus metrics:
```bash
# In .env
ALLOW_PUBLIC_METRICS=true

# Access metrics
curl http://jukeplayer.local:8000/metrics
```

---

## 🎉 Installation Complete!

Your Raspberry Pi Jukebox is now ready to use!

### Quick Command Reference
```bash
# Start/Stop/Restart
sudo systemctl start jukebox
sudo systemctl stop jukebox
sudo systemctl restart jukebox

# View logs
sudo journalctl -u jukebox -f

# Check status
sudo systemctl status jukebox

# Edit configuration
nano /home/pi/shared/jukebox/.env
sudo systemctl restart jukebox  # After changes
```

### Support & Documentation
- **Full Documentation**: See `/docs` folder
- **API Reference**: `http://jukeplayer.local:8000/docs`
- **Configuration Reference**: See `.env.example`
- **Hardware Guide**: See `docs/HARDWARE.md`

---

**Enjoy your jukebox! 🎵**
