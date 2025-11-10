/**
 * Kiosk Device Selector Component
 * Displays available Chromecast devices and allows switching
 */

(function() {
    let deviceData = null;
    
    window.initDeviceSelector = function() {
        loadDevices();
        // Refresh device list every 10 seconds
        setInterval(loadDevices, 10000);
    };
    
    async function loadDevices() {
        try {
            const response = await fetch('/api/chromecast/status');
            const data = await response.json();
            deviceData = data;
            renderDevices();
        } catch (error) {
            console.error('Error loading devices:', error);
            showStatus('Failed to load devices: ' + error.message, 'danger');
        }
    }
    
    function renderDevices() {
        if (!deviceData || !deviceData.available_devices) {
            return;
        }
        
        const grid = document.getElementById('device-grid');
        const devices = deviceData.available_devices;
        const activeDevice = deviceData.active_device;
        
        if (devices.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1;" class="text-center text-muted py-5">
                    <i class="mdi mdi-cast-off" style="font-size: 48px;"></i>
                    <p class="mt-3">No Chromecast devices found</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = devices.map(device => {
            const isActive = device.name === activeDevice;
            return `
                <div class="card h-100 device-card ${isActive ? 'active' : ''}" 
                     onclick="window.selectChromecastDevice('${escapeHtml(device.name)}')" 
                     style="cursor: pointer;">
                    <div class="card-body d-flex flex-column align-items-center justify-content-center text-center p-4">
                        <i class="mdi mdi-cast device-icon" style="font-size: 48px; color: ${isActive ? '#28a745' : '#0d6efd'};"></i>
                        <h5 class="mt-3 mb-0">${escapeHtml(device.name)}</h5>
                        ${isActive ? '<small class="text-success mt-1"><i class="mdi mdi-check-circle"></i> Active</small>' : '<small class="text-muted mt-1">Tap to select</small>'}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    window.selectChromecastDevice = async function(deviceName) {
        if (deviceData && deviceName === deviceData.active_device) {
            showStatus('Device "' + deviceName + '" is already active', 'info');
            return;
        }
        
        showStatus('Switching to ' + deviceName + '...', 'info');
        
        try {
            const response = await fetch('/api/chromecast/switch?device_name=' + encodeURIComponent(deviceName), {
                method: 'POST',
                headers: {
                    'accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                showStatus('Switched to ' + deviceName, 'success');
                // Reload devices to update active status
                setTimeout(loadDevices, 500);
            } else {
                const error = await response.json();
                showStatus('Failed to switch device: ' + (error.detail || 'Unknown error'), 'danger');
            }
        } catch (error) {
            console.error('Error selecting device:', error);
            showStatus('Error: ' + error.message, 'danger');
        }
    };
    
    function showStatus(message, type) {
        const statusDiv = document.getElementById('device-status');
        statusDiv.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Auto-dismiss success messages after 3 seconds
        if (type === 'success') {
            setTimeout(() => {
                const alert = statusDiv.querySelector('.alert');
                if (alert) {
                    alert.classList.remove('show');
                    setTimeout(() => statusDiv.innerHTML = '', 150);
                }
            }, 3000);
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Auto-initialize when component loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.initDeviceSelector);
    } else {
        window.initDeviceSelector();
    }
})();
