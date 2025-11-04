// API Configuration
const CONFIG = {
    // API Base URL - Change this to your backend URL in production
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000/api'
        : '/api', // Use relative path in production
    
    // Camera settings
    CAMERA: {
        WIDTH: 1280,
        HEIGHT: 720,
        FACING_MODE: 'user', // 'user' for front camera, 'environment' for back
        MIN_IMAGES: 3,
        MAX_IMAGES: 10
    },
    
    // Face recognition thresholds
    FACE: {
        CONFIDENCE_THRESHOLD: 0.6,
        QUALITY_THRESHOLD: 0.4
    },
    
    // Pagination
    PAGINATION: {
        PER_PAGE: 20
    },
    
    // Toast duration
    TOAST_DURATION: 4000,
    
    // Refresh intervals (in milliseconds)
    REFRESH: {
        DASHBOARD: 30000, // 30 seconds
        ATTENDANCE: 60000  // 1 minute
    }
};

// Export for use in other modules
window.CONFIG = CONFIG;
