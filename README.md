# Raspberry Pi Jukebox

A modern jukebox system for Raspberry Pi with RFID card support, display interface, and Chromecast integration.

## 🎯 Features

- **RFID Music Cards** - Play albums by scanning RFID cards
- **Touch Display** - ILI9488 480x320 display with touch controls
- **Rotary Encoder** - Volume control and menu navigation
- **Hardware Controls** - Physical buttons for playback control
- **Chromecast Support** - Stream music to Chromecast devices
- **Subsonic Integration** - Connect to Navidrome/Subsonic music servers
- **Web Interface** - FastAPI-based REST API for remote control
- **System Integration** - Systemd service with automatic startup

## 🔧 Hardware Requirements

### **📱 Headless Mode (No Hardware Required)**
For development, testing, or web-only operation:
- Any Raspberry Pi or Linux system
- No display, RFID, or physical controls needed
- Web interface and API remain fully functional
- Set `HARDWARE_MODE=false` in .env file

### **🔧 Full Hardware Mode**

#### **Raspberry Pi**
- Raspberry Pi 4 (recommended) or Pi 3B+
- Raspberry Pi OS 64-bit (Bookworm or later)
- 16GB+ microSD card (Class 10 or better)

#### **Display**
- ILI9488 480x320 TFT display with SPI interface

#### **Input Controls**
- Or local audio via Pi's 3.5mm jack/HDMI

| Display Power | 20 | Display power control |
| Display Backlight | 18 | Backlight PWM control |
| RFID CS | 7 | SPI chip select |
| NFC Card Switch | 26 | Card detection |
| Rotary Encoder A | 6 | Encoder input A |
| Rotary Encoder B | 5 | Encoder input B |
| Button 1 | 14 | Previous track |
| Button 2 | 15 | Play/Pause |
| Button 3 | 12 | Next track |
| Button 4 | 19 | Volume down |
| Button 5 | 17 | Volume up |

*Note: Pins can be customized via environment variables*

## 🚀 Quick Installation

### **Method 1: Automated Installation (Recommended)**

1. **Clone the repository:**
   ```bash
   cd /home/pi
   mkdir shared
   cd shared
   git clone <repository-url> jukebox
   cd jukebox
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install_service.sh
   ./install_service.sh
   ```

   nano .env
   ```
   ```bash
   python3 setup_env.py
   ```

5. **Start the service:**

### **🖥️ Headless Mode Installation**

For development or web-only operation without physical hardware:

1. **Follow steps 1-2 above (clone and run install script)**

2. **Configure for headless mode:**
   ```bash
   cp env.template .env
   nano .env
   ```
   Set: `HARDWARE_MODE=false`

3. **Start in headless mode:**
   ```bash
   sudo systemctl start jukebox
   ```
   
   The system will start without initializing display, RFID, or buttons.
   Web interface available at: `http://your-pi-ip:8000`

### **Method 2: Manual Installation**

See [MANUAL_INSTALLATION.md](docs/MANUAL_INSTALLATION.md) for step-by-step manual setup.

## ⚙️ Configuration

### **Required Environment Variables**

Create a `.env` file with your configuration:

```bash
# Subsonic/Navidrome Configuration
SUBSONIC_URL=http://your-music-server:4747
SUBSONIC_USER=your_username
SUBSONIC_PASS=your_password

# Database Configuration  
# SQLite database is used automatically - no additional configuration needed

# Network Configuration
LOG_SERVER_HOST=your_syslog_server
```

### **Optional Configuration**

All timeouts, GPIO pins, and device settings can be customized via environment variables. See `.env.example` for all available options.

## 🎵 Usage

### **Adding Music Cards**

1. **Access the web interface:** `http://your-pi-ip:8000`
2. **Navigate to Albums** section
3. **Scan an RFID card** when prompted
4. **Associate the card** with an album from your music library
5. **Generate album artwork** (optional)

### **Playing Music**

1. **Scan an RFID card** on the reader
2. **Music will automatically start** playing on your configured Chromecast
3. **Use hardware controls** for volume, skip, pause/play
4. **Touch display** for additional controls and information

### **System Control**

- **Service management:** Use `./jukebox.sh start|stop|restart|status`
- **Web API:** Full REST API available at `http://your-pi-ip:8000/docs`
- **Logs:** `sudo journalctl -u jukebox -f`

## 🔧 Troubleshooting

### **Service Won't Start**
```bash
# Check service status
sudo systemctl status jukebox

# View detailed logs
sudo journalctl -u jukebox -n 50

# Validate configuration
python3 setup_env.py
```

### **Hardware Not Detected**
```bash
# Test SPI interface
ls /dev/spi*

# Test I2C interface  
sudo i2cdetect -y 1

# Check GPIO permissions
groups pi
```

### **Audio Issues**
```bash
# List Chromecast devices
# Via web interface: http://your-pi-ip:8000/api/chromecast/listchromecasts

# Test audio output locally
aplay /usr/share/sounds/alsa/Front_Left.wav
```

## 🏗️ Development

### **Running in Development Mode**
```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
python3 run.py
```

### **Running Tests**
```bash
python3 run_tests.py
```

## 📚 Documentation

- **[Hardware Setup Guide](docs/HARDWARE.md)** - Detailed wiring and assembly
- **[API Documentation](docs/API.md)** - REST API reference
- **[Configuration Reference](docs/CONFIGURATION.md)** - All available settings
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Web framework
- **Luma.LCD** - Display driver library  
- **PyChromecast** - Chromecast integration
- **pi-rc522** - RFID reader library
- **Raspberry Pi Foundation** - Hardware platform
