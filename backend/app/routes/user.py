import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db
from app.models import User, Attendance, Person

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('type') != 'user':
            return jsonify({"error": "Access denied"}), 403
        
        user = User.query.get(identity)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user.to_dict(include_stats=True)), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({"error": "Failed to fetch profile"}), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('type') != 'user':
            return jsonify({"error": "Access denied"}), 403
        
        user = User.query.get(identity)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'phone' in data:
            user.phone = data['phone'].strip()
        
        if 'department' in data:
            user.department = data['department'].strip()
        
        if 'designation' in data:
            user.designation = data['designation'].strip()
        
        if 'profile_image' in data:
            user.profile_image = data['profile_image']
        
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update profile"}), 500


@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get user dashboard data"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('type') != 'user':
            return jsonify({"error": "Access denied"}), 403
        
        user = User.query.get(identity)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get enrollment status
        person = Person.query.filter_by(user_id=user.id).first()
        
        # Get recent attendance (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_attendance = Attendance.query.filter(
            Attendance.user_id == user.id,
            Attendance.timestamp >= week_ago
        ).order_by(Attendance.timestamp.desc()).limit(10).all()
        
        return jsonify({
            "user": user.to_dict(include_stats=True),
            "enrollment": person.to_dict() if person else None,
            "recent_attendance": [a.to_dict() for a in recent_attendance]
        }), 200
        
    except Exception as e:
        logger.error(f"Get dashboard error: {e}")
        return jsonify({"error": "Failed to fetch dashboard"}), 500
