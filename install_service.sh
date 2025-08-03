#!/bin/bash

# Jukebox Service Installation Script
# Run this script on your Raspberry Pi to set up the jukebox as a system service

set -e  # Exit on any error

echo "🎵 Installing Jukebox Service..."

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "❌ This script should be run as the 'pi' user"
    echo "   Please run: ./install_service.sh"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "jukebox.service" ]; then
    echo "❌ jukebox.service file not found"
    echo "   Please run this script from the jukebox directory"
    exit 1
fi

# Check if required files exist
if [ ! -f "app/main.py" ]; then
    echo "❌ app/main.py not found"
    echo "   Please ensure the jukebox application is in the current directory"
    exit 1
fi

# Check if requirements are installed (try importing uvicorn)
echo "🔍 Installing Python dependencies..."
echo "📦 Installing system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev build-essential

# Install all requirements from requirements.txt
echo "🐍 Installing Python packages from requirements.txt..."
pip3 install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed successfully"

# Check if service already exists and remove it
if sudo systemctl is-enabled jukebox.service >/dev/null 2>&1; then
    echo "🔄 Removing existing jukebox service..."
    sudo systemctl stop jukebox.service 2>/dev/null || true
    sudo systemctl disable jukebox.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/jukebox.service
    sudo systemctl daemon-reload
    echo "✅ Existing service removed"
fi

# Copy service file to systemd
echo "📋 Installing systemd service..."
sudo systemctl stop jukebox.service 2>/dev/null || true
sudo cp jukebox.service /etc/systemd/system/

# Reload systemd and enable the service
echo "🔄 Enabling jukebox service..."
sudo systemctl daemon-reload
sudo systemctl enable jukebox.service

# Start the service
echo "🚀 Starting jukebox service..."
sudo systemctl start jukebox.service

# Show status
echo ""
echo "✅ Jukebox service installed successfully!"
echo ""
echo "📊 Service Status:"
sudo systemctl status jukebox.service --no-pager -l

echo ""
echo "🎛️  Useful Commands:"
echo "   Check status:    sudo systemctl status jukebox"
echo "   View logs:       sudo journalctl -u jukebox -f"
echo "   Stop service:    sudo systemctl stop jukebox"
echo "   Start service:   sudo systemctl start jukebox"
echo "   Restart service: sudo systemctl restart jukebox"
echo "   Disable startup: sudo systemctl disable jukebox"
echo ""
echo "🌐 Your jukebox should now be accessible at:"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo ""
