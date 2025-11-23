/**
 * Kiosk Device Selector Component
 * Displays available Chromecast devices and allows switching
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
    
    window.selectChromecastDevice = async function(deviceName) {
        showKioskToast('Switching to ' + deviceName + '...', { theme: 'info' });
        try {
            const response = await fetch('/api/chromecast/switch?device_name=' + encodeURIComponent(deviceName), {
                method: 'POST',
                headers: {
                    'accept': 'application/json'
                }
            });
            if (response.ok) {
                const result = await response.json();
                showKioskToast('Switched to ' + deviceName, { theme: 'success' });
                // Refresh server-rendered device list
                setTimeout(loadDevices, 500);
            } else {
                // Try to parse error body
                let errMsg = 'Unknown error';
                try {
                    const error = await response.json();
                    errMsg = error.detail || errMsg;
                } catch (e) {}
                showKioskToast('Failed to switch device: ' + errMsg, { theme: 'error' });
            }
        } catch (error) {
            console.error('Error selecting device:', error);
            showKioskToast('Error: ' + error.message, { theme: 'error' });
        }
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
