import logging
from flask import Blueprint, request, jsonify

from app import limiter
from app.services.face_recognition_service import face_recognition_service

logger = logging.getLogger(__name__)
face_bp = Blueprint('face', __name__)


@face_bp.route('/detect', methods=['POST'])
@limiter.limit("10 per minute")
def detect_faces():
    
    try:
        data = request.get_json()
        
        if not data or not data.get('image'):
            return jsonify({"error": "Image required"}), 400
        
        # Convert base64 image
        image = face_recognition_service.base64_to_image(data['image'])
        
        # Detect faces
        faces = face_recognition_service.detect_faces(image)
        
        # Assess image quality
        quality = face_recognition_service.assess_image_quality(image)
        
        return jsonify({
            "face_count": len(faces),
            "faces": [{
                "confidence": face['confidence'],
                "facial_area": face['facial_area']
            } for face in faces],
            "quality": quality
        }), 200
        
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return jsonify({"error": str(e)}), 500


@face_bp.route('/quality-check', methods=['POST'])
@limiter.limit("10 per minute")
def check_quality():
    
    try:
        data = request.get_json()
        
        if not data or not data.get('image'):
            return jsonify({"error": "Image required"}), 400
        
        # Convert base64 image
        image = face_recognition_service.base64_to_image(data['image'])
        
        # Detect faces
        faces = face_recognition_service.detect_faces(image)
        
        if not faces:
            return jsonify({
                "suitable": False,
                "reason": "No face detected",
                "suggestions": [
                    "Ensure your face is clearly visible",
                    "Use good lighting",
                    "Face the camera directly"
                ]
            }), 200
        
        if len(faces) > 1:
            return jsonify({
                "suitable": False,
                "reason": "Multiple faces detected",
                "suggestions": [
                    "Ensure only one person is in the frame"
                ]
            }), 200
        
        # Assess quality
        quality = face_recognition_service.assess_image_quality(image)
        
        suggestions = []
        suitable = True
        
        if quality['sharpness'] < 0.3:
            suitable = False
            suggestions.append("Image is too blurry. Hold camera steady")
        
        if quality['brightness'] < 0.3:
            suitable = False
            suggestions.append("Image is too dark. Improve lighting")
        
        if quality['brightness'] > 0.7:
            suitable = False
            suggestions.append("Image is too bright. Reduce lighting")
        
        if quality['contrast'] < 0.3:
            suitable = False
            suggestions.append("Low contrast. Improve lighting")
        
        if quality['quality_score'] < 0.4:
            suitable = False
        
        return jsonify({
            "suitable": suitable,
            "quality_score": quality['quality_score'],
            "metrics": quality,
            "face_confidence": faces[0]['confidence'],
            "suggestions": suggestions if not suitable else ["Image quality is good"]
        }), 200
        
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        return jsonify({"error": str(e)}), 500


@face_bp.route('/test', methods=['POST'])
def test_face_recognition():
    """Test endpoint for face recognition (no auth required)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('image'):
            return jsonify({"error": "Image required"}), 400
        
        # Convert base64 image
        image = face_recognition_service.base64_to_image(data['image'])
        
        # Extract embedding
        embedding = face_recognition_service.extract_embedding(image, enhance=True)
        
        if embedding is None:
            return jsonify({
                "success": False,
                "message": "No face detected"
            }), 200
        
        return jsonify({
            "success": True,
            "message": "Face detected successfully",
            "embedding_dimension": len(embedding),
            "model": face_recognition_service.model_name
        }), 200
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        return jsonify({"error": str(e)}), 500
