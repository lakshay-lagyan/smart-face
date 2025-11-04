# 🚀 Deployment Guide

Complete guide for deploying the Smart Attendance System to production.

## 📋 Pre-Deployment Checklist

### Backend
- [ ] All environment variables configured
- [ ] Database setup (PostgreSQL recommended)
- [ ] Redis configured (optional but recommended)
- [ ] Super admin account created
- [ ] CORS origins updated for production domain
- [ ] Debug mode disabled
- [ ] Secret keys changed from defaults
- [ ] HTTPS enabled

### Frontend
- [ ] API_BASE_URL updated to production backend
- [ ] All assets optimized
- [ ] HTTPS enabled
- [ ] Service worker configured (if using PWA)

## 🌐 Backend Deployment

### Option 1: Render.com (Recommended)

#### Step 1: Prepare Repository
```bash
# Ensure your code is on GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/smart-attendance-v2.git
git push -u origin main
```

#### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### Step 3: Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Name: `attendance-db`
3. Select free tier or paid plan
4. Click "Create Database"
5. **Copy the Internal Database URL** (starts with `postgresql://`)

#### Step 4: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `smart-attendance-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app --workers=4`
   - **Instance Type**: Free or Starter

#### Step 5: Environment Variables
Add these in Render dashboard:

```env
FLASK_ENV=production
SECRET_KEY=<generate-strong-random-key-here>
JWT_SECRET_KEY=<generate-strong-random-key-here>
DATABASE_URL=<paste-postgres-internal-url>
CORS_ORIGINS=https://your-frontend-domain.com
FACE_RECOGNITION_THRESHOLD=0.6
FACE_DETECTION_CONFIDENCE=0.9
MIN_ENROLLMENT_IMAGES=3
MAX_ENROLLMENT_IMAGES=10
```

**Generate secret keys**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

#### Step 6: Deploy
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes first time)
3. Your API will be at `https://smart-attendance-api.onrender.com`

#### Step 7: Initialize Database
```bash
# Use Render Shell
1. Go to your service dashboard
2. Click "Shell" tab
3. Run:
flask init-db
flask create-super-admin
# Enter super admin credentials
```

### Option 2: Heroku

#### Step 1: Install Heroku CLI
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2: Login and Create App
```bash
heroku login
cd backend
heroku create smart-attendance-api
```

#### Step 3: Add PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini
```

#### Step 4: Set Environment Variables
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set JWT_SECRET_KEY=<your-jwt-secret>
heroku config:set CORS_ORIGINS=https://your-frontend-domain.com
```

#### Step 5: Deploy
```bash
git push heroku main
```

#### Step 6: Initialize Database
```bash
heroku run flask init-db
heroku run flask create-super-admin
```

### Option 3: AWS EC2

#### Step 1: Launch EC2 Instance
1. Login to AWS Console
2. Launch Ubuntu 22.04 instance
3. Select t2.micro (free tier) or larger
4. Configure security group (ports 22, 80, 443)
5. Download key pair

#### Step 2: Connect to Instance
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### Step 3: Setup Server
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### Step 4: Setup Application
```bash
# Clone repository
git clone https://github.com/yourusername/smart-attendance-v2.git
cd smart-attendance-v2/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### Step 5: Configure PostgreSQL
```bash
sudo -u postgres psql

# In PostgreSQL:
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q
```

#### Step 6: Configure Environment
```bash
# Create .env file
nano .env

# Add configuration:
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://attendance_user:strong-password@localhost:5432/attendance_db
CORS_ORIGINS=https://your-domain.com
```

#### Step 7: Setup Gunicorn Service
```bash
sudo nano /etc/systemd/system/attendance.service
```

Add:
```ini
[Unit]
Description=Smart Attendance API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/smart-attendance-v2/backend
Environment="PATH=/home/ubuntu/smart-attendance-v2/backend/venv/bin"
ExecStart=/home/ubuntu/smart-attendance-v2/backend/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 run:app

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl start attendance
sudo systemctl enable attendance
sudo systemctl status attendance
```

#### Step 8: Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/attendance
```

Add:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 9: Setup SSL
```bash
sudo certbot --nginx -d api.yourdomain.com
```

## 🎨 Frontend Deployment

### Option 1: Netlify (Recommended)

#### Method A: Drag & Drop
1. Go to https://netlify.com
2. Sign up/login
3. Drag `frontend` folder to Netlify dashboard
4. Done! Site is live

#### Method B: GitHub
1. Push frontend code to GitHub
2. On Netlify, click "New site from Git"
3. Connect repository
4. Configure:
   - **Base directory**: `frontend`
   - **Build command**: (leave empty)
   - **Publish directory**: `.`
5. Deploy

