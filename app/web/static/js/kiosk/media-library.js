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
                showError('Failed to load artists');
            }
        } catch (error) {
            console.error('Error fetching artists:', error);
            showError('Error loading artists');
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
        let html = '<div class="d-flex flex-wrap justify-content-center">';
        groups.forEach(group => {
            html += `
                <button class="btn btn-primary library-group-btn" onclick="window.showArtistsView('${group.name}')">
                    ${group.name}
                </button>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    }
    
    window.showArtistsView = function(groupName) {
        currentView = 'artists';
        currentGroup = groupName;
        const group = groups.find(g => g.name === groupName);
        const backBtn = document.getElementById('library-back-btn');
        
        document.getElementById('library-title').textContent = `Artists: ${groupName}`;
        if (backBtn) {
            backBtn.classList.remove('library-back-btn-hidden');
        }
        
        // Filter artists by group
        const filteredArtists = allArtists.filter(artist => {
            const firstChar = (artist.name || '').toUpperCase().charAt(0);
            return firstChar >= group.range[0] && firstChar < group.range[1];
        });
        
        const content = document.getElementById('library-content');
        if (filteredArtists.length === 0) {
            content.innerHTML = '<div class="text-center text-muted py-5">No artists found</div>';
            return;
        }
        
        let html = '<table class="table library-table"><tbody>';
        filteredArtists.forEach(artist => {
            html += `
                <tr onclick="window.showAlbumsView('${artist.id}', '${escapeHtml(artist.name)}')">
                    <td>
                        <i class="mdi mdi-account-music"></i> 
                        <strong>${escapeHtml(artist.name)}</strong>
                    </td>
                    <td class="text-end">
                        <i class="mdi mdi-chevron-right"></i>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
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
            const response = await fetch(`/api/subsonic/artist/${artistId}`);
            if (!response.ok) throw new Error('Failed to load albums');
            
            const albums = await response.json();
            
            if (albums.length === 0) {
                content.innerHTML = '<div class="text-center text-muted py-5">No albums found</div>';
                return;
            }
            
            let html = '<table class="table library-table"><tbody>';
            albums.forEach(album => {
                const year = album.year ? ` (${album.year})` : '';
                html += `
                    <tr onclick="window.playAlbum('${album.id}', '${escapeHtml(album.name)}')">
                        <td>
                            <i class="mdi mdi-album"></i> 
                            <strong>${escapeHtml(album.name)}</strong>${year}
                        </td>
                        <td class="text-end">
                            <i class="mdi mdi-play-circle text-success" style="font-size: 24px;"></i>
                        </td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
            content.innerHTML = html;
        } catch (error) {
            console.error('Error fetching albums:', error);
            showError('Error loading albums');
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
                showError('Failed to play album');
            }
        } catch (error) {
            console.error('Error playing album:', error);
            showError('Error starting playback');
        }
    };
    
    function showError(message) {
        const content = document.getElementById('library-content');
        content.innerHTML = `
            <div class="text-center text-danger py-5">
                <i class="mdi mdi-alert-circle" style="font-size: 48px;"></i>
                <p class="mt-3">${message}</p>
            </div>
        `;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Auto-initialize when component loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.initMediaLibrary);
    } else {
        window.initMediaLibrary();
    }
})();
