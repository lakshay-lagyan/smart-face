// User Dashboard Manager

class UserDashboard {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Mark attendance button
        document.getElementById('mark-attendance-btn')?.addEventListener('click', () => {
            this.openAttendanceCamera();
        });
    }

    async loadDashboard() {
        try {
            utils.showLoading('Loading dashboard...');

            // Load dashboard data
            const dashboard = await api.getUserDashboard();

            // Update welcome message
            document.getElementById('user-welcome').textContent = `Welcome, ${dashboard.user.name}!`;
            document.getElementById('user-subtitle').textContent = dashboard.user.is_enrolled
                ? 'Mark your attendance easily'
                : 'Please complete enrollment to mark attendance';

            // Update stats
            document.getElementById('total-attendance').textContent = dashboard.user.stats?.total_attendance || 0;
            document.getElementById('this-month').textContent = dashboard.user.stats?.this_month || 0;

            // Load recent attendance
            this.loadRecentAttendance(dashboard.recent_attendance || []);

            // Update mark attendance button state
            const markBtn = document.getElementById('mark-attendance-btn');
            if (!dashboard.user.is_enrolled) {
                markBtn.disabled = true;
                markBtn.innerHTML = '<span>Enrollment Required</span>';
            }

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to load dashboard', 'error');
        }
    }

    loadRecentAttendance(records) {
        const container = document.getElementById('recent-attendance');
        
        if (records.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No attendance records yet</p>';
            return;
        }

        container.innerHTML = records.map(record => `
            <div class="attendance-item">
                <div class="attendance-item-header">
                    <div>
                        <div class="attendance-item-title">${record.check_type === 'in' ? 'Check In' : 'Check Out'}</div>
                        <div class="attendance-item-time">${utils.formatDateTime(record.timestamp)}</div>
                    </div>
                </div>
                <div class="attendance-item-details">
                    <span>📊 Confidence: ${(record.confidence * 100).toFixed(1)}%</span>
                    ${record.location ? `<span>📍 ${record.location}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    openAttendanceCamera() {
        if (window.attendanceCamera) {
            window.attendanceCamera.open();
        }
    }
}

// Initialize user dashboard
window.addEventListener('DOMContentLoaded', () => {
    window.userDashboard = new UserDashboard();
});
