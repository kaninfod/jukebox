/**
 * Kiosk Content Loader
 * 
 * Handles dynamic content loading for kiosk mode
 * Swaps content in center area without full page reload
 */

class KioskContentLoader {
    constructor() {
        this.contentArea = document.getElementById('kiosk-content-area');
        this.currentView = 'player';
        this.initializeListeners();
    }
    
    /**
     * Load a component into the content area with optional data
     */
    async loadContent(componentName, data = {}) {
        try {
            const response = await fetch(`/kiosk/html/component?component_name=${encodeURIComponent(componentName)}`);
            if (!response.ok) {
                throw new Error(`Failed to load component: ${response.status}`);
            }
            
            const html = await response.text();
            
            // Set the HTML content (scripts are already loaded in base template)
            this.contentArea.innerHTML = html;
            
            this.currentView = componentName;
            
            // Initialize component-specific functionality with optional data
            this.initializeComponent(componentName, data);
        } catch (error) {
            console.error('Error loading component:', error);
            this.showError('Failed to load content. Please try again.');
        }
    }
    
    /**
     * Initialize component-specific JavaScript
     */
    initializeComponent(name, data = {}) {
        switch(name) {
            case 'player':
                this.initPlayerStatus();
                break;
            case 'playlist':
                this.initPlaylistView();
                break;
            case 'library':
                this.initMediaLibrary();
                break;
            case 'devices':
                this.initDeviceSelector();
                break;
            case 'system':
                this.initSystemMenu();
                break;
            case 'nfc':
                this.initNfcEncoding(data.albumId, data.albumName);
                break;
            default:
                console.warn(`No initializer for component: ${name}`);
        }
    }
    
    /**
     * Initialize player status component
     */
    initPlayerStatus() {
        // Do a full page reload to refresh the entire browser
        window.location.reload(true);
    }
    
    /**
     * Initialize playlist view component
     */
    initPlaylistView() {
        // Check if the component defined initPlaylistView in global scope
        if (typeof window.initPlaylistView === 'function') {
            window.initPlaylistView();
        }
    }
    
    /**
     * Initialize media library component
     */
    initMediaLibrary() {
        // Check if the component defined initMediaLibrary in global scope
        if (typeof window.initMediaLibrary === 'function') {
            window.initMediaLibrary();
        }
    }
    
    /**
     * Initialize device selector component
     */
    initDeviceSelector() {
        if (typeof window.initDeviceSelector === 'function') {
            window.initDeviceSelector();
        }
    }
    
    /**
     * Initialize system menu component
     */
    initSystemMenu() {
        // Check if the component defined initSystemMenu in global scope
        if (typeof window.initSystemMenu === 'function') {
            window.initSystemMenu();
        }
    }
    
    /**
     * Initialize NFC encoding component
     */
    initNfcEncoding(albumId, albumName) {
        // Check if the component defined initNfcEncoding in global scope
        if (typeof window.initNfcEncoding === 'function') {
            window.initNfcEncoding(albumId, albumName);
        }
    }
    
    /**
     * Initialize event listeners
     */
    initializeListeners() {
        // Listen for custom events from components
        document.addEventListener('kiosk:navigate', (event) => {
            this.loadContent(event.detail.component);
        });
    }
    
    /**
     * Show error message (now uses unified toast)
     */
    showError(message) {
        showKioskToast(message, { theme: 'error', timeout: 5000 });
    }
}

// Initialize kiosk loader when DOM is ready
let kioskLoader;
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.classList.contains('kiosk-layout')) {
        kioskLoader = new KioskContentLoader();
    }
});

// Global navigation function for kiosk navigation buttons
function navigateTo(section) {
    if (typeof kioskLoader !== 'undefined') {
        kioskLoader.loadContent(section);
    } else {
        console.error('kioskLoader not initialized yet');
    }
}

// Global function for device selector
function selectDevice() {
    if (typeof kioskLoader !== 'undefined') {
        kioskLoader.loadContent('devices');
    } else {
        console.error('kioskLoader not initialized yet');
    }
}
