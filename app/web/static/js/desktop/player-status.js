/**
 * Desktop Player Status Component
 * Displays current track information, album art, playlist, and playback controls
 */

function control(action) {
    apiFetch(`/api/mediaplayer/${action}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Optionally show feedback
        });
}

function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return '';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function updateDesktopTrackInfo(data) {
    const infoDiv = document.getElementById('track-info');
    const thumbDiv = document.getElementById('track-thumb');
    
    if (data.current_track) {
        infoDiv.innerHTML = `
            <strong>${data.current_track.artist}</strong><br>
            <strong>${data.current_track.title}</strong><br>
            Album: ${data.current_track.album}<br>
            Year: ${data.current_track.year}<br>
            Status: ${data.status}<br>
            Track: ${data.current_track.track_number} of ${data.playlist.length} in playlist <br>
            Playing on: ${data.chromecast_device} | Volume: ${data.volume}
        `;
        let thumbUrl = data.current_track.thumb;
        if (thumbUrl) {
            thumbDiv.innerHTML = `<img src="${thumbUrl}" alt="Cover" style="width:120px;height:120px;object-fit:cover;border-radius:10px;box-shadow:0 2px 8px #aaa;" />`;
        } else {
            thumbDiv.innerHTML = '';
        }
    } else {
        infoDiv.innerHTML = data.message || 'No track loaded';
        thumbDiv.innerHTML = '';
    }

    // Render playlist
    const playlistDiv = document.getElementById('playlist-list');
    if (data.playlist && Array.isArray(data.playlist)) {
        let html = '';
        for (let i = 0; i < data.playlist.length; i++) {
            const track = data.playlist[i];
            const isCurrent = data.current_track && (track.track_number === data.current_track.track_number);
            html += `<div class="list-group-item d-flex justify-content-between align-items-center ${isCurrent ? 'active' : ''}">` +
                `<div class="d-flex align-items-center gap-3">` +
                    `<div class="text-muted" style="width:24px;text-align:right;">${track.track_number || i+1}</div>` +
                    `<div>${track.title || ''}</div>` +
                `</div>` +
                `<div class="text-muted">${formatDuration(track.duration)}</div>` +
            `</div>`;
        }
        playlistDiv.innerHTML = html;
    } else {
        playlistDiv.innerHTML = '<div class="list-group-item text-center text-muted">No playlist loaded</div>';
    }
}

// Initialize player status on page load
(function() {
    // Fetch initial state from API
    async function initPlayerStatus() {
        try {
            const response = await fetch('/api/mediaplayer/status');
            if (response.ok) {
                const data = await response.json();
                updateDesktopTrackInfo(data);
            }
        } catch (error) {
            console.error('Error fetching initial player status:', error);
        }
    }

    // WebSocket for live track info
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
            if (msg.type === 'current_track') {
                const payload = msg.payload || {};
                if (typeof updateDesktopTrackInfo === 'function') {
                    updateDesktopTrackInfo(payload);
                }
            }
        } 
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPlayerStatus);
    } else {
        initPlayerStatus();
    }
})();
