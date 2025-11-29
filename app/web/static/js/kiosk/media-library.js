/**
 * Kiosk Media Library Component
 * 3-level navigation: Groups → Artists → Albums → Play
 */

(function() {
    let allArtists = [];
    let currentView = 'groups'; // 'groups', 'artists', 'albums'
    let currentGroup = null;
    let currentArtist = null;
    
    const groups = [
        { name: 'A-D', range: ['A', 'E'] },
        { name: 'E-H', range: ['E', 'I'] },
        { name: 'I-L', range: ['I', 'M'] },
        { name: 'M-P', range: ['M', 'Q'] },
        { name: 'Q-T', range: ['Q', 'U'] },
        { name: 'U-Z', range: ['U', '[']}  // '[' is after 'Z' in ASCII
    ];
    
    // Expose functions globally
    window.initMediaLibrary = async function() {
        await fetchAllArtists();
        showGroupsView();
    };
    
    window.libraryGoBack = function() {
        const backBtn = document.getElementById('library-back-btn');
        if (currentView === 'artists') {
            showGroupsView();
        } else if (currentView === 'albums') {
            showArtistsView(currentGroup);
        }
    };
    
    async function fetchAllArtists() {
        try {
            const response = await fetch('/api/subsonic/artists');
            if (response.ok) {
                allArtists = await response.json();
            } else {
                showKioskToast('Failed to load artists', { theme: 'error' });

            }
        } catch (error) {
            console.error('Error fetching artists:', error);
            showKioskToast('Error loading artists', { theme: 'error' });
        }
    }
    
    function showGroupsView() {
        currentView = 'groups';
        currentGroup = null;
        const backBtn = document.getElementById('library-back-btn');
        document.getElementById('library-title').textContent = 'Music Library';
        if (backBtn) {
            backBtn.classList.add('library-back-btn-hidden');
        }

        const content = document.getElementById('library-content');
        let html = '<div class="library-cards-container"><div class="row g-3">';
        groups.forEach(group => {
            html += renderGroupCard(group);
        });
        html += '</div></div>';
        content.innerHTML = html;
    }

    // Template function for group card
    function renderGroupCard(group) {
        return `
            <div class="col-4">
                <div class="card library-group-card" onclick="window.showArtistsView('${group.name}')">
                    <div class="card-body text-center">
                        <h2 class="display-4">${group.name}</h2>
                    </div>
                </div>
            </div>
        `;
    }
    
    window.showArtistsView = async function(groupName) {
        currentView = 'artists';
        currentGroup = groupName;
        const backBtn = document.getElementById('library-back-btn');

        document.getElementById('library-title').textContent = `Artists: ${groupName}`;
        if (backBtn) {
            backBtn.classList.remove('library-back-btn-hidden');
        }

        const content = document.getElementById('library-content');
        content.innerHTML = '<div class="text-center text-muted py-5"><i class="mdi mdi-loading mdi-spin" style="font-size: 48px;"></i><p class="mt-3">Loading artists...</p></div>';

        try {
            const params = new URLSearchParams({ group_name: groupName });
            const response = await fetch(`/kiosk/html/media_library/artists?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to load artists');
            const html = await response.text();
            content.innerHTML = html;
        } catch (error) {
            console.error('Error fetching artists:', error);
            showKioskToast('Error loading artists', { theme: 'error' });
        }
    };
    
    window.showAlbumsView = async function(artistId, artistName) {
        currentView = 'albums';
        currentArtist = { id: artistId, name: artistName };
        const backBtn = document.getElementById('library-back-btn');

        document.getElementById('library-title').textContent = artistName;
        if (backBtn) {
            backBtn.classList.remove('library-back-btn-hidden');
        }

        const content = document.getElementById('library-content');
        content.innerHTML = '<div class="text-center text-muted py-5"><i class="mdi mdi-loading mdi-spin" style="font-size: 48px;"></i><p class="mt-3">Loading albums...</p></div>';

        try {
            const params = new URLSearchParams({
                artist_id: artistId,
                artist_name: artistName
            });
            const response = await fetch(`/kiosk/html/media_library/albums?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to load albums');
            const html = await response.text();
            content.innerHTML = html;
        } catch (error) {
            console.error('Error fetching albums:', error);
            showKioskToast('Error loading albums', { theme: 'error' });
        }
    };
    
    window.playAlbum = async function(albumId, albumName) {
        const content = document.getElementById('library-content');
        content.innerHTML = '<div class="text-center text-muted py-5"><i class="mdi mdi-loading mdi-spin" style="font-size: 48px;"></i><p class="mt-3">Starting playback...</p></div>';
        
        try {
            const response = await fetch(`/api/mediaplayer/play_album_from_albumid/${albumId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                // Navigate back to player
                if (typeof navigateTo === 'function') {
                    navigateTo('player');
                }
            } else {
                showKioskToast('Failed to play album', { theme: 'error' });
            }
        } catch (error) {
            console.error('Error playing album:', error);
            showKioskToast('Error starting playback', { theme: 'error' });
        }
    };
    
    console.log('[MediaLibrary] Defining startNfcEncoding...');
    
    // Start NFC encoding session for album
    window.startNfcEncoding = async function(albumId, albumName) {
        console.log('[MediaLibrary] startNfcEncoding called with:', albumId, albumName);
        console.log('[Library] Starting NFC encoding for album:', albumName, '(id:', albumId, ')');
        
        try {
            const response = await fetch('/api/nfc-encoding/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ album_id: albumId })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start encoding session');
            }
            
            console.log('[Library] Encoding session started, loading NFC component');
            
            // Load NFC encoding component
            if (typeof kioskLoader !== 'undefined') {
                kioskLoader.loadContent('nfc', { albumId, albumName });
            } else {
                console.error('[Library] kioskLoader not available');
                if (typeof showKioskToast === 'function') {
                    showKioskToast('Error: Component loader not available', { theme: 'error' });
                }
            }
        } catch (error) {
            console.error('[Library] Error starting NFC encoding:', error);
            if (typeof showKioskToast === 'function') {
                showKioskToast(`Error: ${error.message}`, { theme: 'error' });
            }
        }
    };
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Auto-initialize when component loads (only if required DOM elements exist)
    function safeInit() {
        if (document.getElementById('library-content')) {
            window.initMediaLibrary();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
})();
