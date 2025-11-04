// Enrollment Manager

class EnrollmentManager {
    constructor() {
        this.capturedImages = [];
        this.enrollmentForm = document.getElementById('enrollment-form');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Back to login button
        document.getElementById('back-to-login')?.addEventListener('click', () => {
            utils.navigateTo('login-page');
            this.reset();
        });

        // Capture photo button
        document.getElementById('capture-photo-btn')?.addEventListener('click', () => {
            this.openCamera();
        });

        // Listen for photo captured event
        document.addEventListener('photo-captured', (e) => {
            this.addCapturedImage(e.detail.image);
        });

        // Enrollment form submission
        if (this.enrollmentForm) {
            this.enrollmentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitEnrollment();
            });
        }

        // Email validation
        document.getElementById('enroll-email')?.addEventListener('blur', (e) => {
            this.validateEmail(e.target.value);
        });
    }

    openCamera() {
        if (this.capturedImages.length >= CONFIG.CAMERA.MAX_IMAGES) {
            utils.showToast(`Maximum ${CONFIG.CAMERA.MAX_IMAGES} images allowed`, 'warning');
            return;
        }

        if (window.enrollmentCamera) {
            window.enrollmentCamera.open();
        }
    }

    addCapturedImage(base64Image) {
        this.capturedImages.push(base64Image);
        this.updateImagePreview();
        this.updateSubmitButton();
        
        if (this.capturedImages.length >= CONFIG.CAMERA.MIN_IMAGES) {
            utils.showToast(`${this.capturedImages.length} images captured. You can add more or submit.`, 'success');
        } else {
            utils.showToast(`${CONFIG.CAMERA.MIN_IMAGES - this.capturedImages.length} more image(s) needed`, 'info');
        }
    }

    removeImage(index) {
        this.capturedImages.splice(index, 1);
        this.updateImagePreview();
        this.updateSubmitButton();
    }

    updateImagePreview() {
        const container = document.getElementById('captured-images');
        const countElement = document.getElementById('image-count');

        countElement.textContent = this.capturedImages.length;

        container.innerHTML = this.capturedImages.map((img, index) => `
            <div class="captured-image">
                <img src="${img}" alt="Captured photo ${index + 1}">
                <button type="button" class="remove-image" onclick="enrollment.removeImage(${index})">×</button>
            </div>
        `).join('');
    }

    updateSubmitButton() {
        const submitBtn = document.getElementById('submit-enrollment');
        const hasEnoughImages = this.capturedImages.length >= CONFIG.CAMERA.MIN_IMAGES;
        
        submitBtn.disabled = !hasEnoughImages;
        
        if (hasEnoughImages) {
            submitBtn.textContent = 'Submit Enrollment Request';
        } else {
            submitBtn.textContent = `Need ${CONFIG.CAMERA.MIN_IMAGES - this.capturedImages.length} more image(s)`;
        }
    }

    async validateEmail(email) {
        if (!email || !utils.isValidEmail(email)) {
            return;
        }

        try {
            const response = await api.checkEmail(email);
            
            if (!response.available) {
                utils.showToast(response.reason, 'warning');
                document.getElementById('enroll-email').value = '';
            }

        } catch (error) {
            // Silently fail - not critical
        }
    }

    async submitEnrollment() {
        if (this.capturedImages.length < CONFIG.CAMERA.MIN_IMAGES) {
            utils.showToast(`Please capture at least ${CONFIG.CAMERA.MIN_IMAGES} images`, 'error');
            return;
        }

        const formData = {
            name: document.getElementById('enroll-name').value.trim(),
            email: document.getElementById('enroll-email').value.trim().toLowerCase(),
            password: document.getElementById('enroll-password').value,
            employee_id: document.getElementById('enroll-employee-id').value.trim(),
            department: document.getElementById('enroll-department').value.trim(),
            phone: document.getElementById('enroll-phone').value.trim(),
            images: this.capturedImages,
            device_info: utils.getDeviceInfo()
        };

        // Validate
        if (!formData.name || !formData.email || !formData.password) {
            utils.showToast('Please fill in all required fields', 'error');
            return;
        }

        if (!utils.isValidEmail(formData.email)) {
            utils.showToast('Please enter a valid email', 'error');
            return;
        }

        if (formData.password.length < 6) {
            utils.showToast('Password must be at least 6 characters', 'error');
            return;
        }

        try {
            utils.showLoading('Submitting enrollment request...');

            const response = await api.submitEnrollment(formData);

            utils.hideLoading();

            alert(`Enrollment Request Submitted Successfully!\n\nRequest ID: ${response.request_id}\n\nYou will be notified once your request is reviewed by an administrator.\n\nYou can check the status using your email.`);

            // Reset and go to login
            this.reset();
            utils.navigateTo('login-page');

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to submit enrollment', 'error');
        }
    }

    reset() {
        this.capturedImages = [];
        if (this.enrollmentForm) {
            this.enrollmentForm.reset();
        }
        this.updateImagePreview();
        this.updateSubmitButton();
    }
}

// Initialize enrollment manager
window.addEventListener('DOMContentLoaded', () => {
    window.enrollment = new EnrollmentManager();
});
