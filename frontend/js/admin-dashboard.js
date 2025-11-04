
class AdminDashboard {
    constructor() {
        this.currentTab = 'dashboard';
        this.currentEnrollmentStatus = 'pending';
        this.currentUserStatus = 'active';
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('#admin-dashboard .tab-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Enrollment filter
        document.getElementById('enrollment-filter')?.addEventListener('change', (e) => {
            this.currentEnrollmentStatus = e.target.value;
            this.loadEnrollmentRequests();
        });

        // User search
        const userSearch = document.getElementById('user-search');
        if (userSearch) {
            userSearch.addEventListener('input', utils.debounce((e) => {
                this.loadUsers(e.target.value);
            }, 500));
        }

        // Attendance date filter
        document.getElementById('attendance-date')?.addEventListener('change', (e) => {
            this.loadAttendanceRecords(e.target.value);
        });
    }

    switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll('#admin-dashboard .tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update active tab content
        document.querySelectorAll('#admin-dashboard .tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.content === tabName);
        });

        this.currentTab = tabName;

        // Load tab data
        switch (tabName) {
            case 'dashboard':
                this.loadStats();
                break;
            case 'enrollments':
                this.loadEnrollmentRequests();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'attendance':
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('attendance-date').value = today;
                this.loadAttendanceRecords(today);
                break;
        }
    }

    async loadDashboard() {
        this.loadStats();
    }

    async loadStats() {
        try {
            const stats = await api.getAdminStats();

            document.getElementById('admin-total-users').textContent = stats.total_users || 0;
            document.getElementById('admin-enrolled-users').textContent = stats.enrolled_users || 0;
            document.getElementById('admin-pending').textContent = stats.pending_enrollments || 0;
            document.getElementById('admin-today-attendance').textContent = stats.today_attendance || 0;

        } catch (error) {
            utils.showToast('Failed to load statistics', 'error');
        }
    }

    async loadEnrollmentRequests() {
        try {
            utils.showLoading('Loading enrollment requests...');
            
            const response = await api.getEnrollmentRequests(this.currentEnrollmentStatus);
            const container = document.getElementById('enrollments-list');

            if (response.requests.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">No enrollment requests found</p>';
                utils.hideLoading();
                return;
            }

            container.innerHTML = response.requests.map(req => `
                <div class="data-item">
                    <div class="attendance-item-header">
                        <div>
                            <div class="attendance-item-title">${req.name}</div>
                            <div class="attendance-item-time">${req.email}</div>
                        </div>
                        <div>${utils.createBadge(req.status)}</div>
                    </div>
                    <div class="attendance-item-details">
                        <span>📅 ${utils.formatDate(req.submitted_at)}</span>
                        <span>🖼️ ${req.image_count} images</span>
                        ${req.employee_id ? `<span>👤 ${req.employee_id}</span>` : ''}
                    </div>
                    ${req.status === 'pending' ? `
                        <div class="mt-2" style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-success" style="flex: 1;" onclick="adminDashboard.approveEnrollment(${req.id})">
                                Approve
                            </button>
                            <button class="btn btn-danger" style="flex: 1;" onclick="adminDashboard.rejectEnrollment(${req.id})">
                                Reject
                            </button>
                        </div>
                    ` : ''}
                    ${req.rejection_reason ? `
                        <div class="mt-2 text-danger">
                            <strong>Reason:</strong> ${req.rejection_reason}
                        </div>
                    ` : ''}
                </div>
            `).join('');

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load enrollment requests', 'error');
        }
    }

    async approveEnrollment(requestId) {
        if (!confirm('Are you sure you want to approve this enrollment request?')) {
            return;
        }

        try {
            utils.showLoading('Approving enrollment...');
            
            await api.approveEnrollment(requestId);
            
            utils.hideLoading();
            utils.showToast('Enrollment approved successfully!', 'success');
            
            this.loadEnrollmentRequests();
            this.loadStats();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to approve enrollment', 'error');
        }
    }

    async rejectEnrollment(requestId) {
        const reason = prompt('Enter rejection reason:');
        
        if (!reason) {
            return;
        }

        try {
            utils.showLoading('Rejecting enrollment...');
            
            await api.rejectEnrollment(requestId, reason);
            
            utils.hideLoading();
            utils.showToast('Enrollment rejected', 'info');
            
            this.loadEnrollmentRequests();
            this.loadStats();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to reject enrollment', 'error');
        }
    }

    async loadUsers(search = '') {
        try {
            utils.showLoading('Loading users...');
            
            const response = await api.getUsers(this.currentUserStatus, search);
            const container = document.getElementById('users-list');

            if (response.users.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">No users found</p>';
                utils.hideLoading();
                return;
            }

            container.innerHTML = response.users.map(user => `
                <div class="data-item">
                    <div class="attendance-item-header">
                        <div>
                            <div class="attendance-item-title">${user.name}</div>
                            <div class="attendance-item-time">${user.email}</div>
                        </div>
                        <div>${utils.createBadge(user.status)}</div>
                    </div>
                    <div class="attendance-item-details">
                        ${user.employee_id ? `<span>👤 ${user.employee_id}</span>` : ''}
                        ${user.department ? `<span>🏢 ${user.department}</span>` : ''}
                        <span>${user.is_enrolled ? '✅ Enrolled' : '❌ Not Enrolled'}</span>
                    </div>
                </div>
            `).join('');

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load users', 'error');
        }
    }

    async loadAttendanceRecords(date = null) {
        try {
            utils.showLoading('Loading attendance...');
            
            const response = await api.getAllAttendance(date);
            const container = document.getElementById('attendance-list');

            if (response.records.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">No attendance records found</p>';
                utils.hideLoading();
                return;
            }

            container.innerHTML = response.records.map(record => `
                <div class="data-item">
                    <div class="attendance-item-header">
                        <div>
                            <div class="attendance-item-title">${record.name}</div>
                            <div class="attendance-item-time">${utils.formatDateTime(record.timestamp)}</div>
                        </div>
                        <div class="badge badge-${record.check_type === 'in' ? 'success' : 'info'}">
                            ${record.check_type === 'in' ? 'CHECK IN' : 'CHECK OUT'}
                        </div>
                    </div>
                    <div class="attendance-item-details">
                        <span>📊 ${(record.confidence * 100).toFixed(1)}% confidence</span>
                        ${record.location ? `<span>${record.location}</span>` : ''}
                    </div>
                </div>
            `).join('');

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load attendance records', 'error');
        }
    }
}

// Initialize admin dashboard
window.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
});
