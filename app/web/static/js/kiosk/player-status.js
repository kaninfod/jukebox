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
    const safeTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    const element = document.getElementById('kiosk-track-info');
    console.log(`[${safeTimestamp}] INIT: safeInit() called. kiosk-track-info element exists: ${!!element}`);
    
    if (element) {
        console.log(`[${safeTimestamp}] INIT: DOM ready, calling window.initPlayerStatus()`);
        window.initPlayerStatus();
    } else {
        console.error(`[${safeTimestamp}] INIT: kiosk-track-info element NOT FOUND - component may not be loaded`);
    }
}

function updateKioskTrackInfo(data) {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    console.log(`[${timestamp}] UPDATE: Received data:`, data);
    console.log(`[${timestamp}] UPDATE: Data structure - has current_track: ${!!data.current_track}, has playlist: ${!!data.playlist}`);
    
    const kioskInfoDiv = document.getElementById('kiosk-track-info');
    const kioskThumbDiv = document.getElementById('kiosk-track-thumb');
    const deviceDiv = document.getElementById('current-device');
    const volumeFill = document.getElementById('kiosk-volume-fill');
    const volumeText = document.getElementById('kiosk-volume-text');
    
    console.log(`[${timestamp}] UPDATE: DOM elements - info: ${!!kioskInfoDiv}, thumb: ${!!kioskThumbDiv}, device: ${!!deviceDiv}, volumeFill: ${!!volumeFill}, volumeText: ${!!volumeText}`);
    
    // Exit early if player status component is not currently loaded
    if (!kioskInfoDiv || !kioskThumbDiv) {
        console.warn(`[${timestamp}] UPDATE: Early return - DOM elements not found. Component may not be initialized.`);
        return;
    }
    
    // Update Chromecast device name
    if (data.chromecast_device && deviceDiv) {
        console.log(`[${timestamp}] UPDATE: Setting device to: ${data.chromecast_device}`);
        deviceDiv.textContent = data.chromecast_device;
    }
    
    // Update volume bar
    if (data.volume !== undefined && volumeFill && volumeText) {
        const volume = parseInt(data.volume) || 0;
        console.log(`[${timestamp}] UPDATE: Setting volume to: ${volume}%`);
        volumeFill.style.height = volume + '%';
        volumeText.textContent = volume + '%';
    }
    
    if (data.current_track) {
        console.log(`[${timestamp}] UPDATE: Current track found - title: "${data.current_track.title}"`);
        console.log(`[${timestamp}] UPDATE: Validating required fields - artist: ${!!data.current_track.artist}, album: ${!!data.current_track.album}, year: ${!!data.current_track.year}, playlist length: ${data.playlist ? data.playlist.length : 'N/A'}`);
        
        // Validate all required fields exist before rendering
        if (!data.current_track.artist || !data.current_track.album || !data.current_track.year || !data.playlist) {
            console.error(`[${timestamp}] UPDATE: MISSING REQUIRED FIELDS - Cannot render. artist: "${data.current_track.artist}", album: "${data.current_track.album}", year: "${data.current_track.year}", playlist: ${!!data.playlist}`);
        }
        
        kioskInfoDiv.innerHTML = `
            <div class="kiosk-status">
                <span><i class="mdi mdi-music-note"></i> Track ${data.current_track.track_number} of ${data.playlist.length}</span>
            </div>
            <div class="kiosk-artist">${data.current_track.artist}</div>
            <div class="kiosk-title">${data.current_track.title}</div>
            <div class="kiosk-album">${data.current_track.album} (${data.current_track.year})</div>
        `;
        console.log(`[${timestamp}] UPDATE: Track info rendered successfully`);
        
        let thumbUrl = data.current_track.thumb;
        if (thumbUrl) {
            console.log(`[${timestamp}] UPDATE: Loading album art from: ${thumbUrl}`);
            kioskThumbDiv.innerHTML = `<img src="${thumbUrl}" alt="Album Cover" />`;
        } else {
            console.log(`[${timestamp}] UPDATE: No thumb URL, showing placeholder`);
            kioskThumbDiv.innerHTML = '<div class="kiosk-no-cover"><i class="mdi mdi-music"></i></div>';
        }
    } else {
        console.warn(`[${timestamp}] UPDATE: No current_track in data. data.message: "${data.message}"`);
        kioskInfoDiv.innerHTML = '<div class="kiosk-no-track">' + (data.message || 'No track loaded') + '</div>';
        kioskThumbDiv.innerHTML = '<div class="kiosk-no-cover"><i class="mdi mdi-music"></i></div>';
    }
}

