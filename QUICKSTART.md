# ⚡ Quick Start Guide

Get your Smart Attendance System running in 5 minutes!

## 🎯 What You're Getting

✅ **Backend**: Flask API with face recognition  
✅ **Frontend**: Mobile-responsive HTML/CSS/JS  
✅ **Features**: User/Admin/Super Admin roles  
✅ **Face Recognition**: DeepFace with FAISS  
✅ **Mobile Support**: Camera integration  
✅ **No CORS Issues**: Properly configured  

## 🚀 5-Minute Setup

### Step 1: Backend Setup (2 minutes)

```bash
# Navigate to backend
cd smart-attendance-v2/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies (this takes ~2 minutes)
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Initialize database
python -c "from app import create_app, db; app = create_app('development'); app.app_context().push(); db.create_all(); print('Database created!')"

# Create super admin
python -c "from app import create_app, db; from app.models import Admin; from werkzeug.security import generate_password_hash; app = create_app('development'); app.app_context().push(); admin = Admin(name='Admin', email='admin@admin.com', password_hash=generate_password_hash('admin123'), role='super_admin', is_active=True); db.session.add(admin); db.session.commit(); print('Super admin created: admin@admin.com / admin123')"

# Run server
python run.py
```

✅ Backend running at `http://localhost:5000`

### Step 2: Frontend Setup (1 minute)

Open a **new terminal**:

```bash
# Navigate to frontend
cd smart-attendance-v2/frontend

# Option A: Python server
python -m http.server 3000

# Option B: Just open index.html in your browser
```

✅ Frontend running at `http://localhost:3000`

### Step 3: Test the System (2 minutes)

1. **Open browser**: Go to `http://localhost:3000`

2. **Login as Super Admin**:
   - Click "Admin Login" tab
   - Email: `admin@admin.com`
   - Password: `admin123`
   - You'll see the Super Admin dashboard

3. **Create a Test User** (Enrollment):
   - Logout (click menu → OK)
   - Click "Enroll Now"
   - Fill in details
   - Capture 3+ photos using your webcam/phone camera
   - Submit

4. **Approve Enrollment**:
   - Login again as admin
   - Go to "Enrollments" tab
   - Click "Approve" on the pending request
   - Wait for face processing (~30 seconds)

5. **Mark Attendance**:
   - Logout
   - Login as the new user
   - Click "Mark Attendance"
   - Capture face photo
   - System recognizes and marks attendance ✅

## 📱 Mobile Testing

### Same Network (Phone + Computer)

1. Find your computer's IP:
   ```bash
   # Windows
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)
   
   # Linux/Mac
   ifconfig | grep inet
   ```

2. On your phone's browser, visit:
   - Frontend: `http://YOUR_IP:3000`
   - Make sure backend is also accessible

3. Test camera and enrollment on mobile!

## 🎨 Default Accounts

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Super Admin | admin@admin.com | admin123 | Full access |

**⚠️ IMPORTANT**: Change the admin password immediately in production!

## 🔧 Common Issues & Fixes

### Issue: `pip install` fails
**Fix**: Update pip first
```bash
python -m pip install --upgrade pip
```

### Issue: Camera not working
**Fix**: 
- Allow camera permissions in browser
- Use HTTPS in production (HTTP works on localhost)
- Try a different browser (Chrome recommended)

### Issue: Face not recognized
**Fix**:
- Ensure good lighting
- Face the camera directly
- Capture from different angles during enrollment
- Check confidence threshold in config

### Issue: CORS errors
**Fix**:
- Backend and frontend must run on same domain OR
- Update `CORS_ORIGINS` in backend `.env`
- Update `API_BASE_URL` in frontend `js/config.js`

### Issue: Database errors
**Fix**: Re-initialize database
```bash
cd backend
rm instance/attendance.db
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## 📚 Key Files to Know

```
smart-attendance-v2/
├── backend/
│   ├── .env                    # ← Configuration (edit this!)
│   ├── run.py                  # ← Start backend
│   ├── requirements.txt        # Dependencies
│   └── app/
│       ├── models.py          # Database models
│       ├── routes/            # API endpoints
│       └── services/          # Face recognition
│
└── frontend/
    ├── index.html             # Main page
    ├── js/
    │   ├── config.js          # ← Frontend config (edit this!)
    │   ├── api.js             # API calls
    │   └── camera.js          # Camera handling
    └── css/
        ├── style.css          # Main styles
        └── mobile.css         # Mobile styles
```

## 🎯 Next Steps

### Customize
1. **Change Colors**: Edit `frontend/css/style.css` → `:root` variables
2. **Change Logo**: Replace SVG in `frontend/index.html`
3. **Adjust Thresholds**: Edit `backend/.env` and `frontend/js/config.js`

### Add Features
1. **Email Notifications**: Configure SMTP in `.env`
2. **Reports**: Add export functionality
3. **Analytics**: Add charts and graphs
4. **Dark Mode**: Add theme toggle

### Deploy
1. See `DEPLOYMENT.md` for complete guide
2. Quick deploy: Render (backend) + Netlify (frontend)
3. Don't forget to update URLs in config!

## 🆘 Need Help?

1. **Check Documentation**:
   - `README.md` - Overview
   - `DEPLOYMENT.md` - Production setup
   - `backend/README.md` - Backend details
   - `frontend/README.md` - Frontend details

2. **Common Questions**:
   - "How do I change admin password?" → Login → Menu → Change Password
   - "How to add more admins?" → Super Admin → Admins tab → Create Admin
   - "Face recognition not accurate?" → Increase MIN_ENROLLMENT_IMAGES
   - "How to backup data?" → Copy `backend/instance/attendance.db`

3. **Debug Mode**:
   ```bash
   # Backend: Check logs
   # Frontend: Open browser console (F12)
   ```

## ✅ Success Checklist

After setup, you should be able to:

- [ ] Login as super admin
- [ ] Create new admin account
- [ ] Enroll new user with face photos
- [ ] Approve enrollment as admin
- [ ] Mark attendance with face recognition
- [ ] View dashboard statistics
- [ ] See recent attendance records
- [ ] Access system on mobile device

## 🎉 You're All Set!

Your Smart Attendance System is ready to use!

**Pro Tips**:
- 💡 Use good lighting for face capture
- 📸 Capture 5-7 images during enrollment
- 🔄 Test on mobile devices early
- 🔒 Change default credentials before deployment
- 💾 Backup database regularly

---

**Questions?** Check the docs or review the code - everything is well-commented!

**Happy tracking! 🚀**
