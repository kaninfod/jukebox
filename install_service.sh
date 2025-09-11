#!/bin/bash

# Raspberry Pi Jukebox Installation Script
# Complete setup for a clean Raspberry Pi 4 running Raspberry Pi OS 64-bit

set -e  # Exit on any error

echo "🎵 Raspberry Pi Jukebox Installation Script"
echo "============================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "❌ This script is designed for Raspberry Pi hardware"
    exit 1
fi

echo "✅ Raspberry Pi detected"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    mariadb-client \
    libmariadb-dev \
    build-essential \
    python3-rpi.gpio \
    python3-spidev \
    i2c-tools \
    python3-smbus \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5

echo "✅ System dependencies installed"

# Enable hardware interfaces
echo "🔧 Enabling SPI and I2C interfaces..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

# Add pi user to required groups
echo "👤 Adding pi user to hardware groups..."
sudo usermod -a -G gpio,spi,i2c pi

echo "✅ Hardware interfaces configured"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

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
sudo cp jukebox.service /etc/systemd/system/
sudo systemctl daemon-reload

# Create polkit rules for system control (shutdown/reboot)
echo "🔐 Setting up polkit rules..."
sudo tee /etc/polkit-1/localauthority/50-local.d/50-jukebox.pkla > /dev/null << EOF
[Allow jukebox system control]
Identity=unix-user:pi
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:poweroff.target;system:reboot.target

[Allow jukebox service control]  
Identity=unix-user:pi
Action=org.freedesktop.systemd1.manage-units
ResultActive=yes
Object=system:jukebox.service
EOF

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
echo "🔄 A reboot is recommended to ensure all hardware interfaces are active:"
echo "   sudo reboot"