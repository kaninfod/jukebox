/**
 * Toast Notification System - Code Examples
 * 
 * Copy these patterns into your JavaScript to add toasts to your features
 */

// ============================================================================
// BASIC EXAMPLES
// ============================================================================

// Show a simple success message
toast.success('Album added to queue!');

// Show an error with custom title
toast.error('Failed to connect to device', 'Connection Error');

// Show warning that doesn't auto-dismiss
toast.warning('This action will remove all data', 'Caution', 0);

// Show info message for 3 seconds
toast.info('Syncing library...', 'Syncing', 3000);


// ============================================================================
// API CALL PATTERNS
// ============================================================================

// Pattern 1: Simple API call with success/error handling
async function playAlbum(albumId) {
    try {
        const response = await fetch(`/api/album/${albumId}/play`, {
            method: 'POST'
        });
        
        if (response.ok) {
            toast.success('Album started playing!');
        } else {
            const error = await response.json();
            toast.error(error.detail || 'Failed to play album', 'Playback Error');
        }
    } catch (error) {
        toast.error(`Network error: ${error.message}`, 'Connection Failed');
    }
}


// Pattern 2: Form submission with validation
async function submitPlaylist(event) {
    event.preventDefault();
    
    // Get form data
    const formData = new FormData(event.target);
    const name = formData.get('name');
    
    // Validate
    if (!name || name.trim() === '') {
        toast.warning('Please enter a playlist name', 'Validation Error');
        return;
    }
    
    // Submit
    try {
        const response = await fetch('/api/playlists', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name.trim() })
        });
        
        if (response.ok) {
            toast.success(`Playlist "${name}" created!`, 'Created');
            event.target.reset();
            // Optionally reload playlists...
        } else {
            const error = await response.json();
            toast.error(error.detail || 'Failed to create playlist', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Network Error');
    }
}


