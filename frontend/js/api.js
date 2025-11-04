// API Service - Handles all backend communication

class APIService {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.token = localStorage.getItem('access_token');
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('access_token', token);
        } else {
            localStorage.removeItem('access_token');
        }
    }

    // Get headers
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (includeAuth && this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders(options.auth !== false)
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ===== AUTH ENDPOINTS =====
    
    async loginUser(email, password) {
        return this.request('/auth/user/login', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ email, password })
        });
    }

    async loginAdmin(email, password) {
        return this.request('/auth/admin/login', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ email, password })
        });
    }

    async verifyToken() {
        return this.request('/auth/verify', {
            method: 'GET'
        });
    }

    async changePassword(currentPassword, newPassword) {
        return this.request('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
    }

    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } finally {
            this.setToken(null);
        }
    }

    // ===== ENROLLMENT ENDPOINTS =====
    
    async submitEnrollment(data) {
        return this.request('/enrollment/request', {
            method: 'POST',
            auth: false,
            body: JSON.stringify(data)
        });
    }

    async checkEmail(email) {
        return this.request('/enrollment/check-email', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ email })
        });
    }

    async getEnrollmentStatus(requestId) {
        return this.request(`/enrollment/status/${requestId}`, {
            method: 'GET',
            auth: false
        });
    }

    // ===== ATTENDANCE ENDPOINTS =====
    
    async markAttendance(image, checkType = 'in', location = null) {
        return this.request('/attendance/mark', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({
                image,
                check_type: checkType,
                location,
                device_info: utils.getDeviceInfo()
            })
        });
    }

    async getMyAttendance(days = 30, page = 1) {
        return this.request(`/attendance/my-records?days=${days}&page=${page}`, {
            method: 'GET'
        });
    }

    async getMyStats() {
        return this.request('/attendance/stats', {
            method: 'GET'
        });
    }

    // ===== USER ENDPOINTS =====
    
    async getUserProfile() {
        return this.request('/user/profile', {
            method: 'GET'
        });
    }

    async updateUserProfile(data) {
        return this.request('/user/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async getUserDashboard() {
        return this.request('/user/dashboard', {
            method: 'GET'
        });
    }

    // ===== ADMIN ENDPOINTS =====
    
    async getEnrollmentRequests(status = 'pending', page = 1) {
        return this.request(`/admin/enrollment-requests?status=${status}&page=${page}`, {
            method: 'GET'
        });
    }

    async getEnrollmentRequest(requestId) {
        return this.request(`/admin/enrollment-requests/${requestId}`, {
            method: 'GET'
        });
    }

    async approveEnrollment(requestId) {
        return this.request(`/admin/enrollment-requests/${requestId}/approve`, {
            method: 'POST'
        });
    }

    async rejectEnrollment(requestId, reason) {
        return this.request(`/admin/enrollment-requests/${requestId}/reject`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async getUsers(status = 'active', search = '', page = 1) {
        let url = `/admin/users?status=${status}&page=${page}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        return this.request(url, { method: 'GET' });
    }

    async getAllAttendance(date = null, userId = null, page = 1) {
        let url = `/admin/attendance/all?page=${page}`;
        if (date) url += `&date=${date}`;
        if (userId) url += `&user_id=${userId}`;
        return this.request(url, { method: 'GET' });
    }

    async getAdminStats() {
        return this.request('/admin/stats', {
            method: 'GET'
        });
    }

    // ===== SUPER ADMIN ENDPOINTS =====
    
    async getSuperAdminDashboard() {
        return this.request('/super-admin/dashboard', {
            method: 'GET'
        });
    }

    async getAllAdmins(page = 1) {
        return this.request(`/super-admin/admins?page=${page}`, {
            method: 'GET'
        });
    }

    async createAdmin(data) {
        return this.request('/super-admin/admins', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateAdmin(adminId, data) {
        return this.request(`/super-admin/admins/${adminId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteAdmin(adminId) {
        return this.request(`/super-admin/admins/${adminId}`, {
            method: 'DELETE'
        });
    }

    async updateUserStatus(userId, status) {
        return this.request(`/super-admin/users/${userId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }

    async getSystemLogs(action = null, userType = null, page = 1) {
        let url = `/super-admin/system/logs?page=${page}`;
        if (action) url += `&action=${action}`;
        if (userType) url += `&user_type=${userType}`;
        return this.request(url, { method: 'GET' });
    }

    async rebuildFAISSIndex() {
        return this.request('/super-admin/system/rebuild-index', {
            method: 'POST'
        });
    }

    // ===== FACE DETECTION ENDPOINTS =====
    
    async detectFace(image) {
        return this.request('/face/detect', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ image })
        });
    }

    async checkQuality(image) {
        return this.request('/face/quality-check', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ image })
        });
    }
}

// Create global API instance
window.api = new APIService();
