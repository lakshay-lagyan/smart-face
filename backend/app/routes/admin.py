import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db
from app.models import EnrollmentRequest, User, Person, Attendance, Admin, SystemLog
from app.services.face_recognition_service import face_recognition_service
from app.services.faiss_service import faiss_service
import pickle

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)


def require_admin(func):
    """Decorator to ensure only admin or super_admin can access"""
    from functools import wraps
    
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('type') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/enrollment-requests', methods=['GET'])
@require_admin
def get_enrollment_requests():
    """Get all enrollment requests"""
    try:
        status = request.args.get('status', 'pending')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = EnrollmentRequest.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        query = query.order_by(EnrollmentRequest.submitted_at.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "requests": [req.to_dict() for req in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get enrollment requests error: {e}")
        return jsonify({"error": "Failed to fetch requests"}), 500


@admin_bp.route('/enrollment-requests/<int:request_id>', methods=['GET'])
@require_admin
def get_enrollment_request(request_id):
    """Get single enrollment request with images"""
    try:
        enrollment_request = EnrollmentRequest.query.get(request_id)
        
        if not enrollment_request:
            return jsonify({"error": "Request not found"}), 404
        
        return jsonify(enrollment_request.to_dict(include_images=True)), 200
        
    except Exception as e:
        logger.error(f"Get enrollment request error: {e}")
        return jsonify({"error": "Failed to fetch request"}), 500


@admin_bp.route('/enrollment-requests/<int:request_id>/approve', methods=['POST'])
@require_admin
def approve_enrollment(request_id):
    """Approve enrollment request and create user"""
    try:
        identity = get_jwt_identity()
        admin = Admin.query.get(identity)
        
        enrollment_request = EnrollmentRequest.query.get(request_id)
        
        if not enrollment_request:
            return jsonify({"error": "Request not found"}), 404
        
        if enrollment_request.status != 'pending':
            return jsonify({"error": f"Request is already {enrollment_request.status}"}), 400
        
        # Process face images and create embedding
        embedding, quality_reports = face_recognition_service.process_enrollment_images(
            enrollment_request.images
        )
        
        if embedding is None:
            return jsonify({
                "error": "Failed to process face images",
                "quality_reports": quality_reports
            }), 400
        
        # Create user
        user = User(
            name=enrollment_request.name,
            email=enrollment_request.email,
            employee_id=enrollment_request.employee_id,
            department=enrollment_request.department,
            designation=enrollment_request.designation,
            phone=enrollment_request.phone,
            password_hash=enrollment_request.password_hash,
            status='active',
            is_enrolled=True,
            enrollment_date=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create person with embedding
        person = Person(
            user_id=user.id,
            name=user.name,
            embedding=pickle.dumps(embedding),
            embedding_dim=len(embedding),
            embedding_model='Facenet512',
            photos_count=len(enrollment_request.images),
            quality_score=sum(r.get('quality_score', 0) for r in quality_reports if r.get('status') == 'accepted') / len([r for r in quality_reports if r.get('status') == 'accepted']),
            status='active'
        )
        
        db.session.add(person)
        
        # Update enrollment request
        enrollment_request.status = 'approved'
        enrollment_request.processed_at = datetime.utcnow()
        enrollment_request.processed_by = admin.email
        
        db.session.commit()
        
        # Add to FAISS index
        faiss_service.add_person(person.id, embedding)
        
        # Log activity
        log = SystemLog(
            action='enrollment_approved',
            user_type='admin',
            user_id=admin.id,
            user_email=admin.email,
            details={
                'enrollment_request_id': request_id,
                'new_user_id': user.id,
                'new_user_email': user.email
            },
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"[Admin] Enrollment approved: {user.email}")
        
        return jsonify({
            "message": "Enrollment approved successfully",
            "user": user.to_dict(),
            "quality_reports": quality_reports
        }), 200
        
    except Exception as e:
        logger.error(f"Approve enrollment error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to approve enrollment"}), 500


@admin_bp.route('/enrollment-requests/<int:request_id>/reject', methods=['POST'])
@require_admin
def reject_enrollment(request_id):
    """Reject enrollment request"""
    try:
        identity = get_jwt_identity()
        admin = Admin.query.get(identity)
        
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        enrollment_request = EnrollmentRequest.query.get(request_id)
        
        if not enrollment_request:
            return jsonify({"error": "Request not found"}), 404
        
        if enrollment_request.status != 'pending':
            return jsonify({"error": f"Request is already {enrollment_request.status}"}), 400
        
        enrollment_request.status = 'rejected'
        enrollment_request.processed_at = datetime.utcnow()
        enrollment_request.processed_by = admin.email
        enrollment_request.rejection_reason = reason
        
        db.session.commit()
        
        logger.info(f"[Admin] Enrollment rejected: {enrollment_request.email}")
        
        return jsonify({
            "message": "Enrollment rejected",
            "request": enrollment_request.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Reject enrollment error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to reject enrollment"}), 500


@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users"""
    try:
        status = request.args.get('status', 'active')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if search:
            query = query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%')) |
                (User.employee_id.ilike(f'%{search}%'))
            )
        
        query = query.order_by(User.created_at.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "users": [user.to_dict() for user in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500


@admin_bp.route('/attendance/all', methods=['GET'])
@require_admin
def get_all_attendance():
    """Get attendance records for all users"""
    try:
        date_str = request.args.get('date')
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        query = Attendance.query
        
        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=target_date)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        query = query.order_by(Attendance.timestamp.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "records": [record.to_dict() for record in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get all attendance error: {e}")
        return jsonify({"error": "Failed to fetch attendance"}), 500


@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_admin_stats():
    """Get system statistics"""
    try:
        # Count statistics
        total_users = User.query.filter_by(status='active').count()
        enrolled_users = User.query.filter_by(status='active', is_enrolled=True).count()
        pending_enrollments = EnrollmentRequest.query.filter_by(status='pending').count()
        
        # Today's attendance
        today = datetime.utcnow().date()
        today_attendance = Attendance.query.filter_by(date=today).count()
        
        # This week's attendance
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_attendance = Attendance.query.filter(Attendance.timestamp >= week_ago).count()
        
        return jsonify({
            "total_users": total_users,
            "enrolled_users": enrolled_users,
            "pending_enrollments": pending_enrollments,
            "today_attendance": today_attendance,
            "week_attendance": week_attendance
        }), 200
        
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500