/**
 * Kiosk Player Status Component
 * Displays current track information, album art, and volume
 */

(function() {
    const initTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    console.log(`[${initTimestamp}] INIT: player-status.js module loading`);
    console.log(`[${initTimestamp}] INIT: document.readyState = "${document.readyState}"`);
    
    let wsReady = false;
    let apiReady = false;
    
    // Expose initPlayerStatus globally so kiosk loader can call it
    window.initPlayerStatus = async function() {
        const funcTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        console.log(`[${funcTimestamp}] INIT: initPlayerStatus() called`);
        
        // Fetch initial state from API
        try {
            const response = await fetch('/api/mediaplayer/status');
            const respTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`[${respTimestamp}] INIT: API response received (raw):`, data);
                
                // Unwrap API envelope if present (API returns {type, payload} but we need just the payload)
                const payloadData = (data.type && data.payload) ? data.payload : data;
                console.log(`[${respTimestamp}] INIT: API response unwrapped:`, payloadData);
                
                updateKioskTrackInfo(payloadData);
                apiReady = true;
                console.log(`[${respTimestamp}] INIT: API data rendered, apiReady = true`);
            } else {
                console.error(`[${respTimestamp}] INIT: API response not OK, status: ${response.status}`);
            }
        } catch (error) {
            const errTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
            console.error(`[${errTimestamp}] INIT: Error fetching initial player status:`, error);
        }
    };
    
    // WebSocket for live track info
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/mediaplayer/status`;
    console.log(`[${initTimestamp}] WS: Creating WebSocket connection to: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = function(event) {
        const wsTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        wsReady = true;
        console.log(`[${wsTimestamp}] WS: WebSocket connected, wsReady = true`);
    };
    
    ws.onerror = function(event) {
        const wsTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        console.error(`[${wsTimestamp}] WS: WebSocket error:`, event);
    };
    
    ws.onmessage = function(event) {
        const wsTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        console.log(`[${wsTimestamp}] WS: Message received. apiReady: ${apiReady}, wsReady: ${wsReady}`);
        
        const msg = JSON.parse(event.data);
        console.log(`[${wsTimestamp}] WS: Parsed message type: "${msg.type}"`);
        
        // Support both new envelope {type, payload} and legacy direct payload
        if (msg && msg.type) {
            if (msg.type === 'ping') {
                console.log(`[${wsTimestamp}] WS: Ping received`);
                return;
            }
            if (msg.type === 'error') {
                console.error(`[${wsTimestamp}] WS: Error message:`, msg.payload && msg.payload.message);
                return;
            }
            if (msg.type === 'notification') {
                // Handle notification event (optional)
                const payload = msg.payload || {};
                console.log(`[${wsTimestamp}] WS: Notification:`, payload);
                showKioskToast('Notification: ' + (payload.message || ''), { theme: 'info' });
                return;
            }
            if (msg.type === 'current_track') {
                // for type 'current_track', payload contains the actual data
                const payload = msg.payload || {};
                console.log(`[${wsTimestamp}] WS: current_track update received:`, payload);
                console.log(`[${wsTimestamp}] WS: Payload structure - has current_track: ${!!payload.current_track}, has playlist: ${!!payload.playlist}`);
                if (typeof window.updateKioskTrackInfo === 'function') {
                    console.log(`[${wsTimestamp}] WS: Calling updateKioskTrackInfo`);
                    window.updateKioskTrackInfo(payload);
                } else {
                    console.error(`[${wsTimestamp}] WS: updateKioskTrackInfo function not found!`);
                }
            }
        } else {
            console.warn(`[${wsTimestamp}] WS: Message structure unexpected:`, msg);
        }
    };
    
    if (document.readyState === 'loading') {
        console.log(`[${initTimestamp}] INIT: document.readyState is "loading", waiting for DOMContentLoaded`);
        document.addEventListener('DOMContentLoaded', function() {
            const domTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
            console.log(`[${domTimestamp}] INIT: DOMContentLoaded fired, calling safeInit()`);
            safeInit();
        });
    } else {
        const readyTimestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        console.log(`[${readyTimestamp}] INIT: document.readyState is "${document.readyState}", calling safeInit() immediately`);
        safeInit();
    }
})();
