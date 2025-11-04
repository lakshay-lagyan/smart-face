import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash

from app import db
from app.models import Admin, User, SystemLog, Settings
from app.services.faiss_service import faiss_service

logger = logging.getLogger(__name__)
super_admin_bp = Blueprint('super_admin', __name__)


def require_super_admin(func):
    """Decorator to ensure only super_admin can access"""
    from functools import wraps
    
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('type') != 'admin' or claims.get('role') != 'super_admin':
            return jsonify({"error": "Super admin access required"}), 403
        return func(*args, **kwargs)
    return wrapper


@super_admin_bp.route('/admins', methods=['GET'])
@require_super_admin
def get_all_admins():
    """Get all admins"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Admin.query.order_by(Admin.created_at.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "admins": [admin.to_dict() for admin in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get admins error: {e}")
        return jsonify({"error": "Failed to fetch admins"}), 500


@super_admin_bp.route('/admins', methods=['POST'])
@require_super_admin
def create_admin():
    """Create new admin"""
    try:
        identity = get_jwt_identity()
        creator = Admin.query.get(identity)
        
        data = request.get_json()
        
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        email = data['email'].lower().strip()
        
        # Check if email already exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400
        
        # Create admin
        admin = Admin(
            name=data['name'].strip(),
            email=email,
            password_hash=generate_password_hash(data['password']),
            role=data.get('role', 'admin'),  # 'admin' or 'super_admin'
            phone=data.get('phone', '').strip(),
            department=data.get('department', '').strip(),
            is_active=True,
            created_by=identity
        )
        
        db.session.add(admin)
        db.session.commit()
        
        # Log activity
        log = SystemLog(
            action='admin_created',
            user_type='admin',
            user_id=creator.id,
            user_email=creator.email,
            details={
                'new_admin_id': admin.id,
                'new_admin_email': admin.email,
                'new_admin_role': admin.role
            },
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"[SuperAdmin] Admin created: {admin.email}")
        
        return jsonify({
            "message": "Admin created successfully",
            "admin": admin.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create admin"}), 500


@super_admin_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@require_super_admin
def update_admin(admin_id):
    """Update admin"""
    try:
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return jsonify({"error": "Admin not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            admin.name = data['name'].strip()
        
        if 'phone' in data:
            admin.phone = data['phone'].strip()
        
        if 'department' in data:
            admin.department = data['department'].strip()
        
        if 'role' in data and data['role'] in ['admin', 'super_admin']:
            admin.role = data['role']
        
        if 'is_active' in data:
            admin.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        logger.info(f"[SuperAdmin] Admin updated: {admin.email}")
        
        return jsonify({
            "message": "Admin updated successfully",
            "admin": admin.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update admin error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update admin"}), 500


@super_admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@require_super_admin
def delete_admin(admin_id):
    """Delete (deactivate) admin"""
    try:
        identity = get_jwt_identity()
        
        if admin_id == identity:
            return jsonify({"error": "Cannot delete yourself"}), 400
        
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return jsonify({"error": "Admin not found"}), 404
        
        # Deactivate instead of delete
        admin.is_active = False
        db.session.commit()
        
        logger.info(f"[SuperAdmin] Admin deactivated: {admin.email}")
        
        return jsonify({"message": "Admin deactivated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete admin error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete admin"}), 500


@super_admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@require_super_admin
def update_user_status(user_id):
    """Update user status (activate/suspend)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['active', 'inactive', 'suspended']:
            return jsonify({"error": "Invalid status"}), 400
        
        user.status = status
        db.session.commit()
        
        logger.info(f"[SuperAdmin] User status updated: {user.email} -> {status}")
        
        return jsonify({
            "message": "User status updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update user status error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user status"}), 500


@super_admin_bp.route('/system/logs', methods=['GET'])
@require_super_admin
def get_system_logs():
    """Get system activity logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        action = request.args.get('action')
        user_type = request.args.get('user_type')
        
        query = SystemLog.query
        
        if action:
            query = query.filter_by(action=action)
        
        if user_type:
            query = query.filter_by(user_type=user_type)
        
        query = query.order_by(SystemLog.timestamp.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "logs": [log.to_dict() for log in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get system logs error: {e}")
        return jsonify({"error": "Failed to fetch logs"}), 500


@super_admin_bp.route('/system/settings', methods=['GET'])
@require_super_admin
def get_settings():
    """Get all system settings"""
    try:
        settings = Settings.query.all()
        
        return jsonify({
            "settings": [setting.to_dict() for setting in settings]
        }), 200
        
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return jsonify({"error": "Failed to fetch settings"}), 500


@super_admin_bp.route('/system/settings', methods=['PUT'])
@require_super_admin
def update_settings():
    """Update system settings"""
    try:
        identity = get_jwt_identity()
        admin = Admin.query.get(identity)
        
        data = request.get_json()
        
        for key, value in data.items():
            setting = Settings.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
                setting.updated_by = admin.email
                setting.updated_at = datetime.utcnow()
            else:
                setting = Settings(
                    key=key,
                    value=value,
                    updated_by=admin.email
                )
                db.session.add(setting)
        
        db.session.commit()
        
        logger.info(f"[SuperAdmin] Settings updated by {admin.email}")
        
        return jsonify({"message": "Settings updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update settings"}), 500


@super_admin_bp.route('/system/rebuild-index', methods=['POST'])
@require_super_admin
def rebuild_faiss_index():
    """Rebuild FAISS index from database"""
    try:
        faiss_service.rebuild_from_database()
        
        logger.info("[SuperAdmin] FAISS index rebuilt")
        
        return jsonify({
            "message": "FAISS index rebuilt successfully",
            "total_persons": faiss_service.get_total_persons()
        }), 200
        
    except Exception as e:
        logger.error(f"Rebuild FAISS error: {e}")
        return jsonify({"error": "Failed to rebuild index"}), 500


@super_admin_bp.route('/dashboard', methods=['GET'])
@require_super_admin
def get_super_admin_dashboard():
    """Get super admin dashboard data"""
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        # System statistics
        total_admins = Admin.query.filter_by(is_active=True).count()
        total_users = User.query.count()
        active_users = User.query.filter_by(status='active').count()
        enrolled_users = User.query.filter_by(is_enrolled=True).count()
        pending_enrollments = EnrollmentRequest.query.filter_by(status='pending').count()
        
        # Attendance statistics
        today = datetime.utcnow().date()
        today_attendance = Attendance.query.filter_by(date=today).count()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_attendance = Attendance.query.filter(Attendance.timestamp >= week_ago).count()
        
        # Recent logs
        recent_logs = SystemLog.query.order_by(
            SystemLog.timestamp.desc()
        ).limit(10).all()
        
        return jsonify({
            "statistics": {
                "total_admins": total_admins,
                "total_users": total_users,
                "active_users": active_users,
                "enrolled_users": enrolled_users,
                "pending_enrollments": pending_enrollments,
                "today_attendance": today_attendance,
                "week_attendance": week_attendance,
                "faiss_index_size": faiss_service.get_total_persons()
            },
            "recent_logs": [log.to_dict() for log in recent_logs]
        }), 200
        
    except Exception as e:
        logger.error(f"Get super admin dashboard error: {e}")
        return jsonify({"error": "Failed to fetch dashboard"}), 500
