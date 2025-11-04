import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from app import db, limiter
from app.models import Admin, User, SystemLog

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


def log_activity(action: str, user_type: str, user_id: int, user_email: str, details: dict = None):
    """Helper to log system activities"""
    try:
        log = SystemLog(
            action=action,
            user_type=user_type,
            user_id=user_id,
            user_email=user_email,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Logging error: {e}")


@auth_bp.route('/admin/login', methods=['POST'])
@limiter.limit("5 per minute")
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password required"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find admin
        admin = Admin.query.filter_by(email=email).first()
        
        if not admin or not check_password_hash(admin.password_hash, password):
            log_activity('admin_login_failed', 'admin', 0, email, {'reason': 'Invalid credentials'})
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not admin.is_active:
            log_activity('admin_login_failed', 'admin', admin.id, email, {'reason': 'Account inactive'})
            return jsonify({"error": "Account is inactive"}), 403
        
        # Update last login
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create JWT tokens
        access_token = create_access_token(
            identity=admin.id,
            additional_claims={
                'type': 'admin',
                'role': admin.role,
                'email': admin.email
            }
        )
        
        refresh_token = create_refresh_token(
            identity=admin.id,
            additional_claims={
                'type': 'admin',
                'role': admin.role
            }
        )
        
        log_activity('admin_login_success', 'admin', admin.id, email)
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "admin": admin.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return jsonify({"error": "Login failed"}), 500


@auth_bp.route('/user/login', methods=['POST'])
@limiter.limit("5 per minute")
def user_login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password required"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            log_activity('user_login_failed', 'user', 0, email, {'reason': 'Invalid credentials'})
            return jsonify({"error": "Invalid credentials"}), 401
        
        if user.status != 'active':
            log_activity('user_login_failed', 'user', user.id, email, {'reason': f'Account {user.status}'})
            return jsonify({"error": f"Account is {user.status}"}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create JWT tokens
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'type': 'user',
                'email': user.email
            }
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims={
                'type': 'user'
            }
        )
        
        log_activity('user_login_success', 'user', user.id, email)
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"User login error: {e}")
        return jsonify({"error": "Login failed"}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Create new access token with same claims
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'type': claims.get('type'),
                'role': claims.get('role'),
                'email': claims.get('email')
            }
        )
        
        return jsonify({"access_token": access_token}), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Token refresh failed"}), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    """Verify token and get current user info"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        if user_type == 'admin':
            admin = Admin.query.get(identity)
            if not admin or not admin.is_active:
                return jsonify({"error": "Invalid token"}), 401
            return jsonify({"user": admin.to_dict(), "type": "admin"}), 200
            
        elif user_type == 'user':
            user = User.query.get(identity)
            if not user or user.status != 'active':
                return jsonify({"error": "Invalid token"}), 401
            return jsonify({"user": user.to_dict(), "type": "user"}), 200
        
        return jsonify({"error": "Invalid token type"}), 401
        
    except Exception as e:
        logger.error(f"Token verify error: {e}")
        return jsonify({"error": "Verification failed"}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({"error": "Current and new password required"}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        if user_type == 'admin':
            admin = Admin.query.get(identity)
            if not admin or not check_password_hash(admin.password_hash, current_password):
                return jsonify({"error": "Current password is incorrect"}), 401
            
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            log_activity('password_changed', 'admin', admin.id, admin.email)
            
        elif user_type == 'user':
            user = User.query.get(identity)
            if not user or not check_password_hash(user.password_hash, current_password):
                return jsonify({"error": "Current password is incorrect"}), 401
            
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            log_activity('password_changed', 'user', user.id, user.email)
        
        else:
            return jsonify({"error": "Invalid user type"}), 400
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({"error": "Password change failed"}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        email = claims.get('email', 'unknown')
        
        log_activity('logout', user_type, identity, email)
        
        return jsonify({"message": "Logged out successfully"}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500
