// Control and navigation functions (moved from template)
function control(action) {
    apiFetch(`/api/mediaplayer/${action}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Optionally show feedback
        });
}

// Auto-initialize when component loads (only if required DOM elements exist)
function safeInit() {
    if (document.getElementById('kiosk-track-info')) {
        window.initPlayerStatus();
    }
}

function updateKioskTrackInfo(data) {
    const kioskInfoDiv = document.getElementById('kiosk-track-info');
    const kioskThumbDiv = document.getElementById('kiosk-track-thumb');
    const deviceDiv = document.getElementById('current-device');
    const volumeFill = document.getElementById('kiosk-volume-fill');
    const volumeText = document.getElementById('kiosk-volume-text');
    
    // Exit early if player status component is not currently loaded
    if (!kioskInfoDiv || !kioskThumbDiv) {
        return;
    }
    
    // Update Chromecast device name
    if (data.chromecast_device && deviceDiv) {
        deviceDiv.textContent = data.chromecast_device;
    }
    
    // Update volume bar
    if (data.volume !== undefined && volumeFill && volumeText) {
        const volume = parseInt(data.volume) || 0;
        volumeFill.style.height = volume + '%';
        volumeText.textContent = volume + '%';
    }
    
    if (data.current_track) {
        kioskInfoDiv.innerHTML = `
            <div class="kiosk-status">
                <span><i class="mdi mdi-music-note"></i> Track ${data.current_track.track_number} of ${data.playlist.length}</span>
            </div>
            <div class="kiosk-artist">${data.current_track.artist}</div>
            <div class="kiosk-title">${data.current_track.title}</div>
            <div class="kiosk-album">${data.current_track.album} (${data.current_track.year})</div>
        `;
        let thumbUrl = data.current_track.thumb;
        if (thumbUrl) {
            kioskThumbDiv.innerHTML = `<img src="${thumbUrl}" alt="Album Cover" />`;
        } else {
            kioskThumbDiv.innerHTML = '<div class="kiosk-no-cover"><i class="mdi mdi-music"></i></div>';
        }
    } else {
        kioskInfoDiv.innerHTML = '<div class="kiosk-no-track">' + (data.message || 'No track loaded') + '</div>';
        kioskThumbDiv.innerHTML = '<div class="kiosk-no-cover"><i class="mdi mdi-music"></i></div>';
    }
}

/**
 * Kiosk Player Status Component
 * Displays current track information, album art, and volume
 */

(function() {
    // Expose initPlayerStatus globally so kiosk loader can call it
    window.initPlayerStatus = async function() {
        // Fetch initial state from API
        try {
        const response = await fetch('/api/mediaplayer/status');
            if (response.ok) {
                const data = await response.json();
                updateKioskTrackInfo(data);
            }
        } catch (error) {
            console.error('Error fetching initial player status:', error);
        }
    };
    
    // WebSocket for live track info (wrapped in IIFE to avoid redeclaration)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/mediaplayer/status`);
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        // Support both new envelope {type, payload} and legacy direct payload
        if (msg && msg.type) {
            if (msg.type === 'ping') return;
            if (msg.type === 'error') {
                console.error('Player status error:', msg.payload && msg.payload.message);
                return;
            }
            // for type 'current_track', payload contains the actual data
            const payload = msg.payload || {};
            if (typeof window.updateKioskTrackInfo === 'function') {
                window.updateKioskTrackInfo(payload);
            }
        } else {
            // legacy format
            if (msg && msg.status === 'ping') return;
            if (typeof window.updateKioskTrackInfo === 'function') {
                window.updateKioskTrackInfo(msg);
            }
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
})();
