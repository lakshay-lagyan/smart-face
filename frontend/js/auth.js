// Authentication Manager

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.currentUserType = null;
        this.loginForm = document.getElementById('login-form');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login tabs
        document.querySelectorAll('.login-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active tab
                document.querySelectorAll('.login-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                // Store selected tab
                this.currentUserType = e.target.dataset.tab;
            });
        });

        // Login form submission
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Enroll link
        const enrollLink = document.getElementById('enroll-link');
        if (enrollLink) {
            enrollLink.addEventListener('click', (e) => {
                e.preventDefault();
                utils.navigateTo('enrollment-page');
            });
        }

        // Menu buttons
        document.getElementById('user-menu-btn')?.addEventListener('click', () => {
            this.showUserMenu();
        });

        document.getElementById('admin-menu-btn')?.addEventListener('click', () => {
            this.showAdminMenu();
        });

        document.getElementById('super-admin-menu-btn')?.addEventListener('click', () => {
            this.showAdminMenu();
        });
    }

    async handleLogin() {
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email || !password) {
            utils.showToast('Please enter email and password', 'error');
            return;
        }

        try {
            utils.showLoading('Logging in...');

            let response;
            if (this.currentUserType === 'admin') {
                response = await api.loginAdmin(email, password);
            } else {
                response = await api.loginUser(email, password);
            }

            // Store token
            api.setToken(response.access_token);
            localStorage.setItem('refresh_token', response.refresh_token);

            // Store user info
            this.currentUser = response.user || response.admin;
            this.currentUserType = response.user ? 'user' : 'admin';

            utils.hideLoading();
            utils.showToast('Login successful!', 'success');

            // Navigate to appropriate dashboard
            this.navigateToDashboard();

        } catch (error) {
            utils.hideLoading();
            utils.showToast(error.message || 'Login failed', 'error');
        }
    }

    navigateToDashboard() {
        if (!this.currentUser) return;

        if (this.currentUserType === 'admin') {
            if (this.currentUser.role === 'super_admin') {
                utils.navigateTo('super-admin-dashboard');
                if (window.superAdminDashboard) {
                    window.superAdminDashboard.loadDashboard();
                }
            } else {
                utils.navigateTo('admin-dashboard');
                if (window.adminDashboard) {
                    window.adminDashboard.loadDashboard();
                }
            }
        } else {
            utils.navigateTo('user-dashboard');
            if (window.userDashboard) {
                window.userDashboard.loadDashboard();
            }
        }
    }

    async checkAuth() {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            this.logout();
            return false;
        }

        try {
            const response = await api.verifyToken();
            this.currentUser = response.user;
            this.currentUserType = response.type;
            return true;
        } catch (error) {
            this.logout();
            return false;
        }
    }

    showUserMenu() {
        const menu = confirm(`Logged in as: ${this.currentUser.name}\n\nChoose an action:\nOK = Logout\nCancel = Stay`);
        if (menu) {
            this.logout();
        }
    }

    showAdminMenu() {
        const menu = confirm(`Logged in as: ${this.currentUser.name} (${this.currentUser.role})\n\nChoose an action:\nOK = Logout\nCancel = Stay`);
        if (menu) {
            this.logout();
        }
    }

    logout() {
        api.logout();
        this.currentUser = null;
        this.currentUserType = null;
        localStorage.clear();
        utils.navigateTo('login-page');
        utils.showToast('Logged out successfully', 'info');
    }
}

// Initialize auth manager
window.addEventListener('DOMContentLoaded', () => {
    window.auth = new AuthManager();
    
    // Check if user is already logged in
    auth.checkAuth().then(isAuthenticated => {
        if (isAuthenticated) {
            auth.navigateToDashboard();
        }
    });
});
