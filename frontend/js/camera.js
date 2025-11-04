// Camera Handler - Manages camera access and photo capture

class CameraHandler {
    constructor(videoElement, canvasElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.stream = null;
        this.facingMode = CONFIG.CAMERA.FACING_MODE;
        this.constraints = null;
    }

    // Start camera
    async start() {
        try {
            // Stop any existing stream
            this.stop();

            // Request camera permissions
            this.constraints = {
                video: {
                    facingMode: this.facingMode,
                    width: { ideal: CONFIG.CAMERA.WIDTH },
                    height: { ideal: CONFIG.CAMERA.HEIGHT }
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(this.constraints);
            this.video.srcObject = this.stream;

            // Wait for video to load
            return new Promise((resolve, reject) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    resolve();
                };
                this.video.onerror = reject;
            });

        } catch (error) {
            console.error('Camera start error:', error);
            
            let errorMessage = 'Camera access denied';
            if (error.name === 'NotAllowedError') {
                errorMessage = 'Please allow camera access to continue';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'No camera found on this device';
            } else if (error.name === 'NotReadableError') {
                errorMessage = 'Camera is being used by another application';
            }
            
            throw new Error(errorMessage);
        }
    }

    // Stop camera
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
        }
    }

    // Switch between front and back camera
    async switchCamera() {
        this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
        await this.start();
    }

    // Capture photo from video
    capture() {
        if (!this.video || !this.canvas) {
            throw new Error('Video or canvas element not found');
        }

        // Set canvas dimensions to match video
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;

        // Draw video frame to canvas
        const context = this.canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

        // Get base64 image
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }

    // Check if camera is available
    static async isAvailable() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.some(device => device.kind === 'videoinput');
        } catch (error) {
            console.error('Error checking camera availability:', error);
            return false;
        }
    }

    // Get list of available cameras
    static async getCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'videoinput');
        } catch (error) {
            console.error('Error getting cameras:', error);
            return [];
        }
    }
}

// Enrollment Camera Manager
class EnrollmentCameraManager {
    constructor() {
        this.modal = document.getElementById('camera-modal');
        this.video = document.getElementById('camera-video');
        this.canvas = document.getElementById('camera-canvas');
        this.camera = new CameraHandler(this.video, this.canvas);
        this.isOpen = false;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Capture button
        document.getElementById('capture-btn').addEventListener('click', () => {
            this.capturePhoto();
        });

        // Switch camera button
        document.getElementById('switch-camera').addEventListener('click', () => {
            this.switchCamera();
        });

        // Close buttons
        document.getElementById('close-camera').addEventListener('click', () => {
            this.close();
        });

        document.getElementById('cancel-camera').addEventListener('click', () => {
            this.close();
        });

        // Close on outside click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    async open() {
        try {
            utils.showLoading('Starting camera...');
            await this.camera.start();
            this.modal.classList.add('active');
            this.isOpen = true;
            utils.hideLoading();
        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message, 'error');
        }
    }

    close() {
        this.camera.stop();
        this.modal.classList.remove('active');
        this.isOpen = false;
    }

    async switchCamera() {
        try {
            utils.showLoading('Switching camera...');
            await this.camera.switchCamera();
            utils.hideLoading();
        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message, 'error');
        }
    }

    async capturePhoto() {
        try {
            const base64Image = this.camera.capture();
            
            // Emit custom event with captured image
            const event = new CustomEvent('photo-captured', {
                detail: { image: base64Image }
            });
            document.dispatchEvent(event);
            
            this.close();
            
        } catch (error) {
            utils.showToast('Failed to capture photo', 'error');
        }
    }
}

// Attendance Camera Manager
class AttendanceCameraManager {
    constructor() {
        this.modal = document.getElementById('attendance-camera-modal');
        this.video = document.getElementById('attendance-video');
        this.canvas = document.getElementById('attendance-canvas');
        this.camera = new CameraHandler(this.video, this.canvas);
        this.isOpen = false;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Capture button
        document.getElementById('capture-attendance-btn').addEventListener('click', () => {
            this.captureAndMarkAttendance();
        });

        // Switch camera button
        document.getElementById('switch-attendance-camera').addEventListener('click', () => {
            this.switchCamera();
        });

        // Close buttons
        document.getElementById('close-attendance-camera').addEventListener('click', () => {
            this.close();
        });

        document.getElementById('cancel-attendance-camera').addEventListener('click', () => {
            this.close();
        });

        // Close on outside click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    async open() {
        try {
            utils.showLoading('Starting camera...');
            await this.camera.start();
            this.modal.classList.add('active');
            this.isOpen = true;
            utils.hideLoading();
        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message, 'error');
        }
    }

    close() {
        this.camera.stop();
        this.modal.classList.remove('active');
        this.isOpen = false;
    }

    async switchCamera() {
        try {
            utils.showLoading('Switching camera...');
            await this.camera.switchCamera();
            utils.hideLoading();
        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message, 'error');
        }
    }

    async captureAndMarkAttendance() {
        try {
            utils.showLoading('Marking attendance...');
            
            const base64Image = this.camera.capture();
            const checkType = document.querySelector('input[name="check-type"]:checked').value;
            
            // Call API to mark attendance
            const response = await api.markAttendance(base64Image, checkType);
            
            utils.hideLoading();
            this.close();
            
            utils.showToast(`Attendance marked successfully! Welcome, ${response.user.name}`, 'success');
            
            // Refresh dashboard
            if (window.userDashboard) {
                window.userDashboard.loadDashboard();
            }
            
        } catch (error) {
            utils.hideLoading();
            this.close();
            utils.showToast(error.message || 'Failed to mark attendance', 'error');
        }
    }
}

// Initialize camera managers
window.addEventListener('DOMContentLoaded', () => {
    window.enrollmentCamera = new EnrollmentCameraManager();
    window.attendanceCamera = new AttendanceCameraManager();
});