#### Configure Custom Domain
1. Go to Site Settings → Domain Management
2. Add custom domain
3. Configure DNS (Netlify provides instructions)

#### Environment Variables
1. Site Settings → Build & Deploy → Environment
2. Add: `API_URL=https://your-backend-api.com`

### Option 2: Vercel

#### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

#### Step 2: Deploy
```bash
cd frontend
vercel
# Follow prompts
```

#### Step 3: Configure
Add `vercel.json`:
```json
{
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

### Option 3: GitHub Pages

#### Step 1: Prepare Repository
```bash
git checkout -b gh-pages
git add frontend/
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages
```

#### Step 2: Enable GitHub Pages
1. Repository → Settings → Pages
2. Source: `gh-pages` branch
3. Folder: `/` (root)
4. Save

#### Step 3: Configure
Update `js/config.js` with absolute API URL.

### Option 4: AWS S3 + CloudFront

#### Step 1: Create S3 Bucket
```bash
aws s3 mb s3://your-bucket-name
```

#### Step 2: Configure for Static Website
```bash
aws s3 website s3://your-bucket-name --index-document index.html
```

#### Step 3: Upload Files
```bash
cd frontend
aws s3 sync . s3://your-bucket-name --acl public-read
```

#### Step 4: Setup CloudFront (Optional)
1. Create CloudFront distribution
2. Point to S3 bucket
3. Configure SSL certificate
4. Set index.html as default root object

## 🔧 Post-Deployment Configuration

### 1. Create Super Admin
```bash
# Backend shell/terminal
flask create-super-admin
```

### 2. Test System
1. Visit frontend URL
2. Enroll test user
3. Login as admin
4. Approve enrollment
5. Mark attendance

### 3. Configure CORS
Ensure backend CORS_ORIGINS includes your frontend domain:
```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 4. Setup Monitoring
- Enable error logging
- Setup uptime monitoring (UptimeRobot, Pingdom)
- Configure email alerts

### 5. Backup Strategy
```bash
# Database backup
pg_dump $DATABASE_URL > backup.sql

# Schedule daily backups
0 2 * * * pg_dump $DATABASE_URL > /backups/attendance_$(date +\%Y\%m\%d).sql
```

## 🔒 Security Hardening

### Backend
1. **Change All Default Credentials**
2. **Enable HTTPS Only**
3. **Set Strong SECRET_KEY**
4. **Configure Rate Limiting**
5. **Regular Security Updates**
6. **Monitor Logs**
7. **Backup Database**

### Frontend
1. **Use HTTPS**
2. **Configure CSP Headers**
3. **Enable HSTS**
4. **XSS Protection**

### Nginx Security Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## 📊 Performance Optimization

### Backend
```python
# Enable gzip compression
# Use connection pooling
# Cache frequent queries
# Optimize database indices
```

### Frontend
```javascript
// Lazy load images
// Minify assets
// Enable browser caching
// Use CDN for static assets
```

## 🐛 Troubleshooting Deployment

### Issue: Camera Not Working
**Solution**: Ensure HTTPS is enabled. HTTP doesn't allow camera access.

### Issue: CORS Errors
**Solution**: 
1. Check CORS_ORIGINS in backend
2. Verify API_BASE_URL in frontend
3. Ensure no trailing slashes

### Issue: Database Connection Failed
**Solution**:
1. Verify DATABASE_URL format
2. Check database is running
3. Verify credentials
4. Check firewall rules

### Issue: 502 Bad Gateway
**Solution**:
1. Check backend service is running
2. Verify port configuration
3. Check Nginx configuration
4. Review application logs

## 📱 Mobile App Deployment (PWA)

### Create manifest.json
```json
{
  "name": "Smart Attendance",
  "short_name": "Attendance",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#4F46E5",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Create Service Worker
```javascript
// sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('attendance-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/css/style.css',
        '/js/app.js'
      ]);
    })
  );
});
```

## ✅ Deployment Verification

Test these after deployment:

- [ ] Frontend loads correctly
- [ ] Can login as super admin
- [ ] Can create new admin
- [ ] User enrollment works
- [ ] Camera access works
- [ ] Face recognition works
- [ ] Attendance marking works
- [ ] All dashboards load
- [ ] Mobile responsive
- [ ] HTTPS enabled
- [ ] No CORS errors
- [ ] No console errors

## 📚 Additional Resources

- [Flask Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Nginx Configuration](https://www.nginx.com/resources/wiki/start/)
- [Let's Encrypt SSL](https://letsencrypt.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [PWA Guide](https://web.dev/progressive-web-apps/)

## 🆘 Getting Help

If you encounter issues:
1. Check logs (backend and frontend)
2. Review this deployment guide
3. Check GitHub issues
4. Contact support

---

**Good luck with your deployment! 🚀**
