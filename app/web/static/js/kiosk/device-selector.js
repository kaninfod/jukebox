/**
 * Kiosk Device Selector Component
 * Displays available output devices (Bluetooth/MPV + Chromecast) and allows switching
 */

(function() {
    let deviceData = null;
    
    window.initDeviceSelector = function() {
        loadDevices();
        // Refresh device list every 10 seconds
        // setInterval(loadDevices, 10000);
    };
    
    async function loadDevices() {
        try {
            // Fetch server-rendered HTML fragment for devices
            const response = await fetch('/kiosk/html/devices');
            if (!response.ok) throw new Error('Failed to load devices');
            const html = await response.text();
            const grid = document.getElementById('device-grid');
            grid.innerHTML = html;
        } catch (error) {
            console.error('Error loading devices:', error);
            showKioskToast('Failed to load devices: ' + error.message, { theme: 'error' });
        }
    }
    
    window.selectOutputDevice = async function(backend, deviceName, label) {
        const targetLabel = label || deviceName || backend;
        showKioskToast('Switching to ' + targetLabel + '...', { theme: 'info' });
        try {
            const payload = { backend: backend };
            if (deviceName) {
                payload.device_name = deviceName;
            }

            const response = await fetch('/api/output/switch', {
                method: 'POST',
                headers: {
                    'accept': 'application/json',
                    'content-type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.status === 'ok') {
                    showKioskToast('Switched to ' + targetLabel, { theme: 'success' });
                } else {
                    const errMsg = result.message || result.error || 'Unknown error';
                    showKioskToast('Failed to switch output: ' + errMsg, { theme: 'error' });
                }
                // Refresh server-rendered device list
                setTimeout(loadDevices, 500);
            } else {
                // Try to parse error body
                let errMsg = 'Unknown error';
                try {
                    const error = await response.json();
                    errMsg = error.detail || error.message || errMsg;
                } catch (e) {}
                showKioskToast('Failed to switch output: ' + errMsg, { theme: 'error' });
            }
        } catch (error) {
            console.error('Error selecting output:', error);
            showKioskToast('Error: ' + error.message, { theme: 'error' });
        }
    };

    // Backward-compatible wrapper used by older templates/callers
    window.selectChromecastDevice = async function(deviceName) {
        return window.selectOutputDevice('chromecast', deviceName, deviceName);
    };
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Auto-initialize when component loads (only if required DOM elements exist)
    function safeInit() {
        if (document.getElementById('device-grid')) {
            window.initDeviceSelector();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
})();
