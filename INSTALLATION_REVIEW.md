# Jukebox Application - Installation & Portability Review

## 🔍 Current State Analysis

### ✅ What's Working
- **Systemd service file** (`jukebox.service`) - properly configured
- **Service management script** (`jukebox.sh`) - convenient wrapper
- **Requirements.txt** - core Python dependencies listed
- **Environment configuration** - `.env` system in place

### ❌ Critical Issues Found

#### 1. **Outdated Dependencies in setup_env.py**
The setup script still references **legacy Home Assistant & YouTube** dependencies:
```python
required_vars = [
    "HA_TOKEN",           # ❌ No longer used
    "HA_BASE_URL",        # ❌ No longer used  
    "DB_PASSWORD",        # ✅ Still needed
    "YOUTUBE_ACCESS_TOKEN", # ❌ No longer used
    "YOUTUBE_REFRESH_TOKEN" # ❌ No longer used
]
```

#### 2. **Missing System Dependencies**
The application requires several system packages not documented:
- **SPI interface** (for display)
- **I2C interface** (for RFID)
- **GPIO access** (for buttons/encoder)
- **MariaDB/MySQL client libraries**
- **Audio system dependencies**

#### 3. **Missing Installation Guide**
No comprehensive installation documentation exists.

#### 4. **Empty Installation Script**
`install_service.sh` is completely empty.

## 📋 Complete Dependency Analysis

### **System Dependencies (apt packages)**
```bash
# Core system packages
sudo apt update
sudo apt install -y \\
    python3 \\
    python3-pip \\
    python3-venv \\
    git \\
    mariadb-client \\
    libmariadb-dev \\
    python3-dev \\
    build-essential

# Hardware interface packages  
sudo apt install -y \\
    python3-rpi.gpio \\
    python3-spidev \\
    i2c-tools \\
    python3-smbus

# Audio system (if using local audio)
sudo apt install -y \\
    alsa-utils \\
    pulseaudio

# Display dependencies
sudo apt install -y \\
    libfreetype6-dev \\
    libjpeg-dev \\
    libopenjp2-7 \\
    libtiff5
```

### **Python Dependencies** (requirements.txt)
Current requirements.txt looks good but missing version pinning:
```text
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
spidev>=3.5
pillow>=8.3.0
luma.lcd>=2.10.0
luma.core>=2.4.0
rpi-lgpio>=0.4
pi-rc522>=2.2.1
mariadb>=1.0.0
pymysql>=1.0.0
sqlalchemy>=1.4.0
requests>=2.25.0
websockets>=10.0
python-dotenv>=0.19.0
pychromecast>=13.0.0
```

### **System Configuration Requirements**

#### **GPIO/SPI/I2C Permissions**
```bash
# Add pi user to required groups
sudo usermod -a -G gpio,spi,i2c pi

# Enable SPI and I2C interfaces
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
```

#### **Polkit Rules** (for system control)
File: `/etc/polkit-1/localauthority/50-local.d/50-jukebox.pkla`
```ini
[Allow jukebox service control]
Identity=unix-user:pi
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:jukebox.service

[Allow system shutdown/reboot]
Identity=unix-user:pi  
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:poweroff.target;system:reboot.target
```

## 🚀 Recommended Installation Process

### **Phase 1: System Preparation**
1. **Fresh Raspberry Pi OS 64-bit** installation
2. **Enable SSH** (optional, for remote setup)
3. **Update system**: `sudo apt update && sudo apt upgrade -y`
4. **Enable hardware interfaces**: SPI, I2C, GPIO
5. **Install system dependencies**

### **Phase 2: Application Setup**
1. **Clone repository** to `/home/pi/shared/jukebox`
2. **Create Python virtual environment**
3. **Install Python dependencies**
4. **Configure environment** (`.env` file)
5. **Set up database** (if required)

### **Phase 3: Service Installation**
1. **Install systemd service**
2. **Configure polkit permissions**
3. **Enable and start service**
4. **Verify operation**

## 📝 Action Items for Portability

### **Immediate Fixes Needed**

#### 1. **Update setup_env.py**
Remove legacy dependencies and add current ones:
```python
required_vars = [
    "DB_PASSWORD",
    "SUBSONIC_USER", 
    "SUBSONIC_PASS"
]
```

#### 2. **Create comprehensive install_service.sh**
```bash
#!/bin/bash
# Complete installation script for Raspberry Pi Jukebox

set -e  # Exit on any error

echo "🎵 Raspberry Pi Jukebox Installation Script"
echo "=========================================="

# System preparation
sudo apt update
# ... (install all dependencies)

# Application setup  
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Service installation
sudo cp jukebox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jukebox

echo "✅ Installation complete!"
```

#### 3. **Create comprehensive README.md**
- **Hardware requirements**
- **System compatibility** 
- **Step-by-step installation**
- **Configuration guide**
- **Troubleshooting**

#### 4. **Version pin requirements.txt**
Add specific version numbers to prevent compatibility issues.

#### 5. **Add hardware validation script**
Test that all GPIO pins, SPI, I2C, and hardware components work.

### **Testing Strategy for Clean RPI4**

1. **Prepare test environment**:
   - Fresh Raspberry Pi OS 64-bit
   - No existing Python packages
   - Default user configuration

2. **Document each step**:
   - Time each installation phase
   - Note any errors or issues
   - Verify all functionality works

3. **Create automated validation**:
   - Hardware detection script
   - Service health checks
   - Configuration validation

## 📦 Recommended Project Structure Updates

```
/Volumes/Shared/jukebox/
├── install/                    # NEW: Installation scripts
│   ├── install.sh             # Main installation script
│   ├── hardware_test.py       # Hardware validation
│   └── polkit_rules.pkla      # Polkit configuration
├── docs/                      # NEW: Documentation
│   ├── README.md             # Main installation guide
│   ├── HARDWARE.md           # Hardware setup guide
│   └── TROUBLESHOOTING.md    # Common issues
├── requirements.txt           # Updated with versions
├── setup_env.py              # Updated for current config
└── ...existing files...
```

## 🎯 Next Steps

1. **Fix setup_env.py** - Remove legacy variables
2. **Create install.sh** - Complete installation automation  
3. **Write README.md** - Step-by-step installation guide
4. **Test on clean RPI4** - Validate entire process
5. **Add hardware validation** - Ensure all components work
6. **Version pin requirements** - Prevent compatibility issues

This review identifies all the gaps that need to be addressed for a smooth installation experience on a clean Raspberry Pi 4.
