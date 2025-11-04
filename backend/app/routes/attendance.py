import logging
from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func, and_

from app import db, limiter
from app.models import Attendance, User, Person
from app.services.face_recognition_service import face_recognition_service
from app.services.faiss_service import faiss_service
import pickle

logger = logging.getLogger(__name__)
attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/mark', methods=['POST'])
@limiter.limit("10 per minute")
def mark_attendance():
    
    try:
        data = request.get_json()
        
        if not data or not data.get('image'):
            return jsonify({"error": "Face image required"}), 400
        
        # Convert base64 image
        image = face_recognition_service.base64_to_image(data['image'])
        
        # Extract embedding from image
        embedding = face_recognition_service.extract_embedding(image, enhance=True)
        
        if embedding is None:
            return jsonify({"error": "No face detected in image"}), 400
        
        # Search for matching person using FAISS
        matches = faiss_service.search(embedding, k=1, threshold=0.6)
        
        if not matches:
            return jsonify({"error": "Face not recognized"}), 404
        
        # Get best match
        person_id, confidence = matches[0]
        
        # Get person details
        person = Person.query.get(person_id)
        if not person or person.status != 'active':
            return jsonify({"error": "Person not active"}), 403
        
        # Get user
        user = User.query.get(person.user_id)
        if not user or user.status != 'active':
            return jsonify({"error": "User not active"}), 403
        
        # Check if already marked today
        today = datetime.utcnow().date()
        check_type = data.get('check_type', 'in')
        
        existing = Attendance.query.filter(
            and_(
                Attendance.user_id == user.id,
                Attendance.date == today,
                Attendance.check_type == check_type
            )
        ).first()
        
        if existing:
            return jsonify({
                "message": f"Attendance already marked for {check_type}",
                "attendance": existing.to_dict()
            }), 200
        
        # Create attendance record
        attendance = Attendance(
            user_id=user.id,
            name=user.name,
            timestamp=datetime.utcnow(),
            date=today,
            confidence=confidence,
            check_type=check_type,
            device_info=data.get('device_info'),
            location=data.get('location'),
            verified_by='face_recognition'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        logger.info(f"[Attendance] Marked for {user.name} (confidence: {confidence:.3f})")
        
        return jsonify({
            "message": "Attendance marked successfully",
            "attendance": attendance.to_dict(),
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Mark attendance error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to mark attendance"}), 500


@attendance_bp.route('/my-records', methods=['GET'])
@jwt_required()
def get_my_attendance():
    """Get current user's attendance records"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('type') != 'user':
            return jsonify({"error": "Only users can access this endpoint"}), 403
        
        user = User.query.get(identity)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query attendance records
        query = Attendance.query.filter(
            and_(
                Attendance.user_id == user.id,
                Attendance.timestamp >= start_date
            )
        ).order_by(Attendance.timestamp.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "records": [record.to_dict() for record in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        logger.error(f"Get my attendance error: {e}")
        return jsonify({"error": "Failed to fetch attendance"}), 500


@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_my_stats():
    """Get current user's attendance statistics"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('type') != 'user':
            return jsonify({"error": "Only users can access this endpoint"}), 403
        
        user = User.query.get(identity)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Calculate statistics
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Total attendance
        total = Attendance.query.filter_by(user_id=user.id).count()
        
        # This week
        this_week = Attendance.query.filter(
            and_(
                Attendance.user_id == user.id,
                Attendance.date >= week_ago
            )
        ).count()
        
        # This month
        this_month = Attendance.query.filter(
            and_(
                Attendance.user_id == user.id,
                Attendance.date >= month_ago
            )
        ).count()
        
        # Today
        today_records = Attendance.query.filter(
            and_(
                Attendance.user_id == user.id,
                Attendance.date == today
            )
        ).all()
        
        return jsonify({
            "total": total,
            "this_week": this_week,
            "this_month": this_month,
            "today": {
                "count": len(today_records),
                "records": [r.to_dict() for r in today_records]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500
