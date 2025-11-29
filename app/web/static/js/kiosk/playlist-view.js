/**
 * Kiosk Playlist View Component
 * Displays current playlist with live WebSocket updates
 */

(function() {
    let playlistWs = null;
    
    // Expose initPlaylistView globally so kiosk loader can call it
    window.initPlaylistView = async function() {
        // Fetch initial state from API
        try {
            const response = await fetch('/api/mediaplayer/status');
            if (response.ok) {
                const data = await response.json();
                updatePlaylistView(data);
            }
        } catch (error) {
            console.error('Error fetching initial playlist:', error);
        }
        
        // Connect to WebSocket for live updates
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        playlistWs = new WebSocket(`${wsProtocol}//${window.location.host}/ws/mediaplayer/status`);

        playlistWs.onmessage = function(event) {
            const msg = JSON.parse(event.data);
            // Support both new envelope {type, payload} and legacy direct payload
            if (msg && msg.type) {
                if (msg.type === 'ping') return;
                if (msg.type === 'error') {
                    console.error('Playlist WS error:', msg.payload && msg.payload.message);
                    document.getElementById('kiosk-playlist-info').textContent = 'Connection error';
                    return;
                }
                const payload = msg.payload || {};
                updatePlaylistView(payload);
            } else {
                if (msg && msg.status === 'ping') return;
                updatePlaylistView(msg);
            }
        };
        
        playlistWs.onerror = function(error) {
            console.error('Playlist WebSocket error:', error);
            document.getElementById('kiosk-playlist-info').textContent = 'Connection error';
        };
        
        playlistWs.onclose = function() {
            setTimeout(window.initPlaylistView, 3000);
        };
    };
    
    function updatePlaylistView(data) {
        const container = document.getElementById('kiosk-playlist-container');
        const infoDiv = document.getElementById('kiosk-playlist-info');
        
        if (data.playlist && Array.isArray(data.playlist) && data.playlist.length > 0) {
            infoDiv.textContent = `${data.playlist.length} tracks`;
            
            let html = '';
            for (let i = 0; i < data.playlist.length; i++) {
                const track = data.playlist[i];
                const isCurrent = data.current_track && (track.track_number === data.current_track.track_number);

                html += `<div class="list-group-item kiosk-playlist-item d-flex justify-content-between align-items-center ${isCurrent ? 'active' : ''}"
                    onclick="window.playTrackAtIndex(${i})" style="cursor:pointer;">` +
                    `<div class="d-flex align-items-center gap-3 flex-grow-1">` +
                        `<div class="track-number">${track.track_number || i+1}</div>` +
                        `<div class="flex-grow-1">` +
                            `<div class="fw-bold">${track.title || 'Unknown Title'}</div>` +
                            `<div class="text-muted small">${track.artist || ''}</div>` +
                        `</div>` +
                    `</div>` +
                    `<div class="text-muted small">${formatDuration(track.duration)}</div>` +
                `</div>`;
            }
            container.innerHTML = html;
            // Play a track at the given index
            window.playTrackAtIndex = async function(index) {
                try {
                    const response = await fetch('/api/mediaplayer/play_track', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ track_index: index })
                    });
                    if (!response.ok) {
                        console.error('Failed to play track at index', index);
                    }
                } catch (error) {
                    console.error('Error playing track at index', index, error);
                }
            };
        } else {
            infoDiv.textContent = 'No tracks';
            container.innerHTML = `<div class="text-center text-muted py-5">
                <i class="mdi mdi-music-note-off" style="font-size: 48px;"></i>
                <p class="mt-3">No playlist loaded</p>
            </div>`;
        }
    }
    
    function formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return '';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    }
    
    // Auto-initialize when component loads (only if required DOM elements exist)
    function safeInit() {
        if (document.getElementById('kiosk-playlist-container')) {
            window.initPlaylistView();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
    
    // Clean up WebSocket on page unload
    window.addEventListener('beforeunload', function() {
        if (playlistWs) {
            playlistWs.close();
        }
    });
})();
