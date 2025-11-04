// Super Admin Dashboard Manager

class SuperAdminDashboard {
    constructor() {
        this.currentTab = 'super-dashboard';
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('#super-admin-dashboard .tab-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Rebuild FAISS index button
        document.getElementById('rebuild-index-btn')?.addEventListener('click', () => {
            this.rebuildFAISSIndex();
        });

        // Create admin button
        document.getElementById('create-admin-btn')?.addEventListener('click', () => {
            this.showCreateAdminForm();
        });

        // Log filter
        document.getElementById('log-filter')?.addEventListener('change', (e) => {
            this.loadSystemLogs(e.target.value);
        });
    }

    switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll('#super-admin-dashboard .tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update active tab content
        document.querySelectorAll('#super-admin-dashboard .tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.content === tabName);
        });

        this.currentTab = tabName;

        // Load tab data
        switch (tabName) {
            case 'super-dashboard':
                this.loadDashboard();
                break;
            case 'admins':
                this.loadAdmins();
                break;
            case 'logs':
                this.loadSystemLogs();
                break;
        }
    }

    async loadDashboard() {
        try {
            utils.showLoading('Loading dashboard...');
            
            const dashboard = await api.getSuperAdminDashboard();
            const stats = dashboard.statistics;

            // Update statistics
            document.getElementById('super-total-admins').textContent = stats.total_admins || 0;
            document.getElementById('super-total-users').textContent = stats.total_users || 0;
            document.getElementById('super-enrolled').textContent = stats.enrolled_users || 0;
            document.getElementById('super-index-size').textContent = stats.faiss_index_size || 0;

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load dashboard', 'error');
        }
    }

    async loadAdmins() {
        try {
            utils.showLoading('Loading admins...');
            
            const response = await api.getAllAdmins();
            const container = document.getElementById('admins-list');

            if (response.admins.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">No admins found</p>';
                utils.hideLoading();
                return;
            }

            container.innerHTML = response.admins.map(admin => `
                <div class="data-item">
                    <div class="attendance-item-header">
                        <div>
                            <div class="attendance-item-title">${admin.name}</div>
                            <div class="attendance-item-time">${admin.email}</div>
                        </div>
                        <div>
                            ${utils.createBadge(admin.role.replace('_', ' '))}
                            ${admin.is_active ? utils.createBadge('active') : utils.createBadge('inactive')}
                        </div>
                    </div>
                    <div class="attendance-item-details">
                        ${admin.department ? `<span>🏢 ${admin.department}</span>` : ''}
                        ${admin.phone ? `<span>📞 ${admin.phone}</span>` : ''}
                        <span>📅 Created ${utils.formatDate(admin.created_at)}</span>
                    </div>
                    ${auth.currentUser.id !== admin.id ? `
                        <div class="mt-2" style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-secondary" style="flex: 1;" onclick="superAdminDashboard.toggleAdminStatus(${admin.id}, ${admin.is_active})">
                                ${admin.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('');

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load admins', 'error');
        }
    }

    showCreateAdminForm() {
        const name = prompt('Enter admin name:');
        if (!name) return;

        const email = prompt('Enter admin email:');
        if (!email || !utils.isValidEmail(email)) {
            utils.showToast('Invalid email', 'error');
            return;
        }

        const password = prompt('Enter password (min 6 characters):');
        if (!password || password.length < 6) {
            utils.showToast('Password must be at least 6 characters', 'error');
            return;
        }

        const role = confirm('Make Super Admin? (OK for Super Admin, Cancel for Regular Admin)')
            ? 'super_admin'
            : 'admin';

        this.createAdmin({ name, email, password, role });
    }

    async createAdmin(data) {
        try {
            utils.showLoading('Creating admin...');
            
            await api.createAdmin(data);
            
            utils.hideLoading();
            utils.showToast('Admin created successfully!', 'success');
            
            this.loadAdmins();
            this.loadDashboard();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to create admin', 'error');
        }
    }

    async toggleAdminStatus(adminId, currentStatus) {
        const action = currentStatus ? 'deactivate' : 'activate';
        
        if (!confirm(`Are you sure you want to ${action} this admin?`)) {
            return;
        }

        try {
            utils.showLoading(`${action === 'deactivate' ? 'Deactivating' : 'Activating'} admin...`);
            
            await api.updateAdmin(adminId, { is_active: !currentStatus });
            
            utils.hideLoading();
            utils.showToast(`Admin ${action}d successfully`, 'success');
            
            this.loadAdmins();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || `Failed to ${action} admin`, 'error');
        }
    }

    async rebuildFAISSIndex() {
        if (!confirm('This will rebuild the entire FAISS index. Continue?')) {
            return;
        }

        try {
            utils.showLoading('Rebuilding FAISS index... This may take a while.');
            
            const response = await api.rebuildFAISSIndex();
            
            utils.hideLoading();
            utils.showToast(`Index rebuilt successfully! Total persons: ${response.total_persons}`, 'success');
            
            this.loadDashboard();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Failed to rebuild index', 'error');
        }
    }

    async loadSystemLogs(action = null) {
        try {
            utils.showLoading('Loading logs...');
            
            const response = await api.getSystemLogs(action);
            const container = document.getElementById('logs-list');

            if (response.logs.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">No logs found</p>';
                utils.hideLoading();
                return;
            }

            container.innerHTML = response.logs.map(log => `
                <div class="data-item">
                    <div class="attendance-item-header">
                        <div>
                            <div class="attendance-item-title">${log.action.replace(/_/g, ' ').toUpperCase()}</div>
                            <div class="attendance-item-time">${utils.formatDateTime(log.timestamp)}</div>
                        </div>
                        <div>${utils.createBadge(log.user_type)}</div>
                    </div>
                    <div class="attendance-item-details">
                        ${log.user_email ? `<span>👤 ${log.user_email}</span>` : ''}
                        ${log.ip_address ? `<span>🌐 ${log.ip_address}</span>` : ''}
                    </div>
                    ${log.details ? `
                        <div class="mt-2" style="font-size: 0.875rem; color: var(--gray-600);">
                            ${JSON.stringify(log.details, null, 2).substring(0, 200)}
                        </div>
                    ` : ''}
                </div>
            `).join('');

            utils.hideLoading();

        } catch (error) {
            utils.hideLoading();
            utils.showToast('Failed to load logs', 'error');
        }
    }
}

// Initialize super admin dashboard
window.addEventListener('DOMContentLoaded', () => {
    window.superAdminDashboard = new SuperAdminDashboard();
});
