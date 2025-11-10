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
            const response = await fetch('/api/mediaplayer/current_track');
            if (response.ok) {
                const data = await response.json();
                updatePlaylistView(data);
            }
        } catch (error) {
            console.error('Error fetching initial playlist:', error);
        }
        
        // Connect to WebSocket for live updates
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        playlistWs = new WebSocket(`${wsProtocol}//${window.location.host}/ws/mediaplayer/current_track`);
        
        playlistWs.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.status === 'ping') {
                return;
            }
            updatePlaylistView(data);
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
                
                html += `<div class="list-group-item kiosk-playlist-item d-flex justify-content-between align-items-center ${isCurrent ? 'active' : ''}">` +
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
    
    // Auto-initialize when component loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.initPlaylistView);
    } else {
        window.initPlaylistView();
    }
    
    // Clean up WebSocket on page unload
    window.addEventListener('beforeunload', function() {
        if (playlistWs) {
            playlistWs.close();
        }
    });
})();