// Pattern 3: Long-running operations with progress
async function encodeNFCTag(tagType) {
    // Show non-dismissing "loading" toast
    toast.info('Encoding NFC tag, please hold it to the device...', 'Encoding', 0);
    
    try {
        const response = await fetch('/api/nfc/encode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: tagType })
        });
        
        if (response.ok) {
            toast.success('NFC tag encoded successfully!', 'Complete');
        } else {
            const error = await response.json();
            toast.error(error.detail || 'Failed to encode tag', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Encoding Failed');
    }
}


// ============================================================================
// CONDITIONAL LOGIC PATTERNS
// ============================================================================

// Pattern 4: Check before taking action
async function toggleFavorite(albumId, isFavorite) {
    const action = isFavorite ? 'adding to' : 'removing from';
    const endpoint = isFavorite ? 'POST' : 'DELETE';
    
    try {
        const response = await fetch(`/api/album/${albumId}/favorite`, {
            method: endpoint
        });
        
        if (response.ok) {
            const message = isFavorite 
                ? 'Added to your favorites!' 
                : 'Removed from favorites';
            toast.success(message);
        } else {
            toast.error('Failed to update favorites', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Network Error');
    }
}


// Pattern 5: Show different messages based on state
function attemptConnect(deviceName, isCurrentDevice) {
    if (isCurrentDevice) {
        // User tried to select already-active device
        toast.info(
            `You're already connected to ${deviceName}`,
            'Already Active',
            3000
        );
        return;
    }
    
    // Proceed with switching
    switchDevice(deviceName);
}


// Pattern 6: Conditional error handling
async function deleteAlbum(albumId, albumName) {
    if (!confirm(`Are you sure you want to delete "${albumName}"?`)) {
        toast.warning('Deletion cancelled', 'Cancelled');
        return;
    }
    
    try {
        const response = await fetch(`/api/album/${albumId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            toast.success(`"${albumName}" has been deleted`, 'Deleted');
            // Refresh album list...
        } else if (response.status === 404) {
            toast.warning('Album not found', 'Not Found');
        } else if (response.status === 403) {
            toast.error('You do not have permission to delete this album', 'Permission Denied');
        } else {
            toast.error('Failed to delete album', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Network Error');
    }
}


// ============================================================================
// ASYNC OPERATIONS PATTERNS
// ============================================================================

// Pattern 7: Promise chain with toasts
function syncLibrary() {
    // Show loading toast that doesn't auto-dismiss
    toast.info('Syncing your music library...', 'Syncing', 0);
    
    fetch('/api/library/sync', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toast.success(
                    `Synced ${data.count} tracks successfully!`,
                    'Sync Complete'
                );
            } else {
                toast.error(data.error || 'Sync failed', 'Error');
            }
        })
        .catch(error => {
            toast.error(error.message, 'Sync Failed');
        });
}


// Pattern 8: Async/await with retry logic
async function connectWithRetry(deviceName, maxRetries = 3) {
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch('/api/chromecast/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device: deviceName })
            });
            
            if (response.ok) {
                toast.success(`Connected to ${deviceName}`, 'Connected');
                return true;
            }
            
            lastError = await response.json();
        } catch (error) {
            lastError = error;
        }
        
        if (attempt < maxRetries) {
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, 1000));
            toast.info(
                `Retrying connection... (${attempt}/${maxRetries})`,
                'Connecting',
                2000
            );
        }
    }
    
    // All retries failed
    toast.error(
        `Failed to connect after ${maxRetries} attempts: ${lastError?.message || 'Unknown error'}`,
        'Connection Failed'
    );
    return false;
}


// ============================================================================
// BATCH OPERATIONS PATTERNS
// ============================================================================

// Pattern 9: Multiple operations with progress feedback
async function addAlbumsToPlaylist(playlistId, albumIds) {
    let successful = 0;
    let failed = 0;
    
    // Show initial toast
    toast.info(
        `Adding ${albumIds.length} albums to playlist...`,
        'Processing',
        0
    );
    
    for (const albumId of albumIds) {
        try {
            const response = await fetch(
                `/api/playlist/${playlistId}/album/${albumId}`,
                { method: 'POST' }
            );
            
            if (response.ok) {
                successful++;
            } else {
                failed++;
            }
        } catch (error) {
            failed++;
        }
    }
    
    // Show results
    if (failed === 0) {
        toast.success(
            `Successfully added all ${successful} albums!`,
            'Complete'
        );
    } else {
        toast.warning(
            `Added ${successful} albums, ${failed} failed`,
            'Partial Success'
        );
    }
}


// ============================================================================
// EVENT HANDLER PATTERNS
// ============================================================================

// Pattern 10: Event delegation with toasts
document.addEventListener('click', async function(event) {
    // Handle all ".play-button" clicks
    if (event.target.classList.contains('play-button')) {
        const albumId = event.target.dataset.albumId;
        const albumName = event.target.dataset.albumName;
        
        event.preventDefault();
        
        try {
            const response = await fetch(`/api/album/${albumId}/play`, {
                method: 'POST'
            });
            
            if (response.ok) {
                toast.success(`Now playing "${albumName}"!`);
            } else {
                toast.error(`Failed to play "${albumName}"`, 'Error');
            }
        } catch (error) {
            toast.error(error.message, 'Playback Error');
        }
    }
});


// ============================================================================
// TIMING AND STATE PATTERNS
// ============================================================================

// Pattern 11: Toast with timeout handling
let currentOperation = null;

async function performLongOperation() {
    // Cancel previous operation if still running
    if (currentOperation) {
        toast.warning('Previous operation is still running', 'Busy');
        return;
    }
    
    currentOperation = true;
    toast.info('Operation started...', 'Processing', 0);
    
    try {
        // Simulate long operation
        await new Promise(resolve => setTimeout(resolve, 3000));
        toast.success('Operation completed successfully!');
    } catch (error) {
        toast.error(error.message, 'Operation Failed');
    } finally {
        currentOperation = false;
    }
}


// Pattern 12: Debounced operations with feedback
let lastSearchTime = 0;

async function searchArtists(query) {
    const now = Date.now();
    
    // Debounce: only search if 500ms has passed since last attempt
    if (now - lastSearchTime < 500) {
        return;
    }
    lastSearchTime = now;
    
    if (!query || query.trim() === '') {
        toast.warning('Please enter a search term', 'Search');
        return;
    }
    
    try {
        const response = await fetch(`/api/search/artists?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.results.length === 0) {
            toast.info(`No artists found for "${query}"`, 'No Results');
        } else {
            toast.success(`Found ${data.results.length} artists!`, 'Search Complete');
        }
    } catch (error) {
        toast.error(error.message, 'Search Error');
    }
}


// ============================================================================
// MODAL/DIALOG PATTERNS
// ============================================================================

// Pattern 13: Toast from modal actions
document.getElementById('confirmDeleteBtn').addEventListener('click', async function() {
    const itemId = document.getElementById('deleteModal').dataset.itemId;
    
    try {
        const response = await fetch(`/api/item/${itemId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Hide modal
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            
            // Show confirmation
            toast.success('Item deleted successfully', 'Deleted');
            
            // Refresh page or list
            location.reload();
        } else {
            toast.error('Failed to delete item', 'Error');
        }
    } catch (error) {
        toast.error(error.message, 'Network Error');
    }
});


// ============================================================================
// KEYBOARD SHORTCUT PATTERNS
// ============================================================================

// Pattern 14: Keyboard shortcuts with toast feedback
document.addEventListener('keydown', async function(event) {
    // Ctrl+S to save
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        
        try {
            const response = await fetch('/api/save', { method: 'POST' });
            if (response.ok) {
                toast.success('Saved!', '', 2000);
            }
        } catch (error) {
            toast.error('Save failed', 'Error');
        }
    }
    
    // Ctrl+P to play
    if (event.ctrlKey && event.key === 'p') {
        event.preventDefault();
        toast.info('Playing current selection...', '', 2000);
        // Play logic...
    }
});


// ============================================================================
// VALIDATION PATTERNS
// ============================================================================

// Pattern 15: Complex validation with specific error messages
function validateArtistForm(formData) {
    // Check name
    if (!formData.name || formData.name.trim() === '') {
        toast.warning('Please enter an artist name', 'Validation Error');
        return false;
    }
    
    // Check name length
    if (formData.name.length > 255) {
        toast.warning('Artist name must be 255 characters or less', 'Name Too Long');
        return false;
    }
    
    // Check biography (optional field)
    if (formData.bio && formData.bio.length > 5000) {
        toast.warning('Biography must be 5000 characters or less', 'Bio Too Long');
        return false;
    }
    
    return true;
}
