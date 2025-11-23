#!/bin/bash
# Access via direct IP to use ALLOW_LOCAL_API_BYPASS (no auth needed)
# Clear cache on startup for fresh CSS/JS loading
#rm -rf ~/.cache/mozilla/firefox/*.default*/cache2/*
#firefox http://192.168.68.104:8000/status?kiosk=1 --kiosk


#!/usr/bin/env bash
set -euo pipefail

# Configuration
SERVICE="jukebox"
URL="http://192.168.68.104:8000/status?kiosk=1"
LOG="/home/pi/shared/jukebox/scripts/start-kiosk.log"
TIMEOUT=300     # seconds to wait before giving up
INTERVAL=2      # polling interval (seconds)

echo "$(date -Is) start-kiosk: script started" >> "$LOG"

# Wait until the service is active (with timeout)
elapsed=0
while ! systemctl is-active --quiet "$SERVICE"; do
  if [ "$elapsed" -ge "$TIMEOUT" ]; then
    echo "$(date -Is) start-kiosk: timeout waiting for $SERVICE (elapsed=$elapsed s)" >> "$LOG"
    exit 1
  fi
  echo "$(date -Is) start-kiosk: $SERVICE not active yet (elapsed=${elapsed}s), sleeping $INTERVAL" >> "$LOG"
  sleep "$INTERVAL"
  elapsed=$((elapsed + INTERVAL))
done

echo "$(date -Is) start-kiosk: $SERVICE is active, preparing to launch Firefox" >> "$LOG"

# If firefox is already running, do nothing
if pgrep -x firefox >/dev/null 2>&1; then
  echo "$(date -Is) start-kiosk: firefox already running, exiting" >> "$LOG"
  exit 0
fi

# Clear Firefox cache for all profiles (safe: only removes contents of cache2 directories)
CACHE_BASE="${HOME:-/home/pi}/.cache/mozilla/firefox"
if [ -d "$CACHE_BASE" ]; then
  for prof in "$CACHE_BASE"/*; do
    if [ -d "$prof/cache2" ]; then
      echo "$(date -Is) start-kiosk: clearing cache in $prof/cache2" >> "$LOG"
      rm -rf "$prof/cache2/"* || echo "$(date -Is) start-kiosk: failed to clear $prof/cache2" >> "$LOG"
    fi
  done
else
  echo "$(date -Is) start-kiosk: no firefox cache directory at $CACHE_BASE" >> "$LOG"
fi

echo "$(date -Is) start-kiosk: launching Firefox in kiosk mode" >> "$LOG"

# Export DISPLAY if needed; usually set in the desktop session. Uncomment if required:
# export DISPLAY=:0

nohup firefox "$URL" --kiosk >> "$LOG" 2>&1 &

echo "$(date -Is) start-kiosk: firefox launched (pid $!)" >> "$LOG"
exit 0

