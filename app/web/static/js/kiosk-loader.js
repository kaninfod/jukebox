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
     * Load a component into the content area
     */
    async loadContent(componentName) {
        try {
            const response = await fetch(`/api/kiosk/component/${componentName}`);
            if (!response.ok) {
                throw new Error(`Failed to load component: ${response.status}`);
            }
            
            const html = await response.text();
            
            // Set the HTML content (scripts are already loaded in base template)
            this.contentArea.innerHTML = html;
            
            this.currentView = componentName;
            
            // Initialize component-specific functionality
            this.initializeComponent(componentName);
        } catch (error) {
            console.error('Error loading component:', error);
            this.showError('Failed to load content. Please try again.');
        }
    }
    
    /**
     * Initialize component-specific JavaScript
     */
    initializeComponent(name) {
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
            default:
                console.warn(`No initializer for component: ${name}`);
        }
    }
    
    /**
     * Initialize player status component
     */
    initPlayerStatus() {
        // Check if the component defined initPlayerStatus in global scope
        if (typeof window.initPlayerStatus === 'function') {
            window.initPlayerStatus();
        }
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
        // TODO: Add device selection functionality
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
     * Initialize event listeners
     */
    initializeListeners() {
        // Listen for custom events from components
        document.addEventListener('kiosk:navigate', (event) => {
            this.loadContent(event.detail.component);
        });
    }
    
    /**
     * Show error message
     */
    showError(message) {
        if (this.contentArea) {
            this.contentArea.innerHTML = `
                <div class="d-flex flex-column align-items-center justify-content-center h-100 text-center p-4">
                    <i class="mdi mdi-alert-circle" style="font-size: 64px; color: #e74c3c;"></i>
                    <h3 class="mt-3">Error</h3>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary mt-3" onclick="kioskLoader.loadContent('player')">
                        Return to Player
                    </button>
                </div>
            `;
        }
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
