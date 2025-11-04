from datetime import datetime
from app import db


class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')  # 'admin' or 'super_admin'
    profile_image = db.Column(db.Text, default='')
    phone = db.Column(db.String(20), default='')
    department = db.Column(db.String(100), default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'profile_image': self.profile_image,
            'phone': self.phone,
            'department': self.department,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        return data
    
    def is_super_admin(self):
        """Check if user is super admin"""
        return self.role == 'super_admin'


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    department = db.Column(db.String(100), default='')
    designation = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    profile_image = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    is_enrolled = db.Column(db.Boolean, default=False)
    enrollment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='user_ref', lazy='dynamic',
                                        foreign_keys='Attendance.user_id')
    
    def to_dict(self, include_stats=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'employee_id': self.employee_id,
            'department': self.department,
            'designation': self.designation,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'status': self.status,
            'is_enrolled': self.is_enrolled,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'role': 'user'
        }
        
        if include_stats:
            # Add attendance statistics
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            data['stats'] = {
                'total_attendance': self.attendance_records.count(),
                'this_week': self.attendance_records.filter(
                    Attendance.timestamp >= week_ago
                ).count(),
                'this_month': self.attendance_records.filter(
                    Attendance.timestamp >= month_ago
                ).count()
            }
        
        return data


class Person(db.Model):
    """Person with face embeddings for recognition"""
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    embedding = db.Column(db.LargeBinary, nullable=False)
    embedding_dim = db.Column(db.Integer, nullable=False)
    embedding_model = db.Column(db.String(50), default='Facenet512')
    photos_count = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('person', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'photos_count': self.photos_count,
            'quality_score': round(self.quality_score, 3),
            'status': self.status,
            'embedding_model': self.embedding_model,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class EnrollmentRequest(db.Model):
    __tablename__ = 'enrollment_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    employee_id = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), default='')
    designation = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    password_hash = db.Column(db.String(255), nullable=False)
    images = db.Column(db.JSON, nullable=False)  # Array of base64 images
    device_info = db.Column(db.JSON, nullable=True)  # Mobile/browser info
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.String(120), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    def to_dict(self, include_images=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'employee_id': self.employee_id,
            'department': self.department,
            'designation': self.designation,
            'phone': self.phone,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_by': self.processed_by,
            'rejection_reason': self.rejection_reason,
            'image_count': len(self.images) if self.images else 0
        }
        if include_images:
            data['images'] = self.images
        if self.device_info:
            data['device_info'] = self.device_info
        return data


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    date = db.Column(db.Date, default=datetime.utcnow, index=True)
    confidence = db.Column(db.Float, default=0.0)
    device_info = db.Column(db.JSON, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    check_type = db.Column(db.String(20), default='in')  # in, out
    image_capture = db.Column(db.Text, nullable=True)  # Optional capture
    verified_by = db.Column(db.String(100), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'date': self.date.isoformat() if self.date else None,
            'confidence': round(self.confidence, 3),
            'check_type': self.check_type,
            'device_info': self.device_info,
            'location': self.location,
            'verified_by': self.verified_by
        }


class SystemLog(db.Model):
    """System activity logs"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    user_type = db.Column(db.String(20), nullable=False)  # admin, user, system
    user_id = db.Column(db.Integer, nullable=True)
    user_email = db.Column(db.String(120), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'user_type': self.user_type,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Settings(db.Model):
    """System settings and configurations"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.String(120), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Create composite indexes for better query performance
db.Index('idx_attendance_user_date', Attendance.user_id, Attendance.date.desc())
db.Index('idx_attendance_date_name', Attendance.date.desc(), Attendance.name)
db.Index('idx_persons_user_status', Person.user_id, Person.status)
db.Index('idx_users_status_enrolled', User.status, User.is_enrolled)
db.Index('idx_enrollment_status_date', EnrollmentRequest.status, EnrollmentRequest.submitted_at.desc())
db.Index('idx_logs_timestamp_action', SystemLog.timestamp.desc(), SystemLog.action)
