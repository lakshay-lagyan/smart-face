import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db, limiter
from app.models import EnrollmentRequest, User, Person
from app.services.face_recognition_service import face_recognition_service
import pickle

logger = logging.getLogger(__name__)
enrollment_bp = Blueprint('enrollment', __name__)


@enrollment_bp.route('/request', methods=['POST'])
@limiter.limit("3 per hour")
def submit_enrollment_request():
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'images']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        email = data['email'].lower().strip()
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        existing_request = EnrollmentRequest.query.filter_by(
            email=email, 
            status='pending'
        ).first()
        
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        if existing_request:
            return jsonify({"error": "Enrollment request already pending"}), 400
        
        images = data['images']
        
        # Validate number of images
        min_images = 3
        max_images = 10
        
        if len(images) < min_images:
            return jsonify({"error": f"At least {min_images} images required"}), 400
        
        if len(images) > max_images:
            return jsonify({"error": f"Maximum {max_images} images allowed"}), 400
        
        # Validate images (check if faces are detected)
        valid_images = 0
        for img in images:
            try:
                image_array = face_recognition_service.base64_to_image(img)
                faces = face_recognition_service.detect_faces(image_array)
                if faces:
                    valid_images += 1
            except:
                continue
        
        if valid_images < min_images:
            return jsonify({
                "error": f"Only {valid_images} valid face images found. Need at least {min_images}"
            }), 400
        
        # Create enrollment request
        enrollment_request = EnrollmentRequest(
            name=data['name'].strip(),
            email=email,
            employee_id=data.get('employee_id', '').strip(),
            department=data.get('department', '').strip(),
            designation=data.get('designation', '').strip(),
            phone=data.get('phone', '').strip(),
            password_hash=generate_password_hash(data['password']),
            images=images,
            device_info=data.get('device_info'),
            status='pending'
        )
        
        db.session.add(enrollment_request)
        db.session.commit()
        
        logger.info(f"[Enrollment] New request submitted: {email}")
        
        return jsonify({
            "message": "Enrollment request submitted successfully",
            "request_id": enrollment_request.id,
            "status": "pending"
        }), 201
        
    except Exception as e:
        logger.error(f"Enrollment request error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to submit enrollment request"}), 500


@enrollment_bp.route('/status/<int:request_id>', methods=['GET'])
def get_enrollment_status(request_id):
    """Check enrollment request status"""
    try:
        enrollment_request = EnrollmentRequest.query.get(request_id)
        
        if not enrollment_request:
            return jsonify({"error": "Request not found"}), 404
        
        return jsonify(enrollment_request.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": "Failed to check status"}), 500


@enrollment_bp.route('/check-email', methods=['POST'])
def check_email():
    """Check if email is available for enrollment"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        existing_user = User.query.filter_by(email=email).first()
        pending_request = EnrollmentRequest.query.filter_by(
            email=email,
            status='pending'
        ).first()
        
        if existing_user:
            return jsonify({
                "available": False,
                "reason": "Email already registered"
            }), 200
        
        if pending_request:
            return jsonify({
                "available": False,
                "reason": "Enrollment request pending"
            }), 200
        
        return jsonify({"available": True}), 200
        
    except Exception as e:
        logger.error(f"Email check error: {e}")
        return jsonify({"error": "Failed to check email"}), 500
