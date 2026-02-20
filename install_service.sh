#!/bin/bash

# Raspberry Pi Jukebox Installation Script
# Complete setup for a clean Raspberry Pi 4 running Raspberry Pi OS 64-bit

set -e  # Exit on any error

INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_UID="$(id -u "$INSTALL_USER")"

echo "🎵 Raspberry Pi Jukebox Installation Script"
echo "============================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "❌ This script is designed for Raspberry Pi hardware"
    exit 1
fi

echo "✅ Raspberry Pi detected"

if [ ! -f "requirements.txt" ] || [ ! -f "jukebox.service" ]; then
    echo "❌ Run this script from the jukebox project root"
    exit 1
fi

echo "👤 Installation user: $INSTALL_USER (uid: $INSTALL_UID)"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y


# Refer to WORKING_GPIO_ENVIRONMENT.txt for GPIO setup details
echo "📦 Installing system dependencies..."

# Remove python3-rpi.gpio if present (must NOT be installed)
if dpkg -l | grep -q python3-rpi.gpio; then
    echo "❌ Removing python3-rpi.gpio to avoid conflicts with rpi-lgpio..."
    sudo apt remove -y python3-rpi.gpio
fi

# Core dependencies that should always be available
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-dotenv \
    git \
    build-essential \
    python3-lgpio \
    python3-rpi-lgpio \
    python3-spidev \
    i2c-tools \
    python3-smbus \
    mpv \
    bluez \
    pulseaudio-utils \
    avahi-daemon \
    avahi-utils \
    libnss-mdns \
    policykit-1 \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7

# SQLite is built into Python - no additional database packages needed

# Image processing dependencies with fallback
if ! sudo apt install -y libtiff6; then
    echo "⚠️ libtiff6 not found, trying libtiff5..."
    sudo apt install -y libtiff5 || echo "⚠️ Neither libtiff6 nor libtiff5 available, may affect image processing"
fi

echo "✅ System dependencies installed"

echo "🔊 Enabling discovery/audio services..."
sudo systemctl enable --now bluetooth || true
sudo systemctl enable --now avahi-daemon || true

# Enable hardware interfaces
echo "🔧 Enabling SPI and I2C interfaces..."
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_i2c 0
else
    echo "⚠️ raspi-config not available - enable SPI/I2C manually if needed"
fi

# Add install user to required groups
echo "👤 Adding $INSTALL_USER to hardware groups..."
sudo usermod -a -G gpio,spi,i2c "$INSTALL_USER"

echo "✅ Hardware interfaces configured"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "✅ Python dependencies installed"

# Setup environment configuration
echo "⚙️ Setting up configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Copied .env.example to .env - please edit with your values"
    else
        echo "❌ No .env.example found - please create .env file manually"
    fi
else
    echo "✅ .env file already exists"
fi

# Install systemd service
echo "🔧 Installing systemd service..."

# Get the current working directory (where jukebox is installed)
JUKEBOX_PATH=$(pwd)
echo "📁 Jukebox installation path: $JUKEBOX_PATH"

# Create a temporary service file with the correct path
TMP_SERVICE_FILE="/tmp/jukebox.service"
sed \
    -e "s|/home/pi/shared/jukebox|$JUKEBOX_PATH|g" \
    -e "s|^User=pi$|User=$INSTALL_USER|" \
    -e "s|^Environment=XDG_RUNTIME_DIR=/run/user/1000$|Environment=XDG_RUNTIME_DIR=/run/user/$INSTALL_UID|" \
    -e "s|^Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native$|Environment=PULSE_SERVER=unix:/run/user/$INSTALL_UID/pulse/native|" \
    jukebox.service > "$TMP_SERVICE_FILE"

# Install the service file
sudo cp "$TMP_SERVICE_FILE" /etc/systemd/system/jukebox.service
sudo systemctl daemon-reload

# Clean up temporary file
rm -f "$TMP_SERVICE_FILE"

echo "✅ Service installed with path: $JUKEBOX_PATH"

# Create polkit rules for system control (shutdown/reboot)
echo "🔐 Setting up polkit rules..."

# Detect which polkit version is available
if [ -d "/etc/polkit-1/rules.d" ]; then
    # Modern polkit (0.106+) - uses JavaScript rules
    echo "   Using modern polkit rules format..."
    sudo tee /etc/polkit-1/rules.d/50-jukebox.rules > /dev/null << 'EOF'
/* Allow pi user to manage jukebox service and system power */
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.systemd1.manage-units" &&
         (action.lookup("unit") == "jukebox.service" ||
          action.lookup("unit") == "poweroff.target" ||
          action.lookup("unit") == "reboot.target")) &&
        subject.user == "__INSTALL_USER__") {
        return polkit.Result.YES;
    }
});
EOF
    sudo sed -i "s/__INSTALL_USER__/$INSTALL_USER/g" /etc/polkit-1/rules.d/50-jukebox.rules
    if [ $? -eq 0 ]; then
        echo "✅ Modern polkit rules installed"
    else
        echo "⚠️ Failed to install polkit rules (non-fatal)"
    fi
elif [ -d "/etc/polkit-1/localauthority/50-local.d" ]; then
    # Legacy polkit - uses .pkla files
    echo "   Using legacy polkit format..."
    sudo tee /etc/polkit-1/localauthority/50-local.d/50-jukebox.pkla > /dev/null << EOF
[Allow jukebox system control]
Identity=unix-user:$INSTALL_USER
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:poweroff.target;system:reboot.target

[Allow jukebox service control]  
Identity=unix-user:$INSTALL_USER
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:jukebox.service
EOF
    if [ $? -eq 0 ]; then
        echo "✅ Legacy polkit rules installed"
    else
        echo "⚠️ Failed to install polkit rules (non-fatal)"
    fi
else
    # Neither directory exists - try to create modern polkit directory
    echo "   Creating polkit rules directory..."
    if sudo mkdir -p /etc/polkit-1/rules.d; then
        sudo tee /etc/polkit-1/rules.d/50-jukebox.rules > /dev/null << 'EOF'
/* Allow pi user to manage jukebox service and system power */
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.systemd1.manage-units" &&
         (action.lookup("unit") == "jukebox.service" ||
          action.lookup("unit") == "poweroff.target" ||
          action.lookup("unit") == "reboot.target")) &&
        subject.user == "__INSTALL_USER__") {
        return polkit.Result.YES;
    }
});
EOF
        sudo sed -i "s/__INSTALL_USER__/$INSTALL_USER/g" /etc/polkit-1/rules.d/50-jukebox.rules
        if [ $? -eq 0 ]; then
            echo "✅ Polkit rules installed (created directory)"
        else
            echo "⚠️ Failed to install polkit rules (non-fatal)"
        fi
    else
        echo "⚠️ Could not create polkit directory - you may need to enter password for system operations"
    fi
fi

# Enable jukebox service
echo "🚀 Enabling jukebox service..."
sudo systemctl enable jukebox

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your configuration:"
echo "   nano .env"
echo ""
echo "2. Run setup validation:"
echo "   python3 setup_env.py"
echo ""
echo "3. Start the jukebox service:"
echo "   sudo systemctl start jukebox"
echo ""
echo "4. Check service status:"
echo "   sudo systemctl status jukebox"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u jukebox -f"
echo ""
echo "6. Validate environment (optional):"
echo "   ./venv/bin/python tests/setup_env.py"
echo ""
echo "🔄 A reboot is recommended to ensure all hardware interfaces are active:"
echo "   sudo reboot"