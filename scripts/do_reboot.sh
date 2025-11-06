#!/bin/bash
# Reboot script for jukebox system
# This script runs independently of the web application systemd service
# to avoid systemd security restrictions

# Ensure we can write to the log file (create if doesn't exist)
touch /tmp/jukebox_reboot.log 2>/dev/null || {
    # If we can't write to /tmp, try home directory
    touch /home/pi/jukebox_reboot.log
    LOG_FILE="/home/pi/jukebox_reboot.log"
} && {
    LOG_FILE="/tmp/jukebox_reboot.log"
}

# Log script start with full environment info
{
    echo "$(date): === REBOOT SCRIPT STARTED ==="
    echo "$(date): PID=$$, PPID=$PPID"
    echo "$(date): USER=$(whoami), HOME=$HOME"
    echo "$(date): PATH=$PATH"
    echo "$(date): PWD=$(pwd)"
    echo "$(date): Script: $0"
} >> "$LOG_FILE"

# Small delay to ensure HTTP response is sent before reboot
sleep 3

# Log before reboot attempt
echo "$(date): About to execute reboot command" >> "$LOG_FILE"

# Execute the reboot command (we know this works from our testing)
sudo /usr/bin/systemctl reboot >> "$LOG_FILE" 2>&1

# This line should not be reached if reboot works
echo "$(date): ERROR - Reboot command completed without rebooting!" >> "$LOG_FILE"