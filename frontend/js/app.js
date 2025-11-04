// Main Application

class App {
    constructor() {
        this.init();
    }

    init() {
        console.log('🚀 Smart Attendance System - v2.0');
        console.log('📱 Mobile-optimized face recognition system');
        
        // Check for required browser features
        this.checkBrowserSupport();
        
        // Initialize service worker for PWA (if needed in future)
        // this.registerServiceWorker();
        
        // Setup global error handler
        this.setupErrorHandler();
        
        // Check for camera on mobile
        if (utils.isMobile()) {
            this.checkMobileCamera();
        }
    }

    checkBrowserSupport() {
        const features = {
            'WebRTC (Camera)': !!navigator.mediaDevices?.getUserMedia,
            'Local Storage': !!window.localStorage,
            'Fetch API': !!window.fetch,
            'ES6 Support': true // If this code runs, ES6 is supported
        };

        console.log('Browser Support:');
        Object.entries(features).forEach(([feature, supported]) => {
            console.log(`${supported ? '✅' : '❌'} ${feature}`);
        });

        // Show warning if critical features are missing
        if (!features['WebRTC (Camera)']) {
            utils.showToast('Your browser does not support camera access', 'warning');
        }

        if (!features['Local Storage']) {
            utils.showToast('Your browser does not support local storage', 'warning');
        }
    }

    async checkMobileCamera() {
        const hasCamera = await utils.hasCamera();
        
        if (!hasCamera) {
            console.warn('⚠️ No camera detected on this device');
        } else {
            console.log('📷 Camera detected');
        }
    }

    setupErrorHandler() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            
            // Don't show toast for every error (can be annoying)
            // Only log to console for debugging
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
        });
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(reg => console.log('Service Worker registered', reg))
                .catch(err => console.log('Service Worker registration failed', err));
        }
    }
}

// Initialize app when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    
    // Add touch feedback for better mobile UX
    if (utils.isMobile()) {
        document.body.classList.add('mobile-device');
    }
    
    console.log('✅ Application initialized');
});

// Prevent accidental page refresh on mobile
window.addEventListener('beforeunload', (e) => {
    // Only show warning if user is logged in
    if (auth && auth.currentUser) {
        // Modern browsers ignore custom messages
        e.preventDefault();
        e.returnValue = '';
    }
});

// Handle online/offline status
window.addEventListener('online', () => {
    utils.showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    utils.showToast('No internet connection', 'warning');
});
